# backend/memory/agentic_memory/nl_interface.py
"""
MemoryNLInterface: Natural language command processing for memory
"""

from typing import Dict, Any, List, Optional
import re
import json
from loguru import logger

from backend.utils.llm_utils import call_ollama_with_retry
from .note import AgenticNote, NoteType
from .opensearch_memory import AgenticMemoryStore



class MemoryNLInterface:
    def __init__(
        self,
        store: AgenticMemoryStore,
        embedding_model,
        llm_model: str = "qwen3-vl:8b"
    ):
        self.store = store
        self.embedding_model = embedding_model
        self.llm_model = llm_model
        
        self.intent_patterns = {
            "forget": [r"forget about (.+)", r"delete memory (.+)", r"remove (.+)"],
            "connect": [r"connect (.+) to (.+)", r"link (.+) with (.+)"],
            "remember": [r"remember that (.+)", r"save that (.+)", r"note that (.+)"],
            "search": [r"what do you know about (.+)", r"find memories about (.+)"],
            "when": [r"when did i mention (.+)", r"when did i talk about (.+)"],
        }

    async def process_command(
        self,
        user_input: str,
        user_id: str
    ) -> Dict[str, Any]:
        intent, matches = self._classify_intent(user_input)
        
        if intent == "forget":
            return await self._handle_forget(matches[0], user_id)
        elif intent == "connect":
            return await self._handle_connect(matches[0], matches[1], user_id)
        elif intent == "remember":
            return await self._handle_remember(matches[0], user_id)
        elif intent == "search":
            return await self._handle_search(matches[0], user_id)
        elif intent == "when":
            return await self._handle_when(matches[0], user_id)
        else:
            return await self._handle_unknown(user_input, user_id)

    def _classify_intent(self, text: str) -> tuple:
        text_lower = text.lower()
        
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower)
                if match:
                    return intent, match.groups()
        
        return "unknown", []

    async def _handle_forget(self, topic: str, user_id: str) -> Dict[str, Any]:
        embedding = self.embedding_model.encode(topic).tolist()
        results = await self.store.search_by_vector(embedding, user_id, k=5)
        
        if not results:
            return {"success": False, "message": f"No memories found about '{topic}'"}
        
        deleted_count = 0
        for result in results:
            if result["score"] > 0.7:
                await self.store.delete_note(result["id"])
                deleted_count += 1
        
        return {
            "success": True,
            "message": f"Deleted {deleted_count} memories related to '{topic}'"
        }

    async def _handle_connect(
        self,
        topic1: str,
        topic2: str,
        user_id: str
    ) -> Dict[str, Any]:
        emb1 = self.embedding_model.encode(topic1).tolist()
        emb2 = self.embedding_model.encode(topic2).tolist()
        
        results1 = await self.store.search_by_vector(emb1, user_id, k=1)
        results2 = await self.store.search_by_vector(emb2, user_id, k=1)
        
        if not results1 or not results2:
            return {"success": False, "message": "Could not find memories for both topics"}
        
        note1 = await self.store.get_note(results1[0]["id"])
        note2 = await self.store.get_note(results2[0]["id"])
        
        if note1 and note2:
            note1.add_link(note2.id)
            note2.add_link(note1.id)
            await self.store.update_note(note1)
            await self.store.update_note(note2)
            
            return {
                "success": True,
                "message": f"Connected memories about '{topic1}' and '{topic2}'"
            }
        
        return {"success": False, "message": "Failed to create connection"}

    async def _handle_remember(self, content: str, user_id: str) -> Dict[str, Any]:
        from .note_generator import NoteGenerator
        
        generator = NoteGenerator(self.llm_model)
        attrs = await generator.generate_note_attributes(content)
        
        note = AgenticNote(
            content=content,
            user_id=user_id,
            context=attrs.get("context", ""),
            keywords=attrs.get("keywords", []),
            tags=attrs.get("tags", []),
            importance=attrs.get("importance", 0.5)
        )
        note.embedding = self.embedding_model.encode(content).tolist()
        
        await self.store.store_note(note)
        
        return {
            "success": True,
            "message": f"Remembered: '{content[:50]}...'",
            "note_id": note.id
        }

    async def _handle_search(self, topic: str, user_id: str) -> Dict[str, Any]:
        embedding = self.embedding_model.encode(topic).tolist()
        results = await self.store.search_by_vector(embedding, user_id, k=5)
        
        if not results:
            return {"success": True, "message": f"I don't have any memories about '{topic}'", "memories": []}
        
        memories = []
        for r in results:
            memories.append({
                "content": r.get("content", "")[:200],
                "context": r.get("context", ""),
                "score": r.get("score", 0)
            })
        
        return {
            "success": True,
            "message": f"Found {len(memories)} memories about '{topic}'",
            "memories": memories
        }

    async def _handle_when(self, topic: str, user_id: str) -> Dict[str, Any]:
        result = await self._handle_search(topic, user_id)
        if result.get("memories"):
            note_data = result["memories"][0]
            return {
                "success": True,
                "message": f"You mentioned '{topic}' with context: {note_data.get('context', 'N/A')}"
            }
        return {"success": True, "message": f"I don't recall you mentioning '{topic}'"}

    async def _handle_unknown(self, text: str, user_id: str) -> Dict[str, Any]:
        prompt = f"""Classify this memory-related command:
"{text}"

Options:
- forget: user wants to delete memories
- connect: user wants to link memories
- remember: user wants to save something
- search: user wants to find memories
- other: not a memory command

Respond with just the option name:"""

        try:
            response = await call_ollama_with_retry(
                base_url="http://localhost:11434",
                model=self.llm_model,
                prompt=prompt,
                think=False
            )
            intent = response.strip().lower()
            
            if intent in ["forget", "connect", "remember", "search"]:
                return {"success": False, "message": f"I understood '{intent}' but couldn't extract the topic. Please rephrase."}
        except:
            pass
        
        return {"success": False, "message": "I didn't understand that memory command. Try: 'remember that...', 'what do you know about...', or 'forget about...'"}

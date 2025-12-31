# backend/memory/agentic_memory/multimodal.py
"""
Multi-Modal Memory Support - Images, code, and cross-modal search
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger

from .note import AgenticNote, Modality, NoteType
from .opensearch_memory import AgenticMemoryStore


class MultiModalMemory:
    def __init__(
        self,
        store: AgenticMemoryStore,
        text_embedding_model,
        clip_model=None
    ):
        self.store = store
        self.text_embedding = text_embedding_model
        self.clip_model = clip_model

    async def store_image_memory(
        self,
        image_path: str,
        description: str,
        user_id: str,
        **kwargs
    ) -> Optional[AgenticNote]:
        try:
            note = AgenticNote(
                content=description,
                user_id=user_id,
                modality=Modality.IMAGE,
                note_type=NoteType.IMAGE,
                thumbnail_path=image_path,
                **kwargs
            )
            
            note.embedding = self.text_embedding.encode(description).tolist()
            
            if self.clip_model:
                try:
                    note.media_embedding = await self._get_clip_embedding(image_path)
                except Exception as e:
                    logger.warning(f"CLIP embedding failed: {e}")
            
            await self.store.store_note(note)
            return note
        except Exception as e:
            logger.error(f"Failed to store image memory: {e}")
            return None

    async def _get_clip_embedding(self, image_path: str) -> Optional[List[float]]:
        if not self.clip_model:
            return None
        try:
            from PIL import Image
            image = Image.open(image_path)
            embedding = self.clip_model.encode(image)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"CLIP embedding error: {e}")
            return None

    async def store_code_memory(
        self,
        code: str,
        language: str,
        description: str,
        user_id: str,
        **kwargs
    ) -> Optional[AgenticNote]:
        try:
            full_content = f"[{language}]\n{code}\n\nDescription: {description}"
            
            note = AgenticNote(
                content=full_content,
                user_id=user_id,
                modality=Modality.CODE,
                note_type=NoteType.CODE,
                metadata={"language": language, "code_length": len(code)},
                **kwargs
            )
            
            note.embedding = self.text_embedding.encode(full_content).tolist()
            
            await self.store.store_note(note)
            return note
        except Exception as e:
            logger.error(f"Failed to store code memory: {e}")
            return None


class CrossModalSearch:
    def __init__(
        self,
        store: AgenticMemoryStore,
        text_embedding_model,
        clip_model=None
    ):
        self.store = store
        self.text_embedding = text_embedding_model
        self.clip_model = clip_model

    async def search(
        self,
        query: str,
        user_id: str,
        modalities: Optional[List[str]] = None,
        k: int = 10
    ) -> List[Dict[str, Any]]:
        query_embedding = self.text_embedding.encode(query).tolist()
        
        filters = {}
        if modalities:
            filters["modality"] = modalities
        
        results = await self.store.search_by_vector(
            embedding=query_embedding,
            user_id=user_id,
            k=k,
            filters=filters if filters else None
        )
        
        return results

    async def search_similar_images(
        self,
        image_path: str,
        user_id: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        if not self.clip_model:
            return []
        
        try:
            from PIL import Image
            image = Image.open(image_path)
            query_embedding = self.clip_model.encode(image).tolist()
            
            return await self.store.search_by_vector(
                embedding=query_embedding,
                user_id=user_id,
                k=k,
                filters={"modality": ["image"]}
            )
        except Exception as e:
            logger.error(f"Image search failed: {e}")
            return []

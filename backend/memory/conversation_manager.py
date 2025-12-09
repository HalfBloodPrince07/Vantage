# backend/memory/conversation_manager.py
"""
Conversation Manager - Multi-user chat history

Manages conversation threads with persistent storage:
- Create/list/get/update/delete conversations
- Add/retrieve messages
- Document attachments per conversation
"""

import uuid
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import aiosqlite
from loguru import logger


class ConversationManager:
    """Manages conversation history for multi-user chat"""
    
    def __init__(self, database_path: str = "locallens_conversations.db"):
        self.database_path = database_path
        self._initialized = False
    
    async def initialize(self):
        """Initialize database and create tables"""
        if self._initialized:
            return
        
        async with aiosqlite.connect(self.database_path) as db:
            # Conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    message_count INTEGER DEFAULT 0,
                    is_pinned BOOLEAN DEFAULT FALSE,
                    metadata TEXT
                )
            """)
            
            # Messages table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    conversation_id TEXT NOT NULL,
                    role TEXT CHECK(role IN ('user', 'assistant')),
                    content TEXT,
                    query TEXT,
                    results TEXT,
                    thinking_steps TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            
            # Document attachments table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversation_documents (
                    conversation_id TEXT,
                    document_id TEXT,
                    attached_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY (conversation_id, document_id),
                    FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_conversations_user 
                ON conversations(user_id, updated_at DESC)
            """)
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_messages_conversation 
                ON messages(conversation_id, timestamp)
            """)
            
            await db.commit()
        
        self._initialized = True
        logger.info("✅ Conversation Manager initialized")
    
    async def create_conversation(
        self, 
        user_id: str, 
        title: str = None,
        initial_query: str = None
    ) -> str:
        """Create a new conversation"""
        conversation_id = str(uuid.uuid4())[:16]
        
        # Auto-generate title from query if not provided
        if not title and initial_query:
            title = self._generate_title(initial_query)
        elif not title:
            title = "New Conversation"
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO conversations (id, user_id, title)
                VALUES (?, ?, ?)
            """, (conversation_id, user_id, title))
            await db.commit()
        
        logger.info(f"Created conversation {conversation_id} for user {user_id}")
        return conversation_id
    
    async def list_conversations(
        self, 
        user_id: str, 
        limit: int = 50,
        offset: int = 0
    ) -> List[Dict]:
        """List conversations for a user, grouped by date"""
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT id, title, created_at, updated_at, message_count, is_pinned
                FROM conversations
                WHERE user_id = ?
                ORDER BY is_pinned DESC, updated_at DESC
                LIMIT ? OFFSET ?
            """, (user_id, limit, offset))
            
            rows = await cursor.fetchall()
            conversations = [dict(row) for row in rows]
        
        # Group by date
        grouped = self._group_by_date(conversations)
        return grouped
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict]:
        """Get conversation details"""
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM conversations WHERE id = ?
            """, (conversation_id,))
            
            row = await cursor.fetchone()
            return dict(row) if row else None
    
    async def update_conversation(
        self, 
        conversation_id: str, 
        title: str = None,
        is_pinned: bool = None
    ):
        """Update conversation metadata"""
        updates = []
        params = []
        
        if title is not None:
            updates.append("title = ?")
            params.append(title)
        
        if is_pinned is not None:
            updates.append("is_pinned = ?")
            params.append(is_pinned)
        
        if not updates:
            return
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(conversation_id)
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute(f"""
                UPDATE conversations 
                SET {', '.join(updates)}
                WHERE id = ?
            """, params)
            await db.commit()
    
    async def delete_conversation(self, conversation_id: str):
        """Delete a conversation and all its messages"""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("DELETE FROM conversations WHERE id = ?", (conversation_id,))
            await db.commit()
        
        logger.info(f"Deleted conversation {conversation_id}")
    
    async def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        query: str = None,
        results: List[Dict] = None,
        thinking_steps: List[Dict] = None
    ) -> str:
        """Add a message to a conversation"""
        import json
        
        message_id = str(uuid.uuid4())[:16]
        
        # Serialize JSON fields
        results_json = json.dumps(results) if results else None
        steps_json = json.dumps(thinking_steps) if thinking_steps else None
        
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                INSERT INTO messages (id, conversation_id, role, content, query, results, thinking_steps)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (message_id, conversation_id, role, content, query, results_json, steps_json))
            
            # Update conversation
            await db.execute("""
                UPDATE conversations 
                SET message_count = message_count + 1,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (conversation_id,))
            
            await db.commit()
        
        return message_id
    
    async def get_messages(
        self, 
        conversation_id: str, 
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """Get messages for a conversation"""
        import json
        
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT * FROM messages
                WHERE conversation_id = ?
                ORDER BY timestamp ASC
                LIMIT ? OFFSET ?
            """, (conversation_id, limit, offset))
            
            rows = await cursor.fetchall()
            messages = []
            for row in rows:
                msg = dict(row)
                # Deserialize JSON fields
                if msg.get('results'):
                    msg['results'] = json.loads(msg['results'])
                if msg.get('thinking_steps'):
                    msg['thinking_steps'] = json.loads(msg['thinking_steps'])
                messages.append(msg)
            
            return messages
    
    async def attach_documents(
        self,
        conversation_id: str,
        document_ids: List[str]
    ):
        """Attach documents to a conversation"""
        async with aiosqlite.connect(self.database_path) as db:
            for doc_id in document_ids:
                await db.execute("""
                    INSERT OR REPLACE INTO conversation_documents (conversation_id, document_id)
                    VALUES (?, ?)
                """, (conversation_id, doc_id))
            await db.commit()
    
    async def get_attached_documents(self, conversation_id: str) -> List[str]:
        """Get documents attached to a conversation"""
        async with aiosqlite.connect(self.database_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("""
                SELECT document_id FROM conversation_documents
                WHERE conversation_id = ?
                ORDER BY attached_at DESC
            """, (conversation_id,))
            
            rows = await cursor.fetchall()
            return [row['document_id'] for row in rows]
    
    async def detach_document(self, conversation_id: str, document_id: str):
        """Remove a document from a conversation"""
        async with aiosqlite.connect(self.database_path) as db:
            await db.execute("""
                DELETE FROM conversation_documents
                WHERE conversation_id = ? AND document_id = ?
            """, (conversation_id, document_id))
            await db.commit()
    
    def _generate_title(self, query: str, max_length: int = 50) -> str:
        """Generate a title from the first query"""
        # Handle empty or whitespace-only queries
        if not query or not query.strip():
            return "New Conversation"
        
        # Clean the query
        original_query = query.strip()
        
        # Remove common prefixes
        prefixes = [
            "show me", "find me", "search for", "get me", "list all",
            "find", "search", "get", "list", "show",
            "what is", "what are", "how to", "tell me about",
            "can you", "could you", "please", "i want", "i need"
        ]
        title = original_query.lower()
        
        for prefix in prefixes:
            if title.startswith(prefix + " "):
                title = title[len(prefix):].strip()
                break
            elif title == prefix:  # Query is exactly the prefix
                title = ""
                break
        
        # If title is empty after removing prefix, use original query
        if not title:
            title = original_query
        
        # Capitalize first letter
        title = title[0].upper() + title[1:] if len(title) > 1 else title.upper()
        
        # Truncate at word boundary if too long
        if len(title) > max_length:
            truncated = title[:max_length].rsplit(' ', 1)[0]
            title = truncated + "..." if truncated else title[:max_length] + "..."
        
        return title if title else "New Conversation"
    
    def _group_by_date(self, conversations: List[Dict]) -> Dict[str, List[Dict]]:
        """Group conversations by date (Today, Yesterday, This Week, Older)"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        today = now.date()
        yesterday = (now - timedelta(days=1)).date()
        week_ago = (now - timedelta(days=7)).date()
        
        grouped = {
            "today": [],
            "yesterday": [],
            "this_week": [],
            "older": []
        }
        
        for conv in conversations:
            # Parse updated_at
            updated_at = datetime.fromisoformat(conv['updated_at'])
            conv_date = updated_at.date()
            
            if conv_date == today:
                grouped["today"].append(conv)
            elif conv_date == yesterday:
                grouped["yesterday"].append(conv)
            elif conv_date >= week_ago:
                grouped["this_week"].append(conv)
            else:
                grouped["older"].append(conv)
        
        return grouped
    
    async def close(self):
        """Cleanup"""
        pass  # aiosqlite handles connection pooling

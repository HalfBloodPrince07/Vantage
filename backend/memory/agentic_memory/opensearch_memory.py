# backend/memory/agentic_memory/opensearch_memory.py
"""
OpenSearch-based storage for Agentic Memories
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger

from .note import AgenticNote


MEMORY_INDEX_MAPPING = {
    "settings": {
        "index": {
            "knn": True,
            "knn.algo_param.ef_search": 100
        },
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "content": {"type": "text", "analyzer": "standard"},
            "context": {"type": "text", "analyzer": "standard"},
            "keywords": {"type": "keyword"},
            "tags": {"type": "keyword"},
            "links": {"type": "keyword"},
            "causal_links": {"type": "keyword"},
            "importance": {"type": "float"},
            "confidence": {"type": "float"},
            "access_count": {"type": "integer"},
            "user_id": {"type": "keyword"},
            "session_id": {"type": "keyword"},
            "episode_id": {"type": "keyword"},
            "note_type": {"type": "keyword"},
            "modality": {"type": "keyword"},
            "source_type": {"type": "keyword"},
            "verification_status": {"type": "keyword"},
            "contradicts": {"type": "keyword"},
            "version": {"type": "integer"},
            "thumbnail_path": {"type": "keyword"},
            "metadata": {"type": "object", "enabled": False},
            "embedding": {
                "type": "knn_vector",
                "dimension": 768,
                "method": {
                    "name": "hnsw",
                    "space_type": "innerproduct",
                    "engine": "faiss",
                    "parameters": {"ef_construction": 128, "m": 16}
                }
            },
            "media_embedding": {
                "type": "knn_vector",
                "dimension": 512,
                "method": {
                    "name": "hnsw",
                    "space_type": "innerproduct",
                    "engine": "faiss"
                }
            },
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    }
}


class AgenticMemoryStore:
    def __init__(self, opensearch_client, index_name: str = "vantage_memories"):
        self.client = opensearch_client
        self.index_name = index_name

    async def create_index(self) -> bool:
        try:
            exists = await self.client.client.indices.exists(index=self.index_name)
            if not exists:
                await self.client.client.indices.create(
                    index=self.index_name,
                    body=MEMORY_INDEX_MAPPING
                )
                logger.info(f"Created agentic memory index: {self.index_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to create memory index: {e}")
            return False

    async def store_note(self, note: AgenticNote) -> bool:
        try:
            doc = note.to_dict()
            doc.pop("embedding", None) if note.embedding is None else None
            doc.pop("media_embedding", None) if note.media_embedding is None else None
            
            await self.client.client.index(
                index=self.index_name,
                id=note.id,
                body=doc,
                refresh=True
            )
            logger.debug(f"Stored note: {note.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store note: {e}")
            return False

    async def get_note(self, note_id: str) -> Optional[AgenticNote]:
        try:
            result = await self.client.client.get(
                index=self.index_name,
                id=note_id
            )
            if result.get("found"):
                return AgenticNote.from_dict(result["_source"])
            return None
        except Exception as e:
            logger.error(f"Failed to get note {note_id}: {e}")
            return None

    async def update_note(self, note: AgenticNote) -> bool:
        note.updated_at = datetime.utcnow().isoformat()
        return await self.store_note(note)

    async def delete_note(self, note_id: str) -> bool:
        try:
            await self.client.client.delete(
                index=self.index_name,
                id=note_id,
                refresh=True
            )
            logger.debug(f"Deleted note: {note_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete note {note_id}: {e}")
            return False

    async def search_by_vector(
        self,
        embedding: List[float],
        user_id: str,
        k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        try:
            must_clauses = [{"term": {"user_id": user_id}}]
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        must_clauses.append({"terms": {key: value}})
                    else:
                        must_clauses.append({"term": {key: value}})

            query = {
                "size": k,
                "query": {
                    "bool": {
                        "must": must_clauses,
                        "should": [
                            {
                                "knn": {
                                    "embedding": {
                                        "vector": embedding,
                                        "k": k
                                    }
                                }
                            }
                        ]
                    }
                }
            }

            result = await self.client.client.search(
                index=self.index_name,
                body=query
            )

            hits = []
            for hit in result["hits"]["hits"]:
                hits.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    **hit["_source"]
                })
            return hits
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []

    async def search_by_text(
        self,
        query: str,
        user_id: str,
        k: int = 10,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        try:
            must_clauses = [
                {"term": {"user_id": user_id}},
                {
                    "multi_match": {
                        "query": query,
                        "fields": ["content^2", "context", "keywords^1.5", "tags"],
                        "type": "best_fields"
                    }
                }
            ]
            if filters:
                for key, value in filters.items():
                    if isinstance(value, list):
                        must_clauses.append({"terms": {key: value}})
                    else:
                        must_clauses.append({"term": {key: value}})

            result = await self.client.client.search(
                index=self.index_name,
                body={"size": k, "query": {"bool": {"must": must_clauses}}}
            )

            hits = []
            for hit in result["hits"]["hits"]:
                hits.append({
                    "id": hit["_id"],
                    "score": hit["_score"],
                    **hit["_source"]
                })
            return hits
        except Exception as e:
            logger.error(f"Text search failed: {e}")
            return []

    async def get_user_notes(
        self,
        user_id: str,
        limit: int = 100,
        offset: int = 0,
        note_type: Optional[str] = None
    ) -> List[AgenticNote]:
        try:
            must_clauses = [{"term": {"user_id": user_id}}]
            if note_type:
                must_clauses.append({"term": {"note_type": note_type}})

            result = await self.client.client.search(
                index=self.index_name,
                body={
                    "size": limit,
                    "from": offset,
                    "query": {"bool": {"must": must_clauses}},
                    "sort": [{"updated_at": "desc"}]
                }
            )

            return [AgenticNote.from_dict(hit["_source"]) for hit in result["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Failed to get user notes: {e}")
            return []

    async def get_linked_notes(self, note_id: str) -> List[AgenticNote]:
        note = await self.get_note(note_id)
        if not note or not note.links:
            return []
        
        linked = []
        for link_id in note.links:
            linked_note = await self.get_note(link_id)
            if linked_note:
                linked.append(linked_note)
        return linked

    async def count_notes(self, user_id: Optional[str] = None) -> int:
        try:
            query = {"match_all": {}}
            if user_id:
                query = {"term": {"user_id": user_id}}
            
            result = await self.client.client.count(
                index=self.index_name,
                body={"query": query}
            )
            return result["count"]
        except Exception as e:
            logger.error(f"Failed to count notes: {e}")
            return 0

    async def get_notes_by_importance(
        self,
        user_id: str,
        max_importance: float,
        limit: int = 100
    ) -> List[AgenticNote]:
        try:
            result = await self.client.client.search(
                index=self.index_name,
                body={
                    "size": limit,
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"user_id": user_id}},
                                {"range": {"importance": {"lte": max_importance}}}
                            ]
                        }
                    },
                    "sort": [{"importance": "asc"}]
                }
            )
            return [AgenticNote.from_dict(hit["_source"]) for hit in result["hits"]["hits"]]
        except Exception as e:
            logger.error(f"Failed to get notes by importance: {e}")
            return []

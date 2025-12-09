# backend/opensearch_client.py - Enhanced OpenSearch Client

from opensearchpy import AsyncOpenSearch
from typing import List, Dict, Any, Optional
import numpy as np
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential


class OpenSearchClient:
    """
    Enhanced OpenSearch client with:
    - Hybrid search (Vector + BM25)
    - Better filtering
    - Improved scoring
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.index_name = config['opensearch']['index_name']
        
        # Initialize client with authentication
        self.client = AsyncOpenSearch(
            hosts=[{
                'host': config['opensearch']['host'],
                'port': config['opensearch']['port']
            }],
            http_auth=(
                config['opensearch']['auth']['username'],
                config['opensearch']['auth']['password']
            ),
            use_ssl=config['opensearch'].get('use_ssl', True),
            verify_certs=config['opensearch'].get('verify_certs', False),
            ssl_show_warn=False,
            timeout=30
        )
        
        # Hybrid search settings
        self.hybrid_enabled = config['search']['hybrid']['enabled']
        self.vector_weight = config['search']['hybrid']['vector_weight']
        self.bm25_weight = config['search']['hybrid']['bm25_weight']
        
        logger.info(f"OpenSearch client initialized (Hybrid: {self.hybrid_enabled})")

    async def create_index(self):
        """Create index with k-NN and BM25 settings - summary-based indexing (no chunks)"""
        mapping = {
            "settings": {
                "index": {
                    "knn": True,
                    "knn.algo_param.ef_search": 100
                },
                "analysis": {
                    "analyzer": {
                        "content_analyzer": {
                            "type": "standard",
                            "stopwords": "_english_"
                        }
                    }
                }
            },
            "mappings": {
                "properties": {
                    # Core identifier
                    "id": {"type": "keyword"},
                    
                    # File metadata
                    "filename": {
                        "type": "text",
                        "analyzer": "content_analyzer",
                        "fields": {"keyword": {"type": "keyword"}}
                    },
                    "file_path": {"type": "keyword"},
                    "file_type": {"type": "keyword"},           # .pdf, .docx, .png, etc.
                    "content_type": {"type": "keyword"},        # text, image, spreadsheet
                    "document_type": {"type": "keyword"},       # report, invoice, screenshot, etc.
                    "is_image": {"type": "boolean"},
                    
                    # Document content (summary-based approach)
                    "detailed_summary": {
                        "type": "text",
                        "analyzer": "content_analyzer"
                    },
                    "full_content": {
                        "type": "text",
                        "analyzer": "content_analyzer"
                    },
                    
                    # Extracted metadata
                    "keywords": {
                        "type": "text",
                        "analyzer": "content_analyzer"
                    },
                    "entities": {"type": "keyword"},
                    "topics": {"type": "keyword"},
                    
                    # Vector embedding (of detailed_summary)
                    "vector_embedding": {
                        "type": "knn_vector",
                        "dimension": self.config['models']['embedding']['dimension'],
                        "method": {
                            "name": "hnsw",
                            "space_type": "innerproduct",
                            "engine": "faiss",
                            "parameters": {"ef_construction": 128, "m": 24}
                        }
                    },
                    
                    # Document statistics
                    "word_count": {"type": "integer"},
                    "page_count": {"type": "integer"},
                    "file_size_bytes": {"type": "long"},
                    
                    # Timestamps
                    "created_at": {"type": "date"},
                    "last_modified": {"type": "date"}
                }
            }
        }
        
        try:
            exists = await self.client.indices.exists(index=self.index_name)
            if not exists:
                await self.client.indices.create(index=self.index_name, body=mapping)
                logger.info(f"Created index: {self.index_name}")
            else:
                logger.info(f"Index already exists: {self.index_name}")
        except Exception as e:
            logger.error(f"Index creation error: {e}")
            raise

    async def document_exists(self, doc_id: str) -> bool:
        try:
            return await self.client.exists(index=self.index_name, id=doc_id)
        except Exception:
            return False

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def index_document(self, doc: Dict[str, Any]):
        try:
            await self.client.index(
                index=self.index_name,
                id=doc['id'],
                body=doc,
                refresh=True
            )
            logger.debug(f"Indexed document: {doc['filename']}")
        except Exception as e:
            logger.error(f"Document indexing error: {e}")
            raise

    def _format_filters(self, filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Normalize filters into OpenSearch DSL format.
        Fixes issue where agents pass simplified dicts like {'file_type': ['.pdf']}
        """
        if not filters:
            return []
        
        # If it already looks like DSL, wrap in list if needed
        if any(k in filters for k in ['term', 'terms', 'range', 'bool', 'match', 'multi_match']):
             return [filters]

        formatted = []
        for key, value in filters.items():
            if key == 'time_range':
                # Simplified time range handling could go here
                pass
            elif isinstance(value, list):
                formatted.append({"terms": {key: value}})
            else:
                formatted.append({"term": {key: value}})
        return formatted

    async def hybrid_search(
        self,
        query: str,
        query_vector: List[float],
        top_k: int = 50,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining vector similarity and BM25 text matching.
        """
        # Format filters correctly
        formatted_filters = self._format_filters(filters) if filters else None
        
        # Vector search query
        vector_query = {
            "size": top_k,
            "query": {
                "knn": {
                    "vector_embedding": {
                        "vector": query_vector,
                        "k": top_k
                    }
                }
            },
            "_source": {"excludes": ["vector_embedding"]}
        }
        
        # BM25 text search query
        bm25_query = {
            "size": top_k,
            "query": {
                "bool": {
                    "should": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": [
                                    "detailed_summary^3",
                                    "full_content^2",
                                    "filename^2",
                                    "keywords^4"
                                ],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        },
                        {
                            "match_phrase": {
                                "detailed_summary": {
                                    "query": query,
                                    "boost": 2
                                }
                            }
                        }
                    ],
                    "minimum_should_match": 1
                }
            },
            "_source": {"excludes": ["vector_embedding"]}
        }
        
        # Apply filters if provided
        if formatted_filters:
            vector_query["query"] = {
                "bool": {
                    "must": [vector_query["query"]],
                    "filter": formatted_filters
                }
            }
            if "filter" not in bm25_query["query"]["bool"]:
                bm25_query["query"]["bool"]["filter"] = []
            
            # Ensure it is a list
            if isinstance(bm25_query["query"]["bool"]["filter"], list):
                bm25_query["query"]["bool"]["filter"].extend(formatted_filters)
            else:
                bm25_query["query"]["bool"]["filter"] = [bm25_query["query"]["bool"]["filter"]] + formatted_filters
        
        try:
            # Execute both searches
            vector_response = await self.client.search(index=self.index_name, body=vector_query)
            bm25_response = await self.client.search(index=self.index_name, body=bm25_query)
            
            # Combine results using RRF
            combined = self._reciprocal_rank_fusion(
                vector_response['hits']['hits'],
                bm25_response['hits']['hits'],
                k=60
            )
            
            return combined[:top_k]
            
        except Exception as e:
            logger.error(f"Hybrid search error: {e}")
            return await self.vector_search(query_vector, top_k, filters)

    def _reciprocal_rank_fusion(
        self,
        vector_hits: List[Dict],
        bm25_hits: List[Dict],
        k: int = 60
    ) -> List[Dict[str, Any]]:
        scores = {}
        docs = {}
        
        for rank, hit in enumerate(vector_hits):
            doc_id = hit['_id']
            rrf_score = self.vector_weight / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
            if doc_id not in docs:
                docs[doc_id] = {'id': doc_id, 'vector_score': hit['_score'], **hit['_source']}
        
        for rank, hit in enumerate(bm25_hits):
            doc_id = hit['_id']
            rrf_score = self.bm25_weight / (k + rank + 1)
            scores[doc_id] = scores.get(doc_id, 0) + rrf_score
            if doc_id not in docs:
                docs[doc_id] = {'id': doc_id, 'bm25_score': hit['_score'], **hit['_source']}
            else:
                docs[doc_id]['bm25_score'] = hit['_score']
        
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        
        results = []
        for doc_id in sorted_ids:
            doc = docs[doc_id]
            doc['score'] = scores[doc_id]
            doc['hybrid'] = True
            results.append(doc)
        
        return results

    async def vector_search(
        self,
        query_vector: List[float],
        top_k: int = 25,
        filters: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """Fallback vector-only search"""
        formatted_filters = self._format_filters(filters) if filters else None

        query = {
            "size": top_k,
            "query": {
                "knn": {
                    "vector_embedding": {
                        "vector": query_vector,
                        "k": top_k
                    }
                }
            },
            "_source": {"excludes": ["vector_embedding"]}
        }
        
        if formatted_filters:
            query["query"] = {
                "bool": {
                    "must": [query["query"]],
                    "filter": formatted_filters
                }
            }
            
        try:
            response = await self.client.search(index=self.index_name, body=query)
            results = []
            for hit in response['hits']['hits']:
                results.append({
                    'id': hit['_id'],
                    'score': hit['_score'],
                    **hit['_source']
                })
            return results
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []


    async def get_document(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a single document by ID"""
        try:
            response = await self.client.get(index=self.index_name, id=doc_id)
            if response and response.get('found'):
                doc = response['_source']
                doc['id'] = doc_id
                return doc
            return None
        except Exception as e:
            logger.error(f"Document retrieval error for {doc_id}: {e}")
            return None

    async def delete_document(self, doc_id: str):
        try:
            await self.client.delete(index=self.index_name, id=doc_id, refresh=True)
            logger.debug(f"Deleted document: {doc_id}")
        except Exception as e:
            logger.error(f"Document deletion error: {e}")
            raise

    async def get_stats(self) -> Dict[str, Any]:
        try:
            stats = await self.client.count(index=self.index_name)
            return {"count": stats['count']}
        except Exception:
            return {"count": 0}

    async def get_cluster_data(self) -> Optional[Dict[str, Any]]:
        try:
            response = await self.client.search(
                index=self.index_name,
                body={
                    "size": 1000,
                    "query": {"match_all": {}},
                    "_source": ["filename", "vector_embedding", "cluster_id"]
                }
            )
            
            if not response['hits']['hits']:
                return None
                
            vectors = []
            labels = []
            cluster_ids = []
            
            for hit in response['hits']['hits']:
                source = hit['_source']
                vectors.append(source['vector_embedding'])
                labels.append(source['filename'])
                cluster_ids.append(source.get('cluster_id', 0))
                
            from umap import UMAP
            reducer = UMAP(n_components=2, random_state=42)
            coords_2d = reducer.fit_transform(np.array(vectors))
            
            return {
                "x": coords_2d[:, 0].tolist(),
                "y": coords_2d[:, 1].tolist(),
                "labels": labels,
                "cluster_ids": cluster_ids
            }
        except Exception as e:
            logger.error(f"Cluster data error: {e}")
            return None

    async def ping(self) -> bool:
        try:
            await self.client.ping()
            return True
        except:
            return False

    async def close(self):
        await self.client.close()
        
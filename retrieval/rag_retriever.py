
"""RAG检索服务"""
from typing import List, Dict, Any, Optional
import asyncio
from database.mongodb import ChunkRepository, mongodb_client
from database.qdrant_client import qdrant_client
from database.neo4j_client import neo4j_client
from embedding.embedding_service import embedding_service
from services.knowledge_extraction_service import knowledge_extraction_service
from utils.logger import logger

try:
    # 暂时禁用 sentence_transformers，因为它在当前环境会导致进程崩溃
    # from sentence_transformers import CrossEncoder
    # HAS_RERANKER = True
    HAS_RERANKER = False
    logger.warning("sentence-transformers 已暂时禁用以防止崩溃")
except Exception as e:
    HAS_RERANKER = False
    logger.warning(f"sentence-transformers 加载失败，重排功能不可用: {e}")

class RAGRetriever:
    """RAG检索器（混合检索：向量检索 + 关键词检索 + 图谱检索 + 重排）"""
    
    def __init__(
        self,
        top_k: int = 5,
        score_threshold: float = 0.5
    ):
        """
        初始化RAG检索器
        
        Args:
            top_k: 返回的检索结果数量
            score_threshold: 相似度阈值
        """
        self.top_k = top_k
        self.score_threshold = score_threshold
        self.chunk_repo = ChunkRepository(mongodb_client)
        self.reranker = None
        if HAS_RERANKER:
            try:
                # 使用轻量级重排模型
                # 可以选择 'BAAI/bge-reranker-base' 或其他模型
                # self.reranker = CrossEncoder('BAAI/bge-reranker-base', device='cpu') # 根据环境可选择 'cuda'
                # logger.info("重排模型加载成功: BAAI/bge-reranker-base")
                pass
            except Exception as e:
                logger.warning(f"重排模型加载失败: {e}")

    def retrieve(self, query: str, document_id: Optional[str] = None, collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        同步检索方法（向后兼容，但不推荐用于新功能）
        注意：此方法无法使用异步的图谱检索和实体提取，会降级为基础检索。
        """
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                 # 这是一个hack，如果在运行中的loop里调用同步方法，我们无法直接运行async
                 # 这里只能降级为仅使用向量+关键词检索
                 logger.warning("在运行中的循环中调用同步 retrieve，降级为基础检索")
                 return self._basic_retrieve(query, document_id, collection_name)
            else:
                 return loop.run_until_complete(self.retrieve_async(query, document_id, collection_name))
        except RuntimeError:
            return asyncio.run(self.retrieve_async(query, document_id, collection_name))

    async def retrieve_async(self, query: str, document_id: Optional[str] = None, collection_name: Optional[str] = None, embedding_model: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        异步检索相关文档块 (High-level RAG)
        
        Args:
            query: 查询文本
            document_id: 可选的文档ID过滤
            collection_name: 可选的集合名称（用于多助手支持）
            embedding_model: 可选的向量模型名称
        
        Returns:
            检索结果列表，包含文本、相似度分数、元数据等
        """
        # 1. 并行执行多种检索策略
        tasks = [
            self._vector_search(query, document_id, collection_name, embedding_model),
            self._keyword_search(query, document_id),
            self._graph_search(query, document_id)
        ]
        
        results_list = await asyncio.gather(*tasks)
        vector_results, keyword_results, graph_results = results_list
        
        # 2. 混合检索结果（合并和初步去重）
        merged_results = self._merge_results(vector_results, keyword_results, graph_results)
        
        # 3. 重排 (Rerank)
        if self.reranker and merged_results:
            reranked_results = self._rerank(query, merged_results)
            return reranked_results[:self.top_k]
        
        # 4. 如果没有重排，直接返回按合并分数排序的结果
        return merged_results[:self.top_k]

    def _basic_retrieve(self, query: str, document_id: Optional[str] = None, collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """仅包含向量和关键词的基础检索"""
        vector_results = asyncio.run(self._vector_search(query, document_id, collection_name))
        keyword_results = asyncio.run(self._keyword_search(query, document_id))
        merged = self._merge_results(vector_results, keyword_results, [])
        return merged[:self.top_k]

    async def _vector_search(self, query: str, document_id: Optional[str], collection_name: Optional[str], embedding_model: Optional[str] = None) -> List[Dict[str, Any]]:
        """向量检索"""
        try:
            # 向量化查询文本 (可能是同步的，但在 executor 中运行比较好，或者假设很快)
            query_vector = embedding_service.encode_single(query, model_name=embedding_model)
            
            filter_conditions = None
            if document_id:
                filter_conditions = {"document_id": document_id}
            
            from database.qdrant_client import get_qdrant_client
            if collection_name:
                client = get_qdrant_client(collection_name)
            else:
                client = qdrant_client
            
            # search 是同步的，但 Qdrant 客户端可能是 HTTP 调用
            # 这里为了简单直接调用
            results = client.search(
                query_vector=query_vector,
                limit=self.top_k * 2,
                score_threshold=self.score_threshold,
                filter_conditions=filter_conditions,
                query_text=query
            )
            return results
        except Exception as e:
            logger.error(f"向量检索失败: {e}")
            return []

    async def _keyword_search(self, query: str, document_id: Optional[str]) -> List[Dict[str, Any]]:
        """关键词检索"""
        try:
            # 获取所有相关块 (对于大文档库这可能很慢，需要优化，比如只检索最近的或限制数量)
            # 这里简单实现，假设 MongoDB 查询够快
            if document_id:
                # 只有指定文档时才做全量关键词匹配，否则太慢
                chunks = self.chunk_repo.get_chunks_by_document(document_id)
            else:
                return [] # 全局关键词检索太慢，跳过
            
            query_keywords = set(query.lower().split())
            results = []
            
            for chunk in chunks:
                chunk_text = chunk.get("text", "").lower()
                matched_keywords = query_keywords.intersection(set(chunk_text.split()))
                if matched_keywords:
                    score = len(matched_keywords) / len(query_keywords)
                    if score > 0.1:
                        results.append({
                            "id": chunk.get("_id"),
                            "score": score,
                            "payload": {
                                "chunk_id": chunk.get("_id"),
                                "document_id": chunk.get("document_id"),
                                "text": chunk.get("text"),
                                "chunk_index": chunk.get("chunk_index"),
                                "metadata": chunk.get("metadata", {})
                            }
                        })
            return sorted(results, key=lambda x: x["score"], reverse=True)[:self.top_k]
        except Exception as e:
            logger.error(f"关键词检索失败: {e}")
            return []

    async def _graph_search(self, query: str, document_id: Optional[str]) -> List[Dict[str, Any]]:
        """图谱检索"""
        try:
            # 1. 提取查询实体
            entities = await knowledge_extraction_service.extract_entities(query)
            if not entities:
                return []
            
            results = []
            if neo4j_client.driver is None:
                neo4j_client.connect()
                
            if neo4j_client.driver:
                for entity in entities:
                    # 查询实体及其一跳邻居
                    cypher = (
                        f"MATCH (n {{name: $name}})-[r]->(m) "
                        f"RETURN n, r, m LIMIT 10"
                    )
                    records = neo4j_client.execute_query(cypher, {"name": entity})
                    
                    if records:
                        # 将图谱路径转化为文本
                        # 格式: Entity -[Relation]-> Entity
                        paths = []
                        for record in records:
                            n = record.get('n', {}).get('name')
                            r_type = record.get('r', {}).get('type') # neo4j driver return structure varies
                            # Check structure of record
                            # record is dict from data()
                            # {'n': {'name': '...'}, 'r': {'name': '...', 'type': '...'}, 'm': {'name': '...'}}
                            # But record.data() usually returns properties. 
                            # Wait, neo4j_client.execute_query returns [record.data() for ...]
                            # record.data() returns {'n': Node(...), ...} -> dict of props
                            # But relationship type is not in props usually.
                            
                            # Let's adjust cypher to return type(r)
                            pass

                # Optimized Cypher to get type
                for entity in entities:
                    cypher = (
                        f"MATCH (n {{name: $name}})-[r]->(m) "
                        f"RETURN n.name as head, type(r) as relation, m.name as tail, r.source_doc as doc_id, r.source_chunk as chunk_id LIMIT 10"
                    )
                    records = neo4j_client.execute_query(cypher, {"name": entity})
                    
                    if records:
                        text_parts = []
                        chunk_ids = set()
                        doc_ids = set()
                        
                        for record in records:
                            head = record.get('head')
                            relation = record.get('relation')
                            tail = record.get('tail')
                            if head and relation and tail:
                                text_parts.append(f"{head} {relation} {tail}")
                            
                            if record.get('chunk_id'):
                                chunk_ids.add(record.get('chunk_id'))
                            if record.get('doc_id'):
                                doc_ids.add(record.get('doc_id'))
                        
                        if text_parts:
                            # 构造一个虚拟的 chunk 结果
                            # 如果有 doc_id 过滤，需要检查
                            if document_id and document_id not in doc_ids:
                                continue
                                
                            combined_text = "Knowledge Graph Context:\n" + "\n".join(text_parts)
                            results.append({
                                "id": f"graph_{entity}",
                                "score": 0.8, # 给图谱检索较高的初始分
                                "payload": {
                                    "text": combined_text,
                                    "retrieval_type": "graph",
                                    "entities": entities,
                                    "chunk_ids": list(chunk_ids)
                                }
                            })
            return results
        except Exception as e:
            logger.error(f"图谱检索失败: {e}")
            return []

    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        graph_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并多种检索结果"""
        result_dict = {}
        
        # 1. 向量结果 (Base)
        for res in vector_results:
            key = res["payload"].get("chunk_id") or res["id"]
            res["payload"]["retrieval_type"] = "vector"
            result_dict[key] = res
            
        # 2. 关键词结果 (Boost)
        for res in keyword_results:
            key = res["payload"].get("chunk_id") or res["id"]
            if key in result_dict:
                # Boost score
                result_dict[key]["score"] += res["score"] * 0.3
                result_dict[key]["payload"]["retrieval_type"] = "hybrid"
            else:
                res["payload"]["retrieval_type"] = "keyword"
                result_dict[key] = res
                
        # 3. 图谱结果 (Add)
        # 图谱结果通常不是原始 chunk，而是生成的知识文本
        for res in graph_results:
            key = res["id"]
            res["payload"]["retrieval_type"] = "graph"
            result_dict[key] = res
            
        merged = list(result_dict.values())
        merged.sort(key=lambda x: x["score"], reverse=True)
        return merged

    def _rerank(self, query: str, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """使用 Cross-Encoder 重排"""
        if not self.reranker or not results:
            return results
            
        try:
            # 准备 pairs [query, doc_text]
            pairs = []
            for res in results:
                text = res["payload"].get("text", "")
                pairs.append([query, text])
            
            # 预测分数
            scores = self.reranker.predict(pairs)
            
            # 更新分数并排序
            for i, score in enumerate(scores):
                results[i]["score"] = float(score)
                # 归一化分数? BGE reranker 输出 logits，可能需要 sigmoid，但直接排序即可
                
            results.sort(key=lambda x: x["score"], reverse=True)
            return results
        except Exception as e:
            logger.error(f"重排失败: {e}")
            return results


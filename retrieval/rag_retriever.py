
"""RAG检索服务"""
from typing import List, Dict, Any, Optional
import asyncio
import os
from database.mongodb import ChunkRepository, mongodb_client
from database.qdrant_client import qdrant_client
from database.neo4j_client import neo4j_client
from embedding.embedding_service import embedding_service
from services.knowledge_extraction_service import knowledge_extraction_service
from utils.logger import logger
from utils.token_utils import truncate_to_tokens

def _env_flag(name: str, default: str = "0") -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "y", "on")

class RAGRetriever:
    """RAG检索器（混合检索：向量检索 + 关键词检索 + 图谱检索 + 重排）"""
    
    def __init__(
        self,
        final_k: int = 5,
        score_threshold: float = 0.5,
        prefetch_k: Optional[int] = None,
        enable_reranker: Optional[bool] = None,
        reranker_model: Optional[str] = None,
        reranker_device: Optional[str] = None,
        reranker_max_tokens: int = 512,
    ):
        """
        初始化RAG检索器
        
        Args:
            final_k: 最终返回的检索结果数量（用于拼上下文）
            score_threshold: 相似度阈值
            prefetch_k: 向量检索候选池大小（用于重排/动态裁剪），默认按 final_k 放大
            enable_reranker: 是否启用重排（默认读取环境变量 ENABLE_RERANKER）
            reranker_model: CrossEncoder 模型名（默认读取环境变量 RERANKER_MODEL）
            reranker_device: cpu/cuda（默认读取环境变量 RERANKER_DEVICE）
            reranker_max_tokens: 送入 CrossEncoder 的文本最大 token（近似预算）
        """
        self.final_k = final_k
        self.prefetch_k = prefetch_k or max(50, final_k * 10)
        self.score_threshold = score_threshold
        self.chunk_repo = ChunkRepository(mongodb_client)
        self._reranker = None
        self.enable_reranker = _env_flag("ENABLE_RERANKER", "0") if enable_reranker is None else bool(enable_reranker)
        self.reranker_model = reranker_model or os.getenv("RERANKER_MODEL", "BAAI/bge-reranker-base")
        self.reranker_device = reranker_device or os.getenv("RERANKER_DEVICE", "cpu")
        self.reranker_max_tokens = reranker_max_tokens

    def _get_reranker(self):
        """延迟加载 CrossEncoder，避免导入阶段崩溃影响服务启动。"""
        if not self.enable_reranker:
            return None
        if self._reranker is not None:
            return self._reranker
        try:
            from sentence_transformers import CrossEncoder  # type: ignore

            self._reranker = CrossEncoder(self.reranker_model, device=self.reranker_device)
            logger.info(f"重排模型加载成功: {self.reranker_model} ({self.reranker_device})")
            return self._reranker
        except Exception as e:
            # 失败自动降级，避免反复尝试
            self.enable_reranker = False
            logger.warning(f"重排模型加载失败，已自动禁用重排: {e}")
            self._reranker = None
            return None

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
        # 运行时开关：决定是否启用图谱检索/重排等高耗模块
        try:
            from services.runtime_config import get_runtime_config

            runtime_cfg = await get_runtime_config()
            modules = runtime_cfg.get("modules") or {}
            if not bool(modules.get("rerank_enabled", True)):
                self.enable_reranker = False
        except Exception:
            modules = {}

        graph_enabled = bool(modules.get("kg_retrieve_enabled", True))

        # 1. 并行执行多种检索策略
        tasks = [
            self._vector_search(query, document_id, collection_name, embedding_model),
            self._keyword_search(query, document_id),
            (self._graph_search(query, document_id) if graph_enabled else asyncio.sleep(0, result=[])),
        ]
        
        results_list = await asyncio.gather(*tasks)
        vector_results, keyword_results, graph_results = results_list
        
        # 2. 混合检索结果（合并和初步去重）
        merged_results = self._merge_results(vector_results, keyword_results, graph_results)
        
        # 3. 重排 (Rerank)
        reranker = self._get_reranker()
        if reranker and merged_results:
            reranked_results = self._rerank(query, merged_results, reranker=reranker)
            # 在线动态裁剪 k：基于重排分数分布自适应（兼顾 recall/precision）
            k = self._dynamic_k_from_scores(reranked_results, default_k=self.final_k)
            return reranked_results[:k]
        
        # 4. 如果没有重排，直接返回按合并分数排序的结果
        return merged_results[: self.final_k]

    def _dynamic_k_from_scores(self, results: List[Dict[str, Any]], default_k: int) -> int:
        """
        在线动态调 k（仅在 reranker 启用时生效）。
        - 区分度高（top1 与 topN 差距大）：减小 k 提升 precision
        - 区分度低（分数接近）：增大 k 保留 recall
        """
        if not results:
            return int(default_k)
        scores = [float(r.get("score", 0.0) or 0.0) for r in results]
        k_min = int(os.getenv("DYNK_MIN", "8"))
        k_max = int(os.getenv("DYNK_MAX", str(max(default_k, 24))))

        # 默认 k
        k = int(default_k)

        # 仅在有足够候选时判断
        if len(scores) >= max(10, default_k):
            s1 = scores[0]
            s10 = scores[min(9, len(scores) - 1)]
            gap = s1 - s10

            # gap 大：强相关集中
            if gap >= float(os.getenv("DYNK_GAP_HIGH", "2.0")):
                k = max(k_min, min(k, 12))
            # gap 小：区分度差，需要更多证据
            elif gap <= float(os.getenv("DYNK_GAP_LOW", "0.6")):
                k = min(k_max, max(k, 24))

        return max(k_min, min(k_max, k))

    def _basic_retrieve(self, query: str, document_id: Optional[str] = None, collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """仅包含向量和关键词的基础检索"""
        vector_results = asyncio.run(self._vector_search(query, document_id, collection_name))
        keyword_results = asyncio.run(self._keyword_search(query, document_id))
        merged = self._merge_results(vector_results, keyword_results, [])
        return merged[: self.final_k]

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
                limit=self.prefetch_k,
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
            return sorted(results, key=lambda x: x["score"], reverse=True)[:self.final_k]
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

    def _rerank(self, query: str, results: List[Dict[str, Any]], reranker) -> List[Dict[str, Any]]:
        """使用 Cross-Encoder 重排"""
        if not reranker or not results:
            return results
            
        try:
            # 准备 pairs [query, doc_text]
            pairs = []
            for res in results:
                text = res["payload"].get("text", "")
                # 控制送入 CrossEncoder 的 token 预算，避免长 chunk 造成延迟/崩溃
                text = truncate_to_tokens(text, self.reranker_max_tokens)
                pairs.append([query, text])
            
            # 预测分数
            scores = reranker.predict(pairs)
            
            # 更新分数并排序
            for i, score in enumerate(scores):
                results[i]["score"] = float(score)
                # 归一化分数? BGE reranker 输出 logits，可能需要 sigmoid，但直接排序即可
                
            results.sort(key=lambda x: x["score"], reverse=True)
            return results
        except Exception as e:
            logger.error(f"重排失败: {e}")
            return results


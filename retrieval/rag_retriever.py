"""RAG检索服务"""
from typing import List, Dict, Any, Optional
from database.mongodb import ChunkRepository, mongodb_client
from database.qdrant_client import qdrant_client
from embedding.embedding_service import embedding_service


class RAGRetriever:
    """RAG检索器（混合检索：向量检索 + 关键词检索）"""
    
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
    
    def retrieve(self, query: str, document_id: Optional[str] = None, collection_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        检索相关文档块
        
        Args:
            query: 查询文本
            document_id: 可选的文档ID过滤
            collection_name: 可选的集合名称（用于多助手支持）
        
        Returns:
            检索结果列表，包含文本、相似度分数、元数据等
        """
        # 1. 向量化查询文本
        query_vector = embedding_service.encode_single(query)
        
        # 2. 向量检索
        filter_conditions = None
        if document_id:
            filter_conditions = {"document_id": document_id}
        
        # 选择使用的Qdrant客户端
        from database.qdrant_client import get_qdrant_client
        if collection_name:
            client = get_qdrant_client(collection_name)
        else:
            client = qdrant_client
        
        vector_results = []
        try:
            vector_results = client.search(
                query_vector=query_vector,
                limit=self.top_k * 2,  # 获取更多结果用于混合检索
                score_threshold=self.score_threshold,
                filter_conditions=filter_conditions,
                query_text=query  # 传递原始查询文本
            )
        except Exception as e:
            # 如果 Qdrant 不可用，只使用关键词检索
            print(f"警告: Qdrant 检索失败: {e}")
        
        # 3. 关键词检索（简单的文本匹配）
        keyword_results = self._keyword_search(query, document_id)
        
        # 4. 混合检索结果（合并和去重）
        merged_results = self._merge_results(vector_results, keyword_results)
        
        # 5. 返回top_k结果
        return merged_results[:self.top_k]
    
    def _keyword_search(
        self,
        query: str,
        document_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """关键词检索（简单实现）"""
        # 获取所有相关块
        if document_id:
            chunks = self.chunk_repo.get_chunks_by_document(document_id)
        else:
            # 这里可以优化：只搜索部分文档
            chunks = []
        
        # 简单的关键词匹配
        query_keywords = set(query.lower().split())
        results = []
        
        for chunk in chunks:
            chunk_text = chunk.get("text", "").lower()
            # 计算关键词匹配度
            matched_keywords = query_keywords.intersection(set(chunk_text.split()))
            if matched_keywords:
                score = len(matched_keywords) / len(query_keywords)
                results.append({
                    "id": chunk.get("_id"),
                    "score": score,
                    "payload": {
                        "chunk_id": chunk.get("_id"),
                        "document_id": chunk.get("document_id"),
                        "text": chunk.get("text"),
                        "chunk_index": chunk.get("chunk_index")
                    }
                })
        
        return sorted(results, key=lambda x: x["score"], reverse=True)
    
    def _merge_results(
        self,
        vector_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """合并向量检索和关键词检索结果"""
        # 创建结果字典（按ID去重）
        result_dict = {}
        
        # 添加向量检索结果（权重较高）
        for result in vector_results:
            chunk_id = result["payload"].get("chunk_id")
            if chunk_id:
                result_dict[chunk_id] = {
                    **result,
                    "retrieval_type": "vector",
                    "combined_score": result["score"] * 0.7  # 向量检索权重0.7
                }
        
        # 添加关键词检索结果
        for result in keyword_results:
            chunk_id = result["payload"].get("chunk_id")
            if chunk_id:
                if chunk_id in result_dict:
                    # 如果已存在，合并分数
                    result_dict[chunk_id]["combined_score"] += result["score"] * 0.3
                    result_dict[chunk_id]["retrieval_type"] = "hybrid"
                else:
                    result_dict[chunk_id] = {
                        **result,
                        "retrieval_type": "keyword",
                        "combined_score": result["score"] * 0.3  # 关键词检索权重0.3
                    }
        
        # 按合并分数排序
        merged_results = list(result_dict.values())
        merged_results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        return merged_results
    
    def get_context(self, query: str, document_id: Optional[str] = None, collection_name: Optional[str] = None) -> str:
        """
        获取检索到的上下文文本
        
        Args:
            query: 查询文本
            document_id: 可选的文档ID过滤
            collection_name: 可选的集合名称（用于多助手支持）
        
        Returns:
            合并后的上下文文本
        """
        results = self.retrieve(query, document_id, collection_name)
        context_parts = []
        
        for result in results:
            text = result["payload"].get("text", "")
            if text:
                context_parts.append(text)
        
        return "\n\n".join(context_parts)


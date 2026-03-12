"""RAG服务核心逻辑"""
from typing import Dict, Any, Optional
import asyncio
from utils.logger import logger


class RAGService:
    """RAG服务封装（通过HTTP调用知识库服务）"""
    
    async def retrieve_context(
        self,
        query: str,
        document_id: Optional[str] = None,
        assistant_id: Optional[str] = None,
        collection_name: Optional[str] = None,
        conversation_id: Optional[str] = None,
        knowledge_space_ids: Optional[list[str]] = None,
    ) -> Dict[str, Any]:
        """
        检索相关上下文（并行检索文档和资源）
        
        Args:
            query: 用户查询
            document_id: 可选的文档ID过滤
            assistant_id: 可选的助手ID（用于获取集合名称）
            collection_name: 可选的集合名称（如果提供则直接使用）
            conversation_id: 可选的对话ID（如果提供，会同时检索对话专用向量空间）
        
        Returns:
            包含上下文、来源信息和推荐资源的字典
        """
        from database.mongodb import mongodb
        # 解析需要检索的集合列表（知识空间优先）
        collection_names: list[str] = []
        if knowledge_space_ids:
            try:
                from bson import ObjectId
                spaces = mongodb.get_collection("knowledge_spaces")
                for sid in knowledge_space_ids:
                    try:
                        doc = await spaces.find_one({"_id": ObjectId(sid)})
                        if doc and doc.get("collection_name"):
                            collection_names.append(doc["collection_name"])
                    except Exception:
                        continue
            except Exception as e:
                logger.warning(f"获取知识空间集合名称失败: {str(e)}")

        # 兼容：如果没有知识空间选择，则按旧 assistant_id/collection_name
        if not collection_names:
            if assistant_id and not collection_name:
                try:
                    from bson import ObjectId
                    collection = mongodb.get_collection("course_assistants")
                    assistant_doc = await collection.find_one({"_id": ObjectId(assistant_id)})
                    if assistant_doc:
                        collection_name = assistant_doc.get("collection_name")
                except Exception as e:
                    logger.warning(f"获取助手集合名称失败: {str(e)}")
            collection_names = [collection_name or "default_knowledge"]
        
        # 并行检索文档和资源
        loop = asyncio.get_event_loop()
        
        # 文档检索任务（知识空间集合，可多集合并行）
        from retrieval.rag_retriever import RAGRetriever
        doc_retriever = RAGRetriever(top_k=100, score_threshold=0.7)
        
        # 使用异步检索方法 (retrieve_async)
        doc_tasks = [
            doc_retriever.retrieve_async(query, document_id, cn)
            for cn in collection_names
        ]
        
        # 等待文档检索完成并合并
        results_list = await asyncio.gather(*doc_tasks) if doc_tasks else [[]]
        results = []
        for part in results_list:
            results.extend(part or [])
        logger.info(f"知识空间检索完成 - 集合数: {len(collection_names)}, 结果数: {len(results)}")
        logger.info(f"RAG检索完成 - 文档结果: {len(results)} 个")
        
        # 构建上下文和来源（包含文档信息）
        context_parts = []
        sources = []
        
        # 获取所有涉及的文档ID和文件ID（对话附件兼容）
        document_ids = set()
        file_ids = set()
        for result in results:
            doc_id = result["payload"].get("document_id")
            if doc_id:
                document_ids.add(doc_id)
            # 对话附件使用 file_id
            file_id = result["payload"].get("file_id")
            if file_id:
                file_ids.add(file_id)
        
        # 批量查询文档信息
        document_info_map = {}
        if document_ids:
            try:
                from database.mongodb import mongodb_client, DocumentRepository
                # 确保 MongoDB 客户端已连接
                if mongodb_client.db is None:
                    mongodb_client.connect()
                doc_repo = DocumentRepository(mongodb_client)
                
                for doc_id in document_ids:
                    try:
                        doc = doc_repo.get_document(doc_id)
                        if doc:
                            # 使用实际文件名，如果没有标题则使用文档ID的一部分
                            doc_title = doc.get("title") or doc.get("file_path", "").split("/")[-1] or f"文档_{doc_id[:8]}"
                            document_info_map[doc_id] = {
                                "title": doc_title,
                                "file_type": doc.get("file_type", ""),
                                "status": doc.get("status", "")
                            }
                    except Exception as e:
                        logger.warning(f"获取文档信息失败 - 文档ID: {doc_id}, 错误: {str(e)}")
                        # 使用文档ID的一部分作为标题
                        document_info_map[doc_id] = {
                            "title": f"文档_{doc_id[:8]}",
                            "file_type": "",
                            "status": ""
                        }
            except Exception as e:
                logger.warning(f"批量查询文档信息失败: {str(e)}")
        
        # 用于去重相同文档：每个文档只保留最高分的chunk
        document_sources_map = {}  # {document_id: source_info}
        
        for result in results:
            text = result["payload"].get("text", "")
            if text:
                context_parts.append(text)
                doc_id = result["payload"].get("document_id")
                file_id = result["payload"].get("file_id")
                conversation_id = result["payload"].get("conversation_id")
                
                score = result.get("score", 0) or result.get("combined_score", 0)
                
                # 判断是文档还是对话附件
                if file_id and conversation_id:
                    # 对话附件
                    filename = result["payload"].get("filename", f"附件_{file_id[:8]}")
                    source_key = f"conversation_{conversation_id}_{file_id}"
                    source_info = {
                        "chunk_id": result["payload"].get("chunk_id"),
                        "file_id": file_id,
                        "conversation_id": conversation_id,
                        "score": score,
                        "retrieval_type": result.get("retrieval_type", "vector"),
                        "document_title": filename,
                        "file_type": result["payload"].get("metadata", {}).get("file_type", ""),
                        "is_conversation_attachment": True
                    }
                else:
                    # 普通文档
                    doc_info = document_info_map.get(doc_id, {})
                    doc_title = doc_info.get("title") or f"文档_{doc_id[:8]}"
                    source_key = doc_id
                    source_info = {
                        "chunk_id": result["payload"].get("chunk_id"),
                        "document_id": doc_id,
                        "score": score,
                        "retrieval_type": result.get("retrieval_type", "vector"),
                        "document_title": doc_title,
                        "file_type": doc_info.get("file_type", ""),
                        "status": doc_info.get("status", ""),
                        "is_conversation_attachment": False
                    }
                
                # 如果该来源还没有记录，或者当前chunk的分数更高，则更新
                if source_key not in document_sources_map or score > document_sources_map[source_key]["score"]:
                    document_sources_map[source_key] = source_info
        
        # 将去重后的来源转换为列表，并按分数排序
        sources = list(document_sources_map.values())
        sources.sort(key=lambda x: x["score"], reverse=True)
        
        context = "\n\n".join(context_parts)
        
        return {
            "context": context,
            "sources": sources,
            "recommended_resources": []
        }
    
    async def generate_response(
        self,
        query: str,
        document_id: Optional[str] = None,
        use_context: bool = True,
        fallback_on_error: bool = True,
        assistant_id: Optional[str] = None,
        collection_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        生成回复（包含RAG检索）
        
        Args:
            query: 用户查询
            document_id: 可选的文档ID过滤
            use_context: 是否使用RAG上下文
            fallback_on_error: 当检索失败时是否回退到不使用上下文（默认True）
            assistant_id: 可选的助手ID（用于获取集合名称）
            collection_name: 可选的集合名称（如果提供则直接使用）
        
        Returns:
            包含回复和来源信息的字典
        """
        context = None
        sources = []
        
        if use_context:
            try:
                retrieval_result = await self.retrieve_context(query, document_id, assistant_id, collection_name)
                context = retrieval_result["context"]
                sources = retrieval_result["sources"]
                logger.info(f"RAG检索成功 - 检索到 {len(sources)} 个来源")
            except Exception as e:
                error_msg = str(e)
                logger.warning(f"RAG检索失败: {error_msg}")
                
                if fallback_on_error:
                    logger.info("回退到不使用上下文的模式继续处理")
                    # 返回空上下文，让服务继续运行
                    context = None
                    sources = []
                else:
                    # 如果不允许回退，重新抛出异常
                    raise
        
        return {
            "context": context,
            "sources": sources,
            "recommended_resources": retrieval_result.get("recommended_resources", [])
        }


# 全局RAG服务实例
rag_service = RAGService()


"""AI智能体工具函数库 - 允许AI调用这些函数获取基础数据"""
from typing import Dict, Any, List, Optional, Callable
from utils.logger import logger
import requests
import os
import json
from database.mongodb import mongodb


class AITools:
    """AI工具函数库"""
    
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}
        self.functions: Dict[str, Callable] = {}
        self._register_tools()
    
    def _register_tools(self):
        """注册所有可用的工具函数"""
        # 工具1: 获取Ollama模型列表
        self.register_tool(
            name="get_available_ollama_models",
            description="获取当前可用的Ollama推理模型列表。当用户询问可用模型、模型列表、有哪些模型等问题时调用此函数。",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            },
            function=self._get_available_ollama_models
        )
        
        # 工具2: 获取知识库文档列表
        self.register_tool(
            name="get_knowledge_base_documents",
            description="获取知识库中的文档列表。当用户询问知识库有哪些文档、文档列表、文档数量、知识库现在有什么文档等问题时，必须调用此函数来实时获取最新信息。",
            parameters={
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "返回的文档数量限制，默认10",
                        "default": 10
                    },
                    "assistant_id": {
                        "type": "string",
                        "description": "助手ID（可选），如果提供则获取该助手知识库的文档列表"
                    }
                },
                "required": []
            },
            function=self._get_knowledge_base_documents
        )
        
        # 工具3: 获取系统信息
        self.register_tool(
            name="get_system_info",
            description="获取系统基本信息，包括当前使用的模型、向量化模型、知识库状态等。当用户询问系统信息、当前配置、用了什么模型、知识库情况等问题时，必须调用此函数来实时获取最新信息。",
            parameters={
                "type": "object",
                "properties": {
                    "assistant_id": {
                        "type": "string",
                        "description": "助手ID（可选），如果提供则获取该助手的特定配置"
                    }
                },
                "required": []
            },
            function=self._get_system_info
        )
        
        # 工具4: 获取知识库详细统计
        self.register_tool(
            name="get_knowledge_base_stats",
            description="获取知识库的详细统计信息，包括文档数量、向量数量、各状态文档统计等。当用户询问知识库状态、知识库信息、知识库统计等问题时，必须调用此函数来实时获取最新信息。",
            parameters={
                "type": "object",
                "properties": {
                    "assistant_id": {
                        "type": "string",
                        "description": "助手ID（可选），如果提供则获取该助手知识库的统计信息"
                    }
                },
                "required": []
            },
            function=self._get_knowledge_base_stats
        )
    
    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        function: Callable
    ):
        """
        注册一个工具函数
        
        Args:
            name: 工具名称
            description: 工具描述
            parameters: 工具参数定义（JSON Schema格式）
            function: 工具函数实现
        """
        self.tools[name] = {
            "name": name,
            "description": description,
            "parameters": parameters
        }
        self.functions[name] = function
        logger.debug(f"注册AI工具: {name}")
    
    def get_tools_schema(self) -> List[Dict[str, Any]]:
        """
        获取所有工具的JSON Schema定义
        
        Returns:
            工具列表（OpenAI Function Calling格式）
        """
        return list(self.tools.values())
    
    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Any:
        """
        调用指定的工具函数
        
        Args:
            name: 工具名称
            arguments: 工具参数
        
        Returns:
            工具函数的返回值
        """
        if name not in self.functions:
            raise ValueError(f"未知的工具函数: {name}")
        
        try:
            func = self.functions[name]
            if arguments:
                return func(**arguments)
            else:
                return func()
        except Exception as e:
            logger.error(f"调用工具函数 {name} 失败: {str(e)}", exc_info=True)
            raise
    
    def _get_available_ollama_models(self) -> Dict[str, Any]:
        """
        获取当前可用的Ollama推理模型列表
        
        Returns:
            包含模型列表的字典
        """
        try:
            ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
            if "host.docker.internal" not in ollama_base_url and "localhost" in ollama_base_url:
                ollama_base_url = ollama_base_url.replace("localhost", "127.0.0.1")
            
            session = requests.Session()
            session.verify = False
            
            response = session.get(
                f"{ollama_base_url}/api/tags",
                timeout=5.0
            )
            response.raise_for_status()
            result = response.json()
            
            models = result.get("models", [])
            
            # 过滤掉向量模型（embedding模型）
            embedding_keywords = [
                "embedding", "bge", "multilingual", "text-embedding",
                "sentence", "nomic-embed", "mxbai-embed"
            ]
            
            inference_models = []
            for model in models:
                model_name = model.get("name", "")
                # 跳过embedding模型
                if any(keyword in model_name.lower() for keyword in embedding_keywords):
                    continue
                
                inference_models.append({
                    "name": model_name,
                    "size": model.get("size", 0),
                    "modified_at": model.get("modified_at", "")
                })
            
            # 按名称排序
            inference_models.sort(key=lambda x: x["name"])
            
            logger.info(f"获取Ollama模型列表成功 - 找到 {len(inference_models)} 个推理模型")
            
            return {
                "success": True,
                "models": inference_models,
                "count": len(inference_models),
                "message": f"当前有 {len(inference_models)} 个可用的推理模型"
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"获取Ollama模型列表失败: {str(e)}")
            return {
                "success": False,
                "models": [],
                "count": 0,
                "error": f"无法连接到Ollama服务: {str(e)}"
            }
        except Exception as e:
            logger.error(f"获取Ollama模型列表失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "models": [],
                "count": 0,
                "error": f"获取模型列表时发生错误: {str(e)}"
            }
    
    def _get_knowledge_base_documents(self, limit: int = 10, assistant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取知识库中的文档列表（实时获取）
        
        Args:
            limit: 返回的文档数量限制
            assistant_id: 助手ID（可选），如果提供则获取该助手知识库的文档列表
        
        Returns:
            包含文档列表的字典
        """
        try:
            import asyncio
            
            async def _fetch_docs():
                collection = mongodb.get_collection("documents")
                
                query = {}
                if assistant_id:
                    query["assistant_id"] = assistant_id
                
                # 获取文档列表（按创建时间倒序）
                cursor = collection.find(query).sort("created_at", -1).limit(limit)
                documents = []
                
                async for doc in cursor:
                    documents.append({
                        "id": str(doc["_id"]),
                        "title": doc.get("title", "未命名文档"),
                        "file_type": doc.get("file_type", ""),
                        "status": doc.get("status", ""),
                        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else "",
                        "file_size": doc.get("file_size", 0)
                    })
                
                total = await collection.count_documents(query)
                
                return documents, total
            
            # 执行异步查询
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _fetch_docs())
                        documents, total = future.result()
                else:
                    documents, total = loop.run_until_complete(_fetch_docs())
            except RuntimeError:
                documents, total = asyncio.run(_fetch_docs())
            
            logger.info(f"获取知识库文档列表成功 - 助手ID: {assistant_id or '全部'}, 总数: {total}, 返回: {len(documents)}")
            
            result = {
                "success": True,
                "documents": documents,
                "total": total,
                "returned": len(documents),
                "message": f"知识库共有 {total} 个文档，返回了最新的 {len(documents)} 个（实时数据）"
            }
            
            if assistant_id:
                result["assistant_id"] = assistant_id
                result["message"] = f"助手知识库共有 {total} 个文档，返回了最新的 {len(documents)} 个（实时数据）"
            
            return result
        except Exception as e:
            logger.error(f"获取知识库文档列表失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "documents": [],
                "total": 0,
                "returned": 0,
                "error": f"获取文档列表时发生错误: {str(e)}"
            }
    
    def _get_system_info(self, assistant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取系统基本信息（实时获取当前配置）
        
        Args:
            assistant_id: 助手ID（可选），如果提供则获取该助手的特定配置
        
        Returns:
            包含系统信息的字典
        """
        try:
            import os
            import asyncio
            
            # 默认模型（从环境变量）
            default_generation_model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
            from embedding.embedding_service import embedding_service
            default_embedding_model = embedding_service.model_name if hasattr(embedding_service, 'model_name') else "未知"
            
            # 实际使用的模型（从assistant配置或默认值）
            actual_generation_model = default_generation_model
            actual_embedding_model = default_embedding_model
            assistant_name = None
            
            # 如果提供了assistant_id，获取该assistant的配置
            async def _get_assistant_config():
                if not assistant_id:
                    return None, None, None
                
                try:
                    collection = mongodb.get_collection("course_assistants")
                    assistant_doc = await collection.find_one({"_id": assistant_id})
                    if assistant_doc:
                        assistant_name = assistant_doc.get("name", "")
                        inference_model = assistant_doc.get("inference_model")
                        embedding_model = assistant_doc.get("embedding_model")
                        return inference_model or default_generation_model, embedding_model or default_embedding_model, assistant_name
                except Exception as e:
                    logger.warning(f"获取助手配置失败: {str(e)}")
                return None, None, None
            
            # 执行异步查询
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _get_assistant_config())
                        inf_model, emb_model, name = future.result()
                else:
                    inf_model, emb_model, name = loop.run_until_complete(_get_assistant_config())
            except RuntimeError:
                inf_model, emb_model, name = asyncio.run(_get_assistant_config())
            
            if inf_model:
                actual_generation_model = inf_model
            if emb_model:
                actual_embedding_model = emb_model
            if name:
                assistant_name = name
            
            # 获取知识库统计（异步）
            async def _get_stats():
                collection = mongodb.get_collection("documents")
                
                query = {}
                if assistant_id:
                    query["assistant_id"] = assistant_id
                
                total_docs = await collection.count_documents(query)
                completed_docs = await collection.count_documents({**query, "status": "completed"})
                processing_docs = await collection.count_documents({**query, "status": "processing"})
                failed_docs = await collection.count_documents({**query, "status": "failed"})
                
                return {
                    "total_documents": total_docs,
                    "completed": completed_docs,
                    "processing": processing_docs,
                    "failed": failed_docs
                }
            
            # 执行异步查询
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _get_stats())
                        kb_stats = future.result()
                else:
                    kb_stats = loop.run_until_complete(_get_stats())
            except RuntimeError:
                kb_stats = asyncio.run(_get_stats())
            
            logger.info(f"获取系统信息成功 - 助手ID: {assistant_id or '默认'}, 推理模型: {actual_generation_model}, 向量化模型: {actual_embedding_model}")
            
            result = {
                "success": True,
                "generation_model": actual_generation_model,
                "embedding_model": actual_embedding_model,
                "knowledge_base": kb_stats,
                "message": "系统信息获取成功（实时数据）"
            }
            
            if assistant_id and assistant_name:
                result["assistant_id"] = assistant_id
                result["assistant_name"] = assistant_name
                result["message"] = f"助手 '{assistant_name}' 的系统信息获取成功（实时数据）"
            
            return result
        except Exception as e:
            logger.error(f"获取系统信息失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"获取系统信息时发生错误: {str(e)}"
            }
    
    def _get_knowledge_base_stats(self, assistant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取知识库的详细统计信息（实时获取）
        
        Args:
            assistant_id: 助手ID（可选），如果提供则获取该助手知识库的统计信息
        
        Returns:
            包含知识库统计信息的字典
        """
        try:
            import asyncio
            
            async def _get_detailed_stats():
                collection = mongodb.get_collection("documents")
                chunks_collection = mongodb.get_collection("chunks")
                
                query = {}
                if assistant_id:
                    query["assistant_id"] = assistant_id
                
                # 文档统计
                total_docs = await collection.count_documents(query)
                completed_docs = await collection.count_documents({**query, "status": "completed"})
                processing_docs = await collection.count_documents({**query, "status": "processing"})
                failed_docs = await collection.count_documents({**query, "status": "failed"})
                
                # 获取文档列表（最新的10个）
                cursor = collection.find(query).sort("created_at", -1).limit(10)
                recent_docs = []
                async for doc in cursor:
                    recent_docs.append({
                        "id": str(doc["_id"]),
                        "title": doc.get("title", "未命名文档"),
                        "file_type": doc.get("file_type", ""),
                        "status": doc.get("status", ""),
                        "created_at": doc.get("created_at").isoformat() if doc.get("created_at") else "",
                        "file_size": doc.get("file_size", 0)
                    })
                
                # 文本块统计
                chunk_query = {}
                if assistant_id:
                    # 通过文档ID关联查询
                    doc_ids = []
                    async for doc in collection.find(query, {"_id": 1}):
                        doc_ids.append(str(doc["_id"]))
                    if doc_ids:
                        chunk_query["document_id"] = {"$in": doc_ids}
                    else:
                        chunk_query["document_id"] = {"$in": []}  # 空列表，不会有结果
                
                total_chunks = await chunks_collection.count_documents(chunk_query) if chunk_query.get("document_id") else await chunks_collection.count_documents({})
                
                # 向量统计（从Qdrant获取）
                total_vectors = 0
                try:
                    from database.qdrant_client import get_qdrant_client
                    if assistant_id:
                        # 获取assistant的collection_name
                        assistant_collection = mongodb.get_collection("course_assistants")
                        assistant_doc = await assistant_collection.find_one({"_id": assistant_id})
                        if assistant_doc:
                            collection_name = assistant_doc.get("collection_name", "sensor_knowledge")
                            qdrant = get_qdrant_client(collection_name)
                            total_vectors = qdrant.get_collection_info().get("points_count", 0)
                    else:
                        # 默认集合
                        qdrant = get_qdrant_client("sensor_knowledge")
                        total_vectors = qdrant.get_collection_info().get("points_count", 0)
                except Exception as e:
                    logger.warning(f"获取向量统计失败: {str(e)}")
                
                return {
                    "total_documents": total_docs,
                    "completed": completed_docs,
                    "processing": processing_docs,
                    "failed": failed_docs,
                    "total_chunks": total_chunks,
                    "total_vectors": total_vectors,
                    "recent_documents": recent_docs
                }
            
            # 执行异步查询
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as executor:
                        future = executor.submit(asyncio.run, _get_detailed_stats())
                        stats = future.result()
                else:
                    stats = loop.run_until_complete(_get_detailed_stats())
            except RuntimeError:
                stats = asyncio.run(_get_detailed_stats())
            
            logger.info(f"获取知识库统计成功 - 助手ID: {assistant_id or '全部'}, 文档数: {stats['total_documents']}, 向量数: {stats['total_vectors']}")
            
            result = {
                "success": True,
                **stats,
                "message": f"知识库统计信息获取成功（实时数据）- 共有 {stats['total_documents']} 个文档，{stats['total_chunks']} 个文本块，{stats['total_vectors']} 个向量"
            }
            
            if assistant_id:
                result["assistant_id"] = assistant_id
                result["message"] = f"助手知识库统计信息获取成功（实时数据）- 共有 {stats['total_documents']} 个文档，{stats['total_chunks']} 个文本块，{stats['total_vectors']} 个向量"
            
            return result
        except Exception as e:
            logger.error(f"获取知识库统计失败: {str(e)}", exc_info=True)
            return {
                "success": False,
                "error": f"获取知识库统计时发生错误: {str(e)}"
            }


# 全局AI工具实例
ai_tools = AITools()


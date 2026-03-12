
from typing import Optional, Type, Dict, Any
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
import asyncio
from services.rag_service import rag_service

class RAGQueryInput(BaseModel):
    query: str = Field(description="知识检索的查询字符串")
    document_id: Optional[str] = Field(description="可选的文档ID过滤", default=None)

class RAGTool(BaseTool):
    name: str = "rag_knowledge_search"
    description: str = "使用此工具从文档数据库和知识图谱中检索领域知识。返回相关上下文。"
    args_schema: Type[BaseModel] = RAGQueryInput

    def _run(self, query: str, document_id: Optional[str] = None) -> str:
        """
        工具的同步执行方法
        
        Args:
            query: 查询字符串
            document_id: 文档ID过滤
            
        Returns:
            检索到的上下文文本
        """
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果我们在事件循环中，不能直接运行 run_until_complete
                # 这是同步工具在异步环境中的限制，没有 nest_asyncio 的情况下
                # 我们应该优先使用异步执行
                return "Error: Use async execution for this tool."
            else:
                result = loop.run_until_complete(rag_service.retrieve_context(query, document_id))
                return result.get("context", "No context found.")
        except RuntimeError:
            # 没有运行中的循环
            result = asyncio.run(rag_service.retrieve_context(query, document_id))
            return result.get("context", "No context found.")

    async def _arun(self, query: str, document_id: Optional[str] = None) -> str:
        """
        工具的异步执行方法
        
        Args:
            query: 查询字符串
            document_id: 文档ID过滤
            
        Returns:
            检索到的上下文文本
        """
        result = await rag_service.retrieve_context(query, document_id)
        return result.get("context", "No context found.")

rag_tool = RAGTool()

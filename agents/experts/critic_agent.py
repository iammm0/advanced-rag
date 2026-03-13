"""批判性思维专家Agent"""
from typing import Dict, Any, Optional, AsyncGenerator
from agents.base.base_agent import BaseAgent
from services.rag_service import rag_service
from utils.logger import logger

class CriticAgent(BaseAgent):
    """批判性思维专家 - 负责验证信息的准确性，检查幻觉，提供反面观点"""
    
    def get_prompt(self) -> str:
        return """你是一个批判性思维专家。你的任务是审查给定的信息或观点，找出潜在的逻辑漏洞、事实错误或幻觉（Hallucination）。

请注意：
1. 你的态度应当是客观、严谨的。
2. 基于检索到的证据进行反驳或确认。
3. 如果发现信息不足以支撑结论，请指出。
4. 提供建设性的修正建议。

输出格式要求：
- **准确性评估**：可信/存疑/不可信。
- **问题点**：列出具体问题。
- **证据对比**：引用检索到的证据。
- **修正建议**：如何改进。
"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行批判性分析任务
        """
        # 1. 执行RAG检索 (获取验证素材)
        rag_context = ""
        sources = []
        
        try:
            logger.info(f"CriticAgent: 开始检索验证素材 - {task[:50]}...")
            retrieval_result = await rag_service.retrieve_context(
                query=task,
                document_id=context.get("document_id") if context else None,
                assistant_id=context.get("assistant_id") if context else None,
                knowledge_space_ids=context.get("knowledge_space_ids") if context else None,
                embedding_model=context.get("generation_config", {}).get("embedding_model") if context else None
            )
            rag_context = retrieval_result.get("context", "")
            sources = retrieval_result.get("sources", [])
        except Exception as e:
            logger.error(f"CriticAgent: 检索失败: {e}")
            yield {
                "type": "error",
                "content": f"检索失败: {str(e)}",
                "agent_type": "critic"
            }
            return

        # 2. 生成分析
        full_response = ""
        try:
            async for chunk in self.ollama_service.generate(
                prompt=f"请批判性地分析以下陈述/问题：'{task}'\n\n基于事实证据：\n{rag_context}",
                context=None,
                stream=stream
            ):
                full_response += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "critic"
                    }
            
            if not stream or full_response:
                yield {
                    "type": "complete",
                    "content": full_response,
                    "agent_type": "critic",
                    "sources": sources
                }
                
        except Exception as e:
            logger.error(f"CriticAgent: 生成失败: {e}")
            yield {
                "type": "error",
                "content": f"生成失败: {str(e)}",
                "agent_type": "critic"
            }

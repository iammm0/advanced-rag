"""物理学课程助手Agent - 封装原有的对话流程（RAG检索 + LLM生成）"""
from typing import Dict, Any, Optional, AsyncGenerator, List
from agents.base.base_agent import BaseAgent
from services.rag_service import rag_service
from services.model_selector import model_selector
from utils.logger import logger


class PhysicsAssistantAgent(BaseAgent):
    """物理学课程助手Agent - 处理常规的物理学课程问答"""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化Agent
        
        Args:
            model_name: 如果提供，则使用指定模型；否则根据问题自动选择
            base_url: Ollama服务地址
        """
        # 如果提供了model_name，使用它；否则在execute时动态选择
        self.fixed_model = model_name
        super().__init__(model_name=None, base_url=base_url)  # 先不设置模型，在execute时动态设置
    
    def get_default_model(self) -> str:
        """获取默认模型名称（实际不使用，会在execute时动态选择）"""
        return "gpt-oss:20b"
    
    def get_prompt(self) -> str:
        """获取系统提示词（注意：实际使用OllamaService的系统提示词）"""
        return """你是一个专业的物理学课程助手，专门帮助学生理解和学习物理学知识。

你的职责：
1. 准确回答学生关于物理学的问题
2. 使用清晰、易懂的语言解释复杂的物理概念
3. 提供相关的公式、示例和实际应用
4. 鼓励学生思考和提问

回答要求：
- 基于提供的上下文信息回答问题
- 如果上下文信息不足，可以结合你的知识进行补充
- 使用Markdown格式组织回答，包括标题、列表、公式等
- 对于公式，使用LaTeX格式（$...$ 或 $$...$$）
- 提供具体的例子帮助理解"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行物理学课程助手任务
        
        Args:
            task: 用户问题
            context: 上下文信息，包含：
                - assistant_id: 助手ID（用于获取系统提示词）
                - conversation_id: 对话ID（可选）
                - document_id: 文档ID（可选）
                - enable_rag: 是否启用RAG检索（默认True）
                - conversation_history: 对话历史（可选）
            stream: 是否流式输出
        
        Yields:
            包含结果和元数据的字典
        """
        # 提取上下文信息
        assistant_id = context.get("assistant_id") if context else None
        knowledge_space_ids = context.get("knowledge_space_ids") if context else None
        document_id = context.get("document_id") if context else None
        enable_rag = context.get("enable_rag", True) if context else True
        conversation_history = context.get("conversation_history") if context else None
        
        # 0. 智能选择模型（如果未固定模型）
        selected_model = self.fixed_model
        if not selected_model:
            try:
                model_selection = model_selector.select_model(task)
                selected_model = model_selection.get("model", "gemma3:1b")
                logger.info(f"PhysicsAssistantAgent: 模型选择 - 问题: {task[:50]}..., 选择模型: {selected_model}, 理由: {model_selection.get('reason', '')}")
            except Exception as e:
                logger.warning(f"PhysicsAssistantAgent: 模型选择失败: {e}，使用默认模型")
                selected_model = "gpt-oss:20b"
        
        # 如果模型已更改，需要重新初始化OllamaService
        if self.ollama_service.model_name != selected_model:
            from services.ollama_service import OllamaService
            self.ollama_service = OllamaService(model_name=selected_model)
            logger.info(f"PhysicsAssistantAgent: 切换模型到 {selected_model}")
        
        # 1. RAG检索（如果启用）
        rag_context = ""
        sources = []
        recommended_resources = []
        
        if enable_rag:
            try:
                logger.info(f"PhysicsAssistantAgent: 开始RAG检索 - 问题: {task[:50]}...")
                retrieval_result = await rag_service.retrieve_context(
                    query=task,
                    document_id=document_id,
                    assistant_id=assistant_id,
                    knowledge_space_ids=knowledge_space_ids,
                )
                
                rag_context = retrieval_result.get("context", "")
                sources = retrieval_result.get("sources", [])
                recommended_resources = retrieval_result.get("recommended_resources", [])
                
                logger.info(f"PhysicsAssistantAgent: RAG检索完成 - 上下文长度: {len(rag_context)}, 来源数: {len(sources)}")
            except Exception as e:
                logger.warning(f"PhysicsAssistantAgent: RAG检索失败: {e}")
                # RAG检索失败不影响继续生成回复
        
        # 2. 获取文档信息和知识库状态（如果需要）
        document_info = None
        knowledge_base_status = None
        
        # 如果提供了document_id，可以获取文档信息（可选）
        # 这里简化处理，不获取文档信息
        
        # 3. 使用OllamaService生成回复（它会自动处理系统提示词、对话历史等）
        try:
            full_response = ""
            async for chunk in self.ollama_service.generate(
                prompt=task,  # 用户问题
                context=rag_context if rag_context else None,  # RAG检索到的上下文
                stream=stream,
                document_id=document_id,
                document_info=document_info,
                knowledge_base_status=knowledge_base_status,
                assistant_id=assistant_id,  # 传递助手ID，用于获取系统提示词
                conversation_history=conversation_history  # 传递对话历史
            ):
                full_response += chunk
                
                # 流式输出时，每次返回一个chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "physics_assistant",
                        "sources": [],  # 流式输出时暂不返回来源，最后统一返回
                        "recommended_resources": []
                    }
            
            # 非流式输出或流式输出结束时，返回完整结果
            if not stream or full_response:
                yield {
                    "type": "complete",
                    "content": full_response,
                    "agent_type": "physics_assistant",
                    "sources": sources,
                    "recommended_resources": recommended_resources,
                    "confidence": 0.8  # 默认置信度
                }
        
        except Exception as e:
            logger.error(f"PhysicsAssistantAgent: 生成回复失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"生成回复时出错: {str(e)}",
                "agent_type": "physics_assistant",
                "sources": sources,
                "recommended_resources": recommended_resources
            }


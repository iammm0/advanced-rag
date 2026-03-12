"""Agent基类 - 定义所有Agent的通用接口和功能"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, AsyncGenerator
from utils.logger import logger
from services.ollama_service import OllamaService


class BaseAgent(ABC):
    """Agent基类 - 所有Agent的基类"""
    
    def __init__(
        self,
        model_name: Optional[str] = None,
        base_url: Optional[str] = None
    ):
        """
        初始化Agent
        
        Args:
            model_name: 使用的模型名称，如果为None则使用默认模型
            base_url: Ollama服务地址，如果为None则使用默认地址
        """
        self.model_name = model_name or self.get_default_model()
        self.ollama_service = OllamaService(base_url=base_url, model_name=self.model_name)
        logger.info(f"{self.__class__.__name__} 初始化完成 - 模型: {self.model_name}")
    
    @abstractmethod
    def get_default_model(self) -> str:
        """
        获取默认模型名称
        
        Returns:
            默认模型名称
        """
        pass
    
    @abstractmethod
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行Agent任务
        
        Args:
            task: 任务描述
            context: 上下文信息（可选）
            stream: 是否流式输出
        
        Yields:
            包含结果和元数据的字典
        """
        pass
    
    def get_tools(self) -> List[Any]:
        """
        获取Agent可用的工具列表
        
        Returns:
            工具列表（LangChain Tools）
        """
        return []
    
    def get_prompt(self) -> str:
        """
        获取Agent的系统提示词
        
        Returns:
            系统提示词
        """
        return ""
    
    async def _call_llm(
        self,
        prompt: str,
        context: Optional[str] = None,
        stream: bool = False
    ) -> AsyncGenerator[str, None]:
        """
        调用LLM生成回复
        
        Args:
            prompt: 提示词
            context: 上下文信息（可选）
            stream: 是否流式输出
        
        Yields:
            生成的文本片段
        """
        async for chunk in self.ollama_service.generate(
            prompt=prompt,
            context=context,
            stream=stream
        ):
            yield chunk
    
    def _build_prompt(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        构建完整的提示词
        
        Args:
            task: 任务描述
            context: 上下文信息（可选）
        
        Returns:
            完整的提示词
        """
        system_prompt = self.get_prompt()
        
        if context:
            context_str = "\n".join([f"{k}: {v}" for k, v in context.items()])
            return f"{system_prompt}\n\n上下文信息:\n{context_str}\n\n任务: {task}"
        
        return f"{system_prompt}\n\n任务: {task}"


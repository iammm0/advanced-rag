"""示例生成专家Agent"""
from typing import Dict, Any, Optional, AsyncGenerator
from agents.base.base_agent import BaseAgent
from utils.logger import logger


class ExampleGenerationAgent(BaseAgent):
    """示例生成专家 - 生成实际应用示例"""
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "gpt-oss:20b"
    
    def get_prompt(self) -> str:
        """获取系统提示词"""
        return """你是示例生成专家，专门生成实际应用示例。

你的任务：
1. 根据问题生成相关的实际应用示例
2. 提供具体的数值计算示例
3. 说明示例的物理意义
4. 提供多种类型的示例（简单到复杂）"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行示例生成任务"""
        try:
            example_prompt = f"""请为以下问题生成实际应用示例：

问题：{task}

请提供：
1. 简单的应用示例
2. 中等难度的计算示例
3. 复杂的实际应用场景
4. 每个示例包含完整的解题过程"""
            
            result = ""
            async for chunk in self._call_llm(prompt=self.merge_system_into_task_prompt(example_prompt), stream=stream):
                result += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "example_generation"
                    }
            
            if result:
                yield {
                    "type": "complete",
                    "content": result,
                    "agent_type": "example_generation",
                    "confidence": 0.85
                }
        
        except Exception as e:
            logger.error(f"ExampleGenerationAgent: 执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"示例生成失败: {str(e)}",
                "agent_type": "example_generation"
            }


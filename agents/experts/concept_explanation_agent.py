"""概念解释专家Agent"""
from typing import Dict, Any, Optional, AsyncGenerator
from agents.base.base_agent import BaseAgent
from utils.logger import logger


class ConceptExplanationAgent(BaseAgent):
    """概念解释专家 - 深入解释专业概念"""
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "gpt-oss:20b"
    
    def get_prompt(self) -> str:
        """获取系统提示词"""
        return """你是概念解释专家，专门深入解释物理学专业概念。

你的任务：
1. 清晰定义概念
2. 解释概念的本质和内涵
3. 说明概念的应用场景
4. 提供相关的例子和类比
5. 解释概念之间的关系"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行概念解释任务"""
        try:
            explanation_prompt = f"""请深入解释以下物理学概念：

问题：{task}

请提供：
1. 概念的定义
2. 概念的物理意义
3. 相关的公式和定律
4. 实际应用示例
5. 与其他概念的关系"""
            
            result = ""
            async for chunk in self._call_llm(prompt=self.merge_system_into_task_prompt(explanation_prompt), stream=stream):
                result += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "concept_explanation"
                    }
            
            if result:
                yield {
                    "type": "complete",
                    "content": result,
                    "agent_type": "concept_explanation",
                    "confidence": 0.9
                }
        
        except Exception as e:
            logger.error(f"ConceptExplanationAgent: 执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"概念解释失败: {str(e)}",
                "agent_type": "concept_explanation"
            }


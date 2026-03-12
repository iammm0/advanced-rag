"""代码分析专家Agent"""
from typing import Dict, Any, Optional, AsyncGenerator
from agents.base.base_agent import BaseAgent
from utils.logger import logger


class CodeAnalysisAgent(BaseAgent):
    """代码分析专家 - 分析代码示例和技术实现"""
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "gpt-oss:20b"
    
    def get_prompt(self) -> str:
        """获取系统提示词"""
        return """你是代码分析专家，专门分析代码示例和技术实现。

你的任务：
1. 分析代码的功能和逻辑
2. 解释代码的关键部分
3. 指出代码的优缺点
4. 提供改进建议
5. 说明代码的应用场景"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行代码分析任务"""
        try:
            # 检查是否包含代码
            if "```" not in task and "def " not in task and "class " not in task:
                yield {
                    "type": "complete",
                    "content": "未检测到代码，此问题可能不需要代码分析。",
                    "agent_type": "code_analysis",
                    "confidence": 0.3
                }
                return
            
            analysis_prompt = f"""请分析以下代码相关问题：

问题：{task}

请提供：
1. 代码功能分析
2. 关键代码段解释
3. 代码实现建议
4. 相关技术说明"""
            
            result = ""
            async for chunk in self._call_llm(prompt=analysis_prompt, stream=stream):
                result += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "code_analysis"
                    }
            
            if result:
                yield {
                    "type": "complete",
                    "content": result,
                    "agent_type": "code_analysis",
                    "confidence": 0.85
                }
        
        except Exception as e:
            logger.error(f"CodeAnalysisAgent: 执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"代码分析失败: {str(e)}",
                "agent_type": "code_analysis"
            }


"""科学计算编码专家Agent"""
from typing import Dict, Any, Optional, AsyncGenerator
from agents.base.base_agent import BaseAgent
from utils.logger import logger


class ScientificCodingAgent(BaseAgent):
    """科学计算编码专家 - 专注于MATLAB、Python等科学计算编程"""
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "gpt-oss:20b"
    
    def get_prompt(self) -> str:
        """获取系统提示词"""
        return """你是科学计算编码专家，专门生成用于物理学研究的代码。

你的专长：
1. MATLAB科学计算编程
2. Python科学计算（NumPy、SciPy、Matplotlib等）
3. 数据可视化代码（用于论文）
4. 科学计算软件交互代码
5. 数据处理和分析代码

代码要求：
- 符合学术规范
- 包含详细的注释
- 使用清晰的变量命名
- 提供使用示例"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行科学计算编码任务"""
        try:
            coding_prompt = f"""请为以下需求生成科学计算代码：

需求：{task}

请提供：
1. 完整的代码实现（MATLAB或Python）
2. 详细的代码注释
3. 代码使用说明
4. 示例数据和运行结果
5. 代码说明文档

代码要求：
- 符合学术规范
- 使用清晰的变量命名
- 包含错误处理
- 提供可视化代码（如果适用）"""
            
            result = ""
            async for chunk in self._call_llm(prompt=coding_prompt, stream=stream):
                result += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "scientific_coding"
                    }
            
            if result:
                yield {
                    "type": "complete",
                    "content": result,
                    "agent_type": "scientific_coding",
                    "confidence": 0.85
                }
        
        except Exception as e:
            logger.error(f"ScientificCodingAgent: 执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"代码生成失败: {str(e)}",
                "agent_type": "scientific_coding"
            }


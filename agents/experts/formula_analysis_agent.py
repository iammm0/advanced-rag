"""公式分析专家Agent"""
from typing import Dict, Any, Optional, AsyncGenerator, List
from agents.base.base_agent import BaseAgent
from utils.logger import logger
import re


class FormulaAnalysisAgent(BaseAgent):
    """公式分析专家 - 分析问题中的数学/物理公式"""
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "gemma3:27b"
    
    def get_prompt(self) -> str:
        """获取系统提示词"""
        return """你是公式分析专家，专门分析数学和物理公式。

你的任务：
1. 识别问题中的公式
2. 解释公式的含义和物理意义
3. 分析公式中各个变量的含义
4. 说明公式的适用条件和应用场景
5. 提供公式的推导过程（如果相关）"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行公式分析任务"""
        try:
            # 提取公式
            formulas = self._extract_formulas(task)
            
            if not formulas:
                yield {
                    "type": "complete",
                    "content": "未检测到公式，此问题可能不需要公式分析。",
                    "agent_type": "formula_analysis",
                    "confidence": 0.3
                }
                return
            
            # 构建分析提示词
            formulas_text = "\n".join([f"- {f}" for f in formulas])
            analysis_prompt = f"""请分析以下公式：

问题：{task}

检测到的公式：
{formulas_text}

请详细分析：
1. 每个公式的物理意义
2. 公式中变量的含义
3. 公式的适用条件
4. 公式的应用场景
5. 相关的推导过程（如果适用）"""
            
            result = ""
            async for chunk in self._call_llm(prompt=self.merge_system_into_task_prompt(analysis_prompt), stream=stream):
                result += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "formula_analysis"
                    }
            
            if result:
                yield {
                    "type": "complete",
                    "content": result,
                    "agent_type": "formula_analysis",
                    "formulas": formulas,
                    "confidence": 0.9
                }
        
        except Exception as e:
            logger.error(f"FormulaAnalysisAgent: 执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"公式分析失败: {str(e)}",
                "agent_type": "formula_analysis"
            }
    
    def _extract_formulas(self, text: str) -> List[str]:
        """从文本中提取公式"""
        formulas = []
        
        # 匹配LaTeX公式
        latex_patterns = [
            r'\$\$.*?\$\$',  # 块级公式
            r'\$[^\$]+\$',    # 行内公式
            r'\\\[.*?\\\]',   # LaTeX块级
            r'\\\(.*?\\\)',   # LaTeX行内
        ]
        
        for pattern in latex_patterns:
            matches = re.findall(pattern, text)
            formulas.extend(matches)
        
        return list(set(formulas))  # 去重


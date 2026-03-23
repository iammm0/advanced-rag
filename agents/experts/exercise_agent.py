"""习题专家Agent - 统一处理出题和解题功能"""
from typing import Dict, Any, Optional, AsyncGenerator
from agents.base.base_agent import BaseAgent
from utils.logger import logger


class ExerciseAgent(BaseAgent):
    """习题专家 - 根据知识点生成题目，并提供详细解题步骤"""
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "gemma3:27b"
    
    def get_prompt(self) -> str:
        """获取系统提示词"""
        return """你是习题专家，专门处理物理学习题。

你的任务：
1. 根据知识点生成相关题目（选择题、填空题、计算题、应用题等）
2. 分析并解答用户提出的问题
3. 提供详细的解题步骤，包括：
   - 题目分析
   - 公式推导
   - 计算过程
   - 答案验证
4. 提供多种解题方法（如果适用）"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """执行习题任务"""
        try:
            # 判断是出题还是解题
            is_problem_solving = self._is_problem_solving(task)
            
            if is_problem_solving:
                # 解题模式
                exercise_prompt = f"""请解答以下物理学习题：

题目：{task}

请提供：
1. 题目分析（理解题意，确定已知条件和求解目标）
2. 解题思路（选择合适的方法和公式）
3. 详细解题步骤（包括公式推导和计算过程）
4. 答案验证（检查答案的合理性）
5. 总结（关键知识点和注意事项）"""
            else:
                # 出题模式
                exercise_prompt = f"""请根据以下知识点生成物理学习题：

知识点：{task}

请生成：
1. 选择题（2-3道，包含选项和答案）
2. 填空题（1-2道，包含答案）
3. 计算题（1-2道，包含详细解题步骤）
4. 应用题（1道，结合实际场景）

每道题都要包含：
- 题目内容
- 难度等级
- 参考答案
- 解题思路（计算题和应用题）"""
            
            result = ""
            async for chunk in self._call_llm(prompt=self.merge_system_into_task_prompt(exercise_prompt), stream=stream):
                result += chunk
                if stream:
                    yield {
                        "type": "chunk",
                        "content": chunk,
                        "agent_type": "exercise"
                    }
            
            if result:
                yield {
                    "type": "complete",
                    "content": result,
                    "agent_type": "exercise",
                    "mode": "solving" if is_problem_solving else "generation",
                    "confidence": 0.9
                }
        
        except Exception as e:
            logger.error(f"ExerciseAgent: 执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"习题处理失败: {str(e)}",
                "agent_type": "exercise"
            }
    
    def _is_problem_solving(self, task: str) -> bool:
        """判断是解题还是出题"""
        # 如果包含明显的题目特征，认为是解题
        solving_keywords = ["求", "计算", "求解", "解答", "题目", "题", "已知", "求"]
        return any(keyword in task for keyword in solving_keywords)


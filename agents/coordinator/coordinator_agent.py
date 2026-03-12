"""协调型Agent - 分析用户问题，规划研究任务，分发给专家Agent"""
from typing import Dict, Any, Optional, List, AsyncGenerator
from agents.base.base_agent import BaseAgent
from utils.logger import logger


class CoordinatorAgent(BaseAgent):
    """协调型Agent - 负责任务规划和分发"""
    
    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        """初始化协调型Agent"""
        super().__init__(model_name=model_name or "deepseek-r1:8b", base_url=base_url)
        self.expert_agents = {}  # 专家Agent实例缓存
    
    def get_default_model(self) -> str:
        """获取默认模型名称"""
        return "deepseek-r1:8b"
    
    def get_prompt(self) -> str:
        """获取系统提示词"""
        return """你是一个研究任务协调者，负责分析用户问题并智能选择需要的专家Agent。

你的职责：
1. 分析用户问题的复杂度和需求
2. 判断需要哪些专家Agent参与（只选择必要的，不要选择所有Agent）
3. 为每个选中的Agent分配具体任务
4. 说明选择每个Agent的理由

可用的专家Agent：
- document_retrieval: 文档检索专家（当问题涉及文档、资料、知识库查询时使用）
- formula_analysis: 公式分析专家（当问题涉及数学/物理公式、公式推导、公式解释时使用）
- code_analysis: 代码分析专家（当问题涉及代码理解、代码解释、代码逻辑分析时使用）
- concept_explanation: 概念解释专家（当问题需要深入解释专业概念、理论时使用）
- example_generation: 示例生成专家（当问题需要实际应用示例、案例、实例时使用）
- exercise: 习题专家（当问题需要生成习题、解题过程、练习题时使用）
- scientific_coding: 科学计算编码专家（当问题需要MATLAB/Python科学计算代码时使用）
- summary: 总结专家（当需要总结和归纳多个Agent的研究结果时使用，通常最后调用）

**重要原则**：
- 只选择真正需要的Agent，不要选择所有Agent
- 如果问题很简单，可能只需要1-2个Agent
- 如果问题很复杂，可能需要3-5个Agent
- 必须返回JSON格式的结果，包含选中的Agent列表

请以JSON格式返回规划结果：
{
    "selected_agents": ["agent_type1", "agent_type2", ...],
    "agent_tasks": {
        "agent_type1": "具体任务描述1",
        "agent_type2": "具体任务描述2"
    },
    "reasoning": "选择这些Agent的理由"
}"""
    
    async def execute(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行协调任务
        
        Args:
            task: 用户问题
            context: 上下文信息
            stream: 是否流式输出
        
        Yields:
            包含任务规划结果的字典
        """
        try:
            # 1. 分析问题并规划任务
            logger.info(f"CoordinatorAgent: 开始分析问题 - {task[:50]}...")
            
            planning_prompt = f"""用户问题：{task}

请分析这个问题，智能选择需要的专家Agent（只选择必要的，不要选择所有Agent），并说明每个Agent的具体任务。

请严格按照以下JSON格式返回（不要添加任何其他文本）：
{{
    "selected_agents": ["agent_type1", "agent_type2"],
    "agent_tasks": {{
        "agent_type1": "具体任务描述1",
        "agent_type2": "具体任务描述2"
    }},
    "reasoning": "选择这些Agent的理由"
}}

可用的agent_type值：
- document_retrieval
- formula_analysis
- code_analysis
- concept_explanation
- example_generation
- exercise
- scientific_coding
- summary

请只返回JSON，不要添加任何解释性文字。"""
            
            # 调用LLM进行规划
            planning_result = ""
            async for chunk in self._call_llm(prompt=planning_prompt, stream=False):
                planning_result += chunk
            
            # 解析规划结果
            import json
            import re
            
            selected_agents = []
            agent_tasks = {}
            reasoning = ""
            
            try:
                # 尝试提取JSON（可能包含markdown代码块）
                json_match = re.search(r'\{[\s\S]*\}', planning_result)
                if json_match:
                    json_str = json_match.group(0)
                    parsed = json.loads(json_str)
                    selected_agents = parsed.get("selected_agents", [])
                    agent_tasks = parsed.get("agent_tasks", {})
                    reasoning = parsed.get("reasoning", "")
                else:
                    # 如果没有找到JSON，尝试直接解析
                    parsed = json.loads(planning_result)
                    selected_agents = parsed.get("selected_agents", [])
                    agent_tasks = parsed.get("agent_tasks", {})
                    reasoning = parsed.get("reasoning", "")
            except json.JSONDecodeError as e:
                logger.warning(f"CoordinatorAgent: JSON解析失败，使用默认Agent列表: {e}")
                # 如果解析失败，使用默认的智能选择逻辑
                selected_agents = self._fallback_agent_selection(task)
                reasoning = "JSON解析失败，使用默认选择逻辑"
            
            # 验证选中的Agent是否有效
            valid_agents = ["document_retrieval", "formula_analysis", "code_analysis", 
                          "concept_explanation", "example_generation", "exercise", 
                          "scientific_coding", "summary"]
            selected_agents = [a for a in selected_agents if a in valid_agents]
            
            # 如果解析失败或没有选中任何Agent，使用默认选择
            if not selected_agents:
                logger.warning("CoordinatorAgent: 未选中任何Agent，使用默认选择")
                selected_agents = self._fallback_agent_selection(task)
            
            logger.info(f"CoordinatorAgent: 任务规划完成，选中 {len(selected_agents)} 个Agent: {selected_agents}")
            
            # 2. 返回规划结果
            yield {
                "type": "planning",
                "content": planning_result,
                "agent_type": "coordinator",
                "selected_agents": selected_agents,
                "agent_tasks": agent_tasks,
                "reasoning": reasoning
            }
            
            # 3. 后续会由工作流编排器执行具体的专家Agent任务
            # 这里只负责规划，不执行具体任务
        
        except Exception as e:
            logger.error(f"CoordinatorAgent: 规划失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"任务规划失败: {str(e)}",
                "agent_type": "coordinator"
            }
    
    def _fallback_agent_selection(self, task: str) -> List[str]:
        """
        后备Agent选择逻辑（当JSON解析失败时使用）
        
        Args:
            task: 用户问题
        
        Returns:
            选中的Agent类型列表
        """
        task_lower = task.lower()
        selected = []
        
        # 根据关键词选择Agent
        if any(kw in task_lower for kw in ["文档", "资料", "知识库", "检索", "查询"]):
            selected.append("document_retrieval")
        
        if any(kw in task_lower for kw in ["公式", "推导", "计算", "数学", "物理公式"]):
            selected.append("formula_analysis")
        
        if any(kw in task_lower for kw in ["代码", "程序", "编程", "算法"]):
            selected.append("code_analysis")
        
        if any(kw in task_lower for kw in ["概念", "理论", "原理", "解释", "是什么", "为什么"]):
            selected.append("concept_explanation")
        
        if any(kw in task_lower for kw in ["示例", "例子", "案例", "应用"]):
            selected.append("example_generation")
        
        if any(kw in task_lower for kw in ["习题", "题目", "练习", "解题"]):
            selected.append("exercise")
        
        if any(kw in task_lower for kw in ["matlab", "python", "科学计算", "数值计算"]):
            selected.append("scientific_coding")
        
        # 如果问题比较复杂，添加总结Agent
        if len(selected) > 2:
            selected.append("summary")
        
        # 如果什么都没选中，至少选择概念解释
        if not selected:
            selected = ["concept_explanation"]
        
        return selected
    
    def parse_planning_result(self, planning_text: str) -> List[Dict[str, Any]]:
        """
        解析规划结果，提取需要调用的专家Agent列表
        
        Args:
            planning_text: LLM返回的规划文本
        
        Returns:
            专家Agent任务列表
        """
        import json
        import re
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', planning_text)
            if json_match:
                json_str = json_match.group(0)
                parsed = json.loads(json_str)
                selected_agents = parsed.get("selected_agents", [])
                agent_tasks = parsed.get("agent_tasks", {})
                
                return [
                    {
                        "type": agent_type,
                        "task": agent_tasks.get(agent_type, f"{agent_type}的任务"),
                        "priority": i + 1
                    }
                    for i, agent_type in enumerate(selected_agents)
                ]
        except Exception as e:
            logger.warning(f"解析规划结果失败: {e}")
        
        # 后备方案
        return [
            {"type": "concept_explanation", "task": "解释核心概念", "priority": 1},
        ]


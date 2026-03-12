"""Agent工作流编排 - 使用LangChain编排并行工作流"""
from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
import time
from utils.logger import logger

from agents.coordinator.coordinator_agent import CoordinatorAgent
from agents.experts.document_retrieval_agent import DocumentRetrievalAgent
from agents.experts.formula_analysis_agent import FormulaAnalysisAgent
from agents.experts.code_analysis_agent import CodeAnalysisAgent
from agents.experts.concept_explanation_agent import ConceptExplanationAgent
from agents.experts.example_generation_agent import ExampleGenerationAgent
from agents.experts.summary_agent import SummaryAgent
from agents.experts.exercise_agent import ExerciseAgent
from agents.experts.scientific_coding_agent import ScientificCodingAgent


async def get_agent_config(agent_type: str) -> Dict[str, Optional[str]]:
    """
    从数据库获取Agent的模型配置
    
    Args:
        agent_type: Agent类型
        
    Returns:
        包含 inference_model 和 embedding_model 的字典
    """
    try:
        from database.mongodb import mongodb
        collection = mongodb.get_collection("agent_configs")
        doc = await collection.find_one({"agent_type": agent_type})
        
        if doc:
            return {
                "inference_model": doc.get("inference_model"),
                "embedding_model": doc.get("embedding_model")
            }
    except Exception as e:
        logger.warning(f"获取Agent配置失败 ({agent_type}): {str(e)}，使用默认配置")
    
    return {
        "inference_model": None,
        "embedding_model": None
    }


class AgentWorkflow:
    """Agent工作流编排器 - 管理多Agent协作"""
    
    # Agent类型映射
    AGENT_MAP = {
        "document_retrieval": DocumentRetrievalAgent,
        "formula_analysis": FormulaAnalysisAgent,
        "code_analysis": CodeAnalysisAgent,
        "concept_explanation": ConceptExplanationAgent,
        "example_generation": ExampleGenerationAgent,
        "summary": SummaryAgent,
        "exercise": ExerciseAgent,
        "scientific_coding": ScientificCodingAgent,
    }
    
    def __init__(self):
        """初始化工作流编排器"""
        # Coordinator将在execute_workflow中初始化（需要异步加载配置）
        self.coordinator = None
        self.expert_agents = {}  # 专家Agent实例缓存
        self._agent_configs_cache = {}  # Agent配置缓存
    
    async def _init_coordinator(self, generation_config: Optional[Dict[str, Any]] = None):
        """初始化协调型Agent（异步加载配置）"""
        if self.coordinator is None:
            model_name = None
            if generation_config:
                model_name = generation_config.get("llm_model")
            
            if not model_name:
                config = await get_agent_config("coordinator")
                model_name = config.get("inference_model")
            
            self.coordinator = CoordinatorAgent(model_name=model_name)
    
    async def _get_expert_agent(self, agent_type: str, generation_config: Optional[Dict[str, Any]] = None):
        """获取专家Agent实例（延迟初始化，异步加载配置）"""
        if agent_type not in self.expert_agents:
            agent_class = self.AGENT_MAP.get(agent_type)
            if agent_class:
                model_name = None
                if generation_config:
                    # 可以在这里处理特定Agent的模型配置，目前统一使用llm_model
                    model_name = generation_config.get("llm_model")
                
                if not model_name:
                    # 从数据库加载配置
                    if agent_type not in self._agent_configs_cache:
                        self._agent_configs_cache[agent_type] = await get_agent_config(agent_type)
                    
                    config = self._agent_configs_cache[agent_type]
                    model_name = config.get("inference_model")
                
                self.expert_agents[agent_type] = agent_class(model_name=model_name)
            else:
                logger.warning(f"未知的Agent类型: {agent_type}")
                return None
        return self.expert_agents.get(agent_type)
    
    async def execute_workflow(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        enabled_agents: Optional[List[str]] = None,
        stream: bool = False
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        执行多Agent协作工作流
        
        Args:
            query: 用户问题
            context: 上下文信息
            enabled_agents: 启用的专家Agent列表（如果为None则使用所有Agent）
            stream: 是否流式输出
        
        Yields:
            包含Agent结果和状态的字典
        """
        try:
            # 0. 初始化协调型Agent（异步加载配置）
            generation_config = context.get("generation_config") if context else None
            await self._init_coordinator(generation_config)
            
            # 1. 协调Agent规划任务
            logger.info(f"AgentWorkflow: 开始规划任务 - {query[:50]}...")
            
            planning_context = context or {}
            planning_context["query"] = query
            
            selected_agents_from_coordinator = None
            agent_tasks = {}
            planning_reasoning = ""
            
            async for planning_result in self.coordinator.execute(
                task=query,
                context=planning_context,
                stream=False
            ):
                if planning_result.get("type") == "planning":
                    # 获取协调型Agent选择的Agent列表
                    selected_agents_from_coordinator = planning_result.get("selected_agents")
                    agent_tasks = planning_result.get("agent_tasks", {})
                    planning_reasoning = planning_result.get("reasoning", "")
                    
                    yield {
                        "type": "planning",
                        "content": planning_result.get("content", ""),
                        "agent_type": "coordinator",
                        "selected_agents": selected_agents_from_coordinator,
                        "agent_tasks": agent_tasks,
                        "reasoning": planning_reasoning
                    }
                    
                    # 发送所有Agent的初始状态（包括未被选中的）
                    if stream and selected_agents_from_coordinator:
                        all_agent_types = list(self.AGENT_MAP.keys())
                        for agent_type in all_agent_types:
                            if agent_type in selected_agents_from_coordinator:
                                # 被选中的Agent，状态为pending（等待执行）
                                yield {
                                    "type": "agent_status",
                                    "agent_type": agent_type,
                                    "status": "pending",
                                    "reason": "等待执行"
                                }
                            else:
                                # 未被选中的Agent，状态为skipped
                                yield {
                                    "type": "agent_status",
                                    "agent_type": agent_type,
                                    "status": "skipped",
                                    "reason": planning_reasoning or "协调型Agent未选择此Agent"
                                }
            
            # 2. 确定要执行的专家Agent
            if enabled_agents:
                # 如果手动指定了Agent，使用指定的
                agent_types = enabled_agents
                logger.info(f"AgentWorkflow: 使用手动指定的Agent列表: {agent_types}")
            elif selected_agents_from_coordinator:
                # 使用协调型Agent选择的Agent列表
                agent_types = selected_agents_from_coordinator
                logger.info(f"AgentWorkflow: 协调型Agent选择了 {len(agent_types)} 个Agent: {agent_types}")
                logger.info(f"AgentWorkflow: 选择理由: {planning_reasoning}")
            else:
                # 后备方案：使用所有Agent
                agent_types = list(self.AGENT_MAP.keys())
                logger.warning(f"AgentWorkflow: 协调型Agent未返回选择结果，使用所有Agent: {agent_types}")
            
            # 验证Agent类型有效性
            valid_agent_types = set(self.AGENT_MAP.keys())
            agent_types = [a for a in agent_types if a in valid_agent_types]
            
            if not agent_types:
                logger.warning("AgentWorkflow: 没有有效的Agent类型，使用默认Agent")
                agent_types = ["concept_explanation"]
            
            logger.info(f"AgentWorkflow: 将执行 {len(agent_types)} 个专家Agent: {agent_types}")
            
            # 3. 顺序执行专家Agent（以便前端可以实时显示进度）
            expert_context = context or {}
            expert_context["query"] = query
            # 将Agent任务描述添加到上下文中
            if agent_tasks:
                expert_context["agent_tasks"] = agent_tasks
            
            agent_results = []
            
            # 注意：Agent的初始状态已经在planning事件中发送了
            # 这里只需要确保第一个Agent开始执行
            
            # 顺序执行每个被选中的Agent
            for agent_type in agent_types:
                # 发送Agent开始执行的状态
                if stream:
                    yield {
                        "type": "agent_status",
                        "agent_type": agent_type,
                        "status": "running",
                        "current_step": "开始工作...",
                        "progress": 0,
                        "started_at": int(time.time() * 1000)
                    }
                
                try:
                    # 获取Agent实例
                    agent = await self._get_expert_agent(agent_type, generation_config)
                    if not agent:
                        logger.warning(f"AgentWorkflow: {agent_type} 未找到，跳过")
                        if stream:
                            yield {
                                "type": "agent_status",
                                "agent_type": agent_type,
                                "status": "error",
                                "details": "Agent未找到"
                            }
                        continue
                    
                    # 执行Agent任务
                    result_content = ""
                    sources = []
                    confidence = 0.5
                    progress = 0
                    
                    async for result in agent.execute(task=query, context=expert_context, stream=stream):
                        if result.get("type") == "complete":
                            result_content = result.get("content", "")
                            sources = result.get("sources", [])
                            confidence = result.get("confidence", 0.5)
                            progress = 100
                            
                            # 发送完成状态
                            if stream:
                                yield {
                                    "type": "agent_status",
                                    "agent_type": agent_type,
                                    "status": "completed",
                                    "progress": 100,
                                    "completed_at": int(time.time() * 1000)
                                }
                                
                                yield {
                                    "type": "agent_result",
                                    "agent_type": agent_type,
                                    "content": result_content,
                                    "sources": sources,
                                    "confidence": confidence
                                }
                        elif result.get("type") == "chunk" and stream:
                            result_content += result.get("content", "")
                            # 更新进度（简单估算）
                            progress = min(progress + 2, 95)
                            yield {
                                "type": "agent_status",
                                "agent_type": agent_type,
                                "status": "running",
                                "current_step": result.get("current_step", "正在生成内容..."),
                                "progress": progress
                            }
                        elif result.get("type") == "status" and stream:
                            # Agent发送的状态更新
                            yield {
                                "type": "agent_status",
                                "agent_type": agent_type,
                                "status": result.get("status", "running"),
                                "current_step": result.get("current_step"),
                                "progress": result.get("progress", progress),
                                "details": result.get("details")
                            }
                    
                    # 保存结果
                    agent_results.append({
                        "agent_type": agent_type,
                        "content": result_content,
                        "sources": sources,
                        "confidence": confidence,
                        "error": False
                    })
                    
                except Exception as e:
                    logger.error(f"AgentWorkflow: {agent_type} 执行失败: {e}", exc_info=True)
                    error_msg = f"执行失败: {str(e)}"
                    agent_results.append({
                        "agent_type": agent_type,
                        "content": error_msg,
                        "error": True
                    })
                    # 发送错误状态
                    if stream:
                        yield {
                            "type": "agent_status",
                            "agent_type": agent_type,
                            "status": "error",
                            "details": error_msg
                        }
            
            # 5. 返回所有结果
            yield {
                "type": "complete",
                "agent_results": agent_results,
                "total_agents": len(agent_types),
                "successful_agents": len([r for r in agent_results if not r.get("error")])
            }
        
        except Exception as e:
            logger.error(f"AgentWorkflow: 工作流执行失败: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"工作流执行失败: {str(e)}"
            }
    
    async def _execute_expert_agent(
        self,
        agent,
        agent_type: str,
        task: str,
        context: Dict[str, Any],
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        执行单个专家Agent任务
        
        Args:
            agent: Agent实例
            agent_type: Agent类型
            task: 任务描述
            context: 上下文信息
            stream: 是否流式输出
        
        Returns:
            Agent执行结果
        """
        try:
            result_content = ""
            sources = []
            confidence = 0.5
            
            async for result in agent.execute(task=task, context=context, stream=stream):
                if result.get("type") == "complete":
                    result_content = result.get("content", "")
                    sources = result.get("sources", [])
                    confidence = result.get("confidence", 0.5)
                elif result.get("type") == "chunk" and stream:
                    result_content += result.get("content", "")
            
            return {
                "agent_type": agent_type,
                "content": result_content,
                "sources": sources,
                "confidence": confidence,
                "error": False
            }
        
        except Exception as e:
            logger.error(f"执行 {agent_type} Agent失败: {e}", exc_info=True)
            return {
                "agent_type": agent_type,
                "content": f"执行失败: {str(e)}",
                "error": True
            }


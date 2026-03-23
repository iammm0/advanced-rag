"""多智能体与深度研究：Agent 配置（MongoDB agent_configs）"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from database.mongodb import mongodb
from utils.logger import logger


AGENT_LABELS: Dict[str, str] = {
    "coordinator": "协调 Agent",
    "document_retrieval": "文档检索",
    "formula_analysis": "公式分析",
    "code_analysis": "代码分析",
    "concept_explanation": "概念解释",
    "example_generation": "示例生成",
    "summary": "总结归纳",
    "exercise": "习题生成",
    "scientific_coding": "科学计算",
}

# coordinator 不可禁用（深度研究入口）
AGENT_LOCK_ENABLE: frozenset = frozenset({"coordinator"})


def builtin_prompt_for_type(agent_type: str) -> str:
    """供 API 返回默认提示词（代码内置，未覆盖 DB 时使用）。"""
    if agent_type == "coordinator":
        from agents.coordinator.coordinator_agent import CoordinatorAgent

        return CoordinatorAgent().get_prompt()
    from agents.workflow.agent_workflow import AgentWorkflow

    cls = AgentWorkflow.AGENT_MAP.get(agent_type)
    if cls:
        return cls().get_prompt()
    return ""


async def get_agent_config_from_db(agent_type: str) -> Dict[str, Any]:
    """供工作流读取：模型、提示覆盖、是否启用。"""
    try:
        collection = mongodb.get_collection("agent_configs")
        doc = await collection.find_one({"agent_type": agent_type})
        if doc:
            return {
                "inference_model": doc.get("inference_model"),
                "embedding_model": doc.get("embedding_model"),
                "system_prompt": doc.get("system_prompt"),
                "enabled": doc.get("enabled", True),
            }
    except Exception as e:
        logger.warning(f"读取 Agent 配置失败 ({agent_type}): {e}")
    return {
        "inference_model": None,
        "embedding_model": None,
        "system_prompt": None,
        "enabled": True,
    }


async def list_enabled_expert_types() -> List[str]:
    """深度研究中可被协调器调度、且未禁用的专家类型。"""
    from agents.workflow.agent_workflow import AgentWorkflow

    enabled: List[str] = []
    for agent_type in AgentWorkflow.AGENT_MAP.keys():
        cfg = await get_agent_config_from_db(agent_type)
        if cfg.get("enabled", True):
            enabled.append(agent_type)
    return enabled


async def list_agent_configs_for_api() -> List[Dict[str, Any]]:
    """管理端：列出全部 Agent 及合并后的展示字段。"""
    from agents.workflow.agent_workflow import AgentWorkflow

    rows: List[Dict[str, Any]] = []

    db_c = await get_agent_config_from_db("coordinator")
    rows.append(
        {
            "agent_type": "coordinator",
            "label": AGENT_LABELS.get("coordinator", "coordinator"),
            "role": "coordinator",
            "inference_model": db_c.get("inference_model"),
            "embedding_model": db_c.get("embedding_model"),
            "system_prompt": db_c.get("system_prompt"),
            "builtin_system_prompt": builtin_prompt_for_type("coordinator"),
            "enabled": True,
            "enable_locked": True,
        }
    )

    for agent_type in AgentWorkflow.AGENT_MAP.keys():
        db = await get_agent_config_from_db(agent_type)
        rows.append(
            {
                "agent_type": agent_type,
                "label": AGENT_LABELS.get(agent_type, agent_type),
                "role": "expert",
                "inference_model": db.get("inference_model"),
                "embedding_model": db.get("embedding_model"),
                "system_prompt": db.get("system_prompt"),
                "builtin_system_prompt": builtin_prompt_for_type(agent_type),
                "enabled": db.get("enabled", True),
                "enable_locked": False,
            }
        )

    return rows


async def upsert_agent_config(
    agent_type: str,
    inference_model: Optional[str] = None,
    embedding_model: Optional[str] = None,
    system_prompt: Optional[str] = None,
    enabled: Optional[bool] = None,
    clear_system_prompt: bool = False,
) -> Dict[str, Any]:
    """写入或更新单条配置。"""
    from agents.workflow.agent_workflow import AgentWorkflow

    if agent_type == "coordinator":
        pass
    elif agent_type not in AgentWorkflow.AGENT_MAP:
        raise ValueError(f"未知的 agent_type: {agent_type}")

    collection = mongodb.get_collection("agent_configs")
    raw = await collection.find_one({"agent_type": agent_type}) or {}

    out: Dict[str, Any] = {
        "agent_type": agent_type,
        "inference_model": raw.get("inference_model"),
        "embedding_model": raw.get("embedding_model"),
        "system_prompt": raw.get("system_prompt"),
        "enabled": raw.get("enabled", True),
    }

    if inference_model is not None:
        out["inference_model"] = inference_model
    if embedding_model is not None:
        out["embedding_model"] = embedding_model
    if clear_system_prompt:
        out["system_prompt"] = None
    elif system_prompt is not None:
        out["system_prompt"] = system_prompt

    if agent_type in AGENT_LOCK_ENABLE:
        out["enabled"] = True
    elif enabled is not None:
        out["enabled"] = enabled

    await collection.update_one({"agent_type": agent_type}, {"$set": out}, upsert=True)
    return await get_agent_config_from_db(agent_type)

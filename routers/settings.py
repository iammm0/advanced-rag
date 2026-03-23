"""运行时配置路由（快捷模式 + 高级开关）"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database.mongodb import require_mongodb
from services.runtime_config import RuntimeConfig, RuntimeMode, get_runtime_config, upsert_runtime_config
from services import agent_settings as agent_settings_service
from utils.logger import logger


router = APIRouter()


class RuntimeConfigResponse(BaseModel):
    mode: RuntimeMode
    modules: Dict[str, bool] = Field(default_factory=dict)
    params: Dict[str, Any] = Field(default_factory=dict)
    updated_at: Optional[str] = None


class RuntimeConfigUpdateRequest(BaseModel):
    mode: Optional[RuntimeMode] = None
    modules: Optional[Dict[str, bool]] = None
    params: Optional[Dict[str, Any]] = None


class AgentConfigItemResponse(BaseModel):
    agent_type: str
    label: str
    role: str
    inference_model: Optional[str] = None
    embedding_model: Optional[str] = None
    system_prompt: Optional[str] = None
    builtin_system_prompt: str = ""
    enabled: bool = True
    enable_locked: bool = False


class AgentConfigsListResponse(BaseModel):
    agents: List[AgentConfigItemResponse]


class AgentConfigUpdateRequest(BaseModel):
    inference_model: Optional[str] = None
    embedding_model: Optional[str] = None
    system_prompt: Optional[str] = None
    enabled: Optional[bool] = None
    clear_system_prompt: bool = False


@router.get("/runtime", response_model=RuntimeConfigResponse)
async def get_runtime_settings(_: None = Depends(require_mongodb)):
    cfg = await get_runtime_config()
    return RuntimeConfigResponse(
        mode=cfg.get("mode", "custom"),
        modules=dict(cfg.get("modules") or {}),
        params=dict(cfg.get("params") or {}),
        updated_at=cfg.get("updated_at"),
    )


@router.put("/runtime", response_model=RuntimeConfigResponse)
async def update_runtime_settings(request: RuntimeConfigUpdateRequest, _: None = Depends(require_mongodb)):
    try:
        patch: RuntimeConfig = {}
        if request.mode:
            patch["mode"] = request.mode
        if request.modules is not None:
            patch["modules"] = request.modules
        if request.params is not None:
            patch["params"] = request.params

        cfg = await upsert_runtime_config(patch)
        logger.info(f"运行时配置已更新: mode={cfg.get('mode')}")
        return RuntimeConfigResponse(
            mode=cfg.get("mode", "custom"),
            modules=dict(cfg.get("modules") or {}),
            params=dict(cfg.get("params") or {}),
            updated_at=cfg.get("updated_at"),
        )
    except Exception as e:
        logger.error(f"更新运行时配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新失败: {str(e)}")


@router.get("/agents", response_model=AgentConfigsListResponse)
async def list_agent_configs(_: None = Depends(require_mongodb)):
    """深度研究多智能体：列出全部协调器与专家配置（含内置提示词预览）。"""
    rows = await agent_settings_service.list_agent_configs_for_api()
    return AgentConfigsListResponse(
        agents=[AgentConfigItemResponse(**r) for r in rows]
    )


@router.put("/agents/{agent_type}", response_model=AgentConfigItemResponse)
async def update_agent_config(
    agent_type: str,
    request: AgentConfigUpdateRequest,
    _: None = Depends(require_mongodb),
):
    """更新单个 Agent 的模型、系统提示词与启用状态。"""
    try:
        await agent_settings_service.upsert_agent_config(
            agent_type=agent_type,
            inference_model=request.inference_model,
            embedding_model=request.embedding_model,
            system_prompt=request.system_prompt,
            enabled=request.enabled,
            clear_system_prompt=request.clear_system_prompt,
        )
        rows = await agent_settings_service.list_agent_configs_for_api()
        for r in rows:
            if r["agent_type"] == agent_type:
                return AgentConfigItemResponse(**r)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="未找到该 Agent")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"更新 Agent 配置失败: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"更新失败: {str(e)}")


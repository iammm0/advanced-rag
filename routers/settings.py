"""运行时配置路由（快捷模式 + 高级开关）"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from database.mongodb import require_mongodb
from services.runtime_config import RuntimeConfig, RuntimeMode, get_runtime_config, upsert_runtime_config
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


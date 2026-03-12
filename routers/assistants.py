"""助手信息路由（纯RAG系统：仅提供读取能力）"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from database.mongodb import mongodb
from utils.logger import logger


router = APIRouter()


class AssistantResponse(BaseModel):
    """助手响应模型（前端只读使用）"""

    id: str
    name: str
    description: Optional[str] = None
    system_prompt: str
    collection_name: str
    is_default: bool
    greeting_message: Optional[str] = None
    quick_prompts: Optional[list[str]] = None
    inference_model: Optional[str] = None
    embedding_model: Optional[str] = None
    icon_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class AssistantListResponse(BaseModel):
    assistants: List[AssistantResponse]
    total: int


@router.get("", response_model=AssistantListResponse)
async def list_assistants(skip: int = 0, limit: int = 100):
    """获取助手列表（匿名模式，只读）"""
    logger.info(f"获取助手列表请求 - skip: {skip}, limit: {limit}")
    try:
        collection = mongodb.get_collection("course_assistants")
        total = await collection.count_documents({})
        cursor = collection.find({}).sort("created_at", -1).skip(skip).limit(limit)

        assistants: List[AssistantResponse] = []
        async for doc in cursor:
            assistants.append(
                AssistantResponse(
                    id=str(doc.get("_id")),
                    name=doc.get("name", ""),
                    description=doc.get("description"),
                    system_prompt=doc.get("system_prompt", ""),
                    collection_name=doc.get("collection_name", ""),
                    is_default=doc.get("is_default", False),
                    greeting_message=doc.get("greeting_message"),
                    quick_prompts=doc.get("quick_prompts"),
                    inference_model=doc.get("inference_model"),
                    embedding_model=doc.get("embedding_model"),
                    icon_url=doc.get("icon_url"),
                    created_at=doc.get("created_at").isoformat()
                    if isinstance(doc.get("created_at"), datetime)
                    else (str(doc.get("created_at")) if doc.get("created_at") else None),
                    updated_at=doc.get("updated_at").isoformat()
                    if isinstance(doc.get("updated_at"), datetime)
                    else (str(doc.get("updated_at")) if doc.get("updated_at") else None),
                )
            )

        return AssistantListResponse(assistants=assistants, total=total)
    except Exception as e:
        logger.error(f"获取助手列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取助手列表失败: {str(e)}",
        )


@router.get("/{assistant_id}", response_model=AssistantResponse)
async def get_assistant(assistant_id: str):
    """获取助手详情（匿名模式，只读）"""
    logger.info(f"获取助手详情请求 - assistant_id: {assistant_id}")
    try:
        collection = mongodb.get_collection("course_assistants")
        doc = await collection.find_one({"_id": assistant_id})
        if not doc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="助手不存在")

        return AssistantResponse(
            id=str(doc.get("_id")),
            name=doc.get("name", ""),
            description=doc.get("description"),
            system_prompt=doc.get("system_prompt", ""),
            collection_name=doc.get("collection_name", ""),
            is_default=doc.get("is_default", False),
            greeting_message=doc.get("greeting_message"),
            quick_prompts=doc.get("quick_prompts"),
            inference_model=doc.get("inference_model"),
            embedding_model=doc.get("embedding_model"),
            icon_url=doc.get("icon_url"),
            created_at=doc.get("created_at").isoformat()
            if isinstance(doc.get("created_at"), datetime)
            else (str(doc.get("created_at")) if doc.get("created_at") else None),
            updated_at=doc.get("updated_at").isoformat()
            if isinstance(doc.get("updated_at"), datetime)
            else (str(doc.get("updated_at")) if doc.get("updated_at") else None),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取助手详情失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取助手详情失败: {str(e)}",
        )


"""知识空间（Knowledge Space）路由

说明：
- 物理“助手”仅保留一个默认对话助手（GeneralAssistantAgent）
- 原“助手列表/助手选择”在产品层面改为“知识空间选择”
- 每个知识空间对应一个独立的向量集合（Qdrant collection_name）
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field

from database.mongodb import mongodb, require_mongodb
from utils.logger import logger


router = APIRouter()


class KnowledgeSpaceResponse(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    collection_name: str
    is_default: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class KnowledgeSpaceListResponse(BaseModel):
    knowledge_spaces: List[KnowledgeSpaceResponse]
    total: int


class KnowledgeSpaceCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    description: Optional[str] = Field(default=None, max_length=200)


def _to_iso(dt) -> Optional[str]:
    if isinstance(dt, datetime):
        return dt.isoformat()
    return str(dt) if dt else None


@router.get("", response_model=KnowledgeSpaceListResponse)
async def list_knowledge_spaces(
    skip: int = 0,
    limit: int = 100,
    _: None = Depends(require_mongodb),
):
    logger.info(f"获取知识空间列表请求 - skip: {skip}, limit: {limit}")
    try:
        collection = mongodb.get_collection("knowledge_spaces")
        total = await collection.count_documents({})
        cursor = collection.find({}).sort("created_at", -1).skip(skip).limit(limit)

        items: List[KnowledgeSpaceResponse] = []
        async for doc in cursor:
            items.append(
                KnowledgeSpaceResponse(
                    id=str(doc.get("_id")),
                    name=doc.get("name", ""),
                    description=doc.get("description"),
                    collection_name=doc.get("collection_name", "default_knowledge"),
                    is_default=bool(doc.get("is_default", False)),
                    created_at=_to_iso(doc.get("created_at")),
                    updated_at=_to_iso(doc.get("updated_at")),
                )
            )

        return KnowledgeSpaceListResponse(knowledge_spaces=items, total=total)
    except Exception as e:
        logger.error(f"获取知识空间列表失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取知识空间列表失败: {str(e)}",
        )


@router.post("", response_model=KnowledgeSpaceResponse, status_code=status.HTTP_201_CREATED)
async def create_knowledge_space(
    request: KnowledgeSpaceCreateRequest,
    _: None = Depends(require_mongodb),
):
    logger.info(f"创建知识空间请求 - name: {request.name}")
    try:
        collection = mongodb.get_collection("knowledge_spaces")

        # 名称去重：避免使用 $regex（在某些编码/输入场景下可能产生无效正则）
        name = request.name.strip()
        name_key = name.casefold()
        exists = await collection.find_one({"name_key": name_key})
        if exists:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="知识空间名称已存在")

        # 生成 collection_name：确保稳定、可读且不含空格
        import re
        import uuid
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "_", request.name.strip()).strip("_").lower()
        suffix = uuid.uuid4().hex[:8]
        collection_name = f"kb_{slug}_{suffix}" if slug else f"kb_{suffix}"

        from utils.timezone import beijing_now

        now = beijing_now()
        doc = {
            "name": name,
            "name_key": name_key,
            "description": request.description.strip() if request.description else None,
            "collection_name": collection_name,
            "is_default": False,
            "created_at": now,
            "updated_at": now,
        }
        result = await collection.insert_one(doc)

        return KnowledgeSpaceResponse(
            id=str(result.inserted_id),
            name=doc["name"],
            description=doc.get("description"),
            collection_name=doc["collection_name"],
            is_default=False,
            created_at=_to_iso(doc.get("created_at")),
            updated_at=_to_iso(doc.get("updated_at")),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"创建知识空间失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建知识空间失败: {str(e)}",
        )


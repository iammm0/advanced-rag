"""课程助手模型"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional
import re


class CourseAssistant(BaseModel):
    """课程助手模型（公开信息）"""
    id: Optional[str] = None
    name: str  # 助手名称
    description: Optional[str] = None  # 助手描述
    system_prompt: str  # 系统提示词
    collection_name: str  # Qdrant集合名称
    is_default: bool = False  # 是否为默认助手
    greeting_message: Optional[str] = None  # 初始问候语
    quick_prompts: Optional[list[str]] = None  # 快捷提示词列表
    inference_model: Optional[str] = None  # 推理模型名称（用于生成回复）
    embedding_model: Optional[str] = None  # 向量化模型名称（用于文档向量化）
    icon_url: Optional[str] = None  # 助手图标URL
    created_at: datetime
    updated_at: datetime
    
    @classmethod
    def validate_name(cls, v: str) -> str:
        """验证助手名称"""
        if not v or not v.strip():
            raise ValueError('助手名称不能为空')
        if len(v.strip()) > 100:
            raise ValueError('助手名称不能超过100个字符')
        return v.strip()
    
    @classmethod
    def validate_collection_name(cls, v: str) -> str:
        """验证集合名称（Qdrant集合名称规范）"""
        if not v or not v.strip():
            raise ValueError('集合名称不能为空')
        # Qdrant集合名称只能包含字母、数字、下划线和连字符
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('集合名称只能包含字母、数字、下划线和连字符')
        if len(v) > 63:
            raise ValueError('集合名称不能超过63个字符')
        return v.strip()


class CourseAssistantInDB(CourseAssistant):
    """课程助手模型（数据库存储）"""
    pass


class CourseAssistantCreate(BaseModel):
    """创建助手请求模型"""
    name: str
    description: Optional[str] = None
    system_prompt: str
    collection_name: Optional[str] = None  # 如果不提供，自动生成
    is_default: Optional[bool] = False
    greeting_message: Optional[str] = None  # 初始问候语
    quick_prompts: Optional[list[str]] = None  # 快捷提示词列表
    inference_model: Optional[str] = None  # 推理模型名称（用于生成回复）
    embedding_model: Optional[str] = None  # 向量化模型名称（用于文档向量化）
    icon_url: Optional[str] = None  # 助手图标URL


class CourseAssistantUpdate(BaseModel):
    """更新助手请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    is_default: Optional[bool] = None
    greeting_message: Optional[str] = None  # 初始问候语
    quick_prompts: Optional[list[str]] = None  # 快捷提示词列表
    inference_model: Optional[str] = None  # 推理模型名称（用于生成回复）
    embedding_model: Optional[str] = None  # 向量化模型名称（用于文档向量化）
    icon_url: Optional[str] = None  # 助手图标URL


"""资源模型"""
from pydantic import BaseModel, field_validator
from typing import Optional, Literal, List
from datetime import datetime
import re


class Resource(BaseModel):
    """资源模型"""
    id: Optional[str] = None
    title: str
    description: str
    file_path: Optional[str] = None  # 文件路径（可选，外部链接资源可能没有）
    file_type: str
    file_size: int
    url: Optional[str] = None  # 外部链接（可选，如B站视频链接）
    thumbnail_url: Optional[str] = None  # 视频封面URL（可选，主要用于视频资源）
    cover_image: Optional[str] = None  # 资源封面图片路径（可选，管理员上传的封面）
    assistant_id: Optional[str] = None
    uploader_id: Optional[str] = None  # 上传者ID
    status: Literal["active", "down", "deleted"] = "active"  # 资源状态：active（正常）、down（下架）、deleted（已删除）
    is_public: bool = True  # 是否公开（所有用户可见）
    tags: List[str] = []  # 标签列表
    schema_version: int = 2  # 资源模型版本（用于兼容性迁移）
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ResourceCreate(BaseModel):
    """创建资源请求模型"""
    title: str
    description: str
    file_path: Optional[str] = None
    file_type: str
    file_size: int
    url: Optional[str] = None
    assistant_id: Optional[str] = None
    uploader_id: Optional[str] = None
    is_public: bool = True
    tags: List[str] = []

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: Optional[str]) -> Optional[str]:
        """验证URL格式"""
        if v is None or v == "":
            return None
        # 基本的URL格式验证
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        if not url_pattern.match(v):
            raise ValueError('无效的URL格式')
        return v


def validate_url(url: Optional[str]) -> Optional[str]:
    """验证URL格式的独立函数"""
    if url is None or url == "":
        return None
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    if not url_pattern.match(url):
        raise ValueError('无效的URL格式')
    return url


class ResourceUpdate(BaseModel):
    """更新资源请求模型"""
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[Literal["active", "down", "deleted"]] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    cover_image: Optional[str] = None  # 封面图片路径（更新时可选）


class ResourceTagUpdate(BaseModel):
    """资源标签更新请求模型"""
    tags: List[str]

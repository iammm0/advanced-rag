"""用户公开资料访问记录模型"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ProfileVisit(BaseModel):
    """用户公开资料访问记录"""
    visitor_id: str  # 访问者ID
    visited_user_id: str  # 被访问用户ID
    visited_at: datetime  # 访问时间
    ip_address: Optional[str] = None  # 访问IP（可选）


class ProfileVisitResponse(BaseModel):
    """访问记录响应模型"""
    visitor_id: str
    visitor_username: str
    visitor_full_name: Optional[str] = None
    visitor_avatar_url: Optional[str] = None
    visitor_user_type: Optional[str] = None
    visited_at: str
    ip_address: Optional[str] = None


class ProfileVisitorsResponse(BaseModel):
    """访问记录列表响应模型"""
    visitors: list[ProfileVisitResponse]
    total: int
    page: int
    page_size: int

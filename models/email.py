"""邮件模型"""
from pydantic import BaseModel, field_validator
from typing import List, Optional, Dict, Any, Literal
from datetime import datetime


class EmailAttachment(BaseModel):
    """邮件附件模型"""
    filename: str
    file_path: str
    file_size: int
    content_type: str


class EmailCreate(BaseModel):
    """创建邮件请求模型"""
    to_user_ids: Optional[List[str]] = None  # 点对点发送的收件人ID列表
    to_user_type: Optional[Literal["all", "students", "teachers"]] = None  # 批量发送的用户类型
    to_class_names: Optional[List[str]] = None  # 特定班级（普通管理员）
    to_grades: Optional[List[str]] = None  # 特定年级（普通管理员）
    subject: str
    content: str
    markdown_content: Optional[str] = None
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    is_relationship_required: bool = True  # 是否需要建立关系（用户间发送时）
    
    @field_validator("to_user_ids", "to_user_type")
    def validate_recipients(cls, v, info):
        """验证收件人设置：要么指定用户ID列表，要么指定用户类型"""
        data = info.data
        if not v and not data.get("to_user_ids") and not data.get("to_user_type"):
            raise ValueError("必须指定收件人（to_user_ids 或 to_user_type）")
        return v


class EmailDraftCreate(BaseModel):
    """创建草稿请求模型"""
    to_user_ids: Optional[List[str]] = None
    to_user_type: Optional[Literal["all", "students", "teachers"]] = None
    to_class_names: Optional[List[str]] = None
    to_grades: Optional[List[str]] = None
    subject: str = ""
    content: str = ""
    markdown_content: Optional[str] = None
    priority: Literal["low", "normal", "high", "urgent"] = "normal"


class EmailResponse(BaseModel):
    """邮件响应模型"""
    id: str
    from_user_id: str
    from_username: str
    to_user_ids: List[str]
    to_user_type: Optional[str] = None
    to_class_names: Optional[List[str]] = None
    to_grades: Optional[List[str]] = None
    subject: str
    content: str
    markdown_content: Optional[str] = None
    attachments: List[EmailAttachment] = []
    priority: str
    status: Literal["draft", "sent", "deleted"]
    is_relationship_required: bool
    relationship_invitation_id: Optional[str] = None  # 关联的关系邀请ID（如果是关系邀请邮件）
    created_at: str
    sent_at: Optional[str] = None
    updated_at: str


class EmailListItem(BaseModel):
    """邮件列表项模型"""
    id: str
    from_user_id: str
    from_username: str
    subject: str
    content_preview: str  # 内容预览（前100字符）
    content: Optional[str] = None  # 完整内容（用于对话窗口）
    priority: str
    is_read: bool
    created_at: str
    sent_at: Optional[str] = None
    folder: Literal["inbox", "sent", "draft", "trash"]


class EmailListResponse(BaseModel):
    """邮件列表响应模型"""
    emails: List[EmailListItem]
    total: int
    unread_count: int
    page: int = 1
    page_size: int = 20


class BatchEmailCreate(BaseModel):
    """批量发送邮件请求模型（管理员）"""
    to_user_type: Literal["all", "students", "teachers"]
    to_class_names: Optional[List[str]] = None
    to_grades: Optional[List[str]] = None
    subject: str
    content: str
    markdown_content: Optional[str] = None
    priority: Literal["low", "normal", "high", "urgent"] = "normal"


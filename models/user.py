"""用户模型"""
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, Literal, List, Dict, Any
import re


class User(BaseModel):
    """用户模型（公开信息）"""
    id: Optional[str] = None
    username: str
    email: str  # 使用 str 类型，通过自定义验证器验证
    full_name: Optional[str] = None
    user_type: Literal["student", "teacher", "other"] = "student"  # 用户身份：student（学生）、teacher（教师）、other（其他）
    student_id: Optional[str] = None  # 学号（仅学生身份需要）
    class_name: Optional[str] = None  # 班级（仅学生身份需要）
    grade: Optional[str] = None  # 第几届（仅学生身份需要）
    is_online: bool = False  # 在线状态
    last_seen: Optional[datetime] = None  # 最后在线时间
    created_at: datetime
    is_active: bool = True
    role: Literal["admin", "teacher", "user", "developer"] = "user"  # 用户角色：admin（系统管理员）、teacher（普通管理员/授课老师）、user（普通用户）、developer（开发者）
    max_assistants: Optional[int] = None  # 最大助手数（仅普通管理员）
    max_documents: Optional[int] = None  # 最大文档数（仅普通管理员）
    assistant_ids: Optional[list[str]] = []  # 可管理的助手ID列表（仅普通管理员）
    viewable_assistant_ids: Optional[list[str]] = []  # 可查看的助手ID列表（仅普通管理员，独立于assistant_ids）
    avatar_url: Optional[str] = None  # 头像URL
    
    # 细粒度权限字段（仅普通管理员）
    # 助手管理权限
    can_view_assistants: Optional[bool] = None  # 查看助手权限
    can_create_assistants: Optional[bool] = None
    can_edit_assistants: Optional[bool] = None
    can_delete_assistants: Optional[bool] = None
    # 文档管理权限
    can_view_documents: Optional[bool] = None  # 查看文档权限
    can_create_documents: Optional[bool] = None
    can_edit_documents: Optional[bool] = None
    can_delete_documents: Optional[bool] = None
    # 资源管理权限
    can_view_resources: Optional[bool] = None  # 查看资源权限
    can_create_resources: Optional[bool] = None
    can_edit_resources: Optional[bool] = None
    can_delete_resources: Optional[bool] = None
    # 标签管理权限
    can_view_tags: Optional[bool] = None  # 查看标签权限
    can_create_tags: Optional[bool] = None
    can_edit_tags: Optional[bool] = None
    can_delete_tags: Optional[bool] = None
    # 基础提示词编辑权限（仅普通管理员）
    can_edit_base_prompt: Optional[bool] = None  # 编辑基础提示词权限
    # 邮件发送权限（仅普通管理员）
    can_send_notifications: Optional[bool] = None  # 是否可以发送通知/邮件
    can_send_emails_to_all: Optional[bool] = None  # 系统管理员：可以发送给所有人
    can_send_emails_to_students: Optional[bool] = None  # 普通管理员：可以发送给学生
    can_send_emails_to_classes: Optional[List[str]] = None  # 可发送的班级列表
    can_send_emails_to_grades: Optional[List[str]] = None  # 可发送的年级列表
    
    # 新增字段：用户资料扩展
    research_fields: Optional[List[str]] = None  # 研究领域列表
    education: Optional[Dict[str, Any]] = None  # 教育背景（学历、学校、专业、毕业时间、学院）
    work_experience: Optional[List[Dict[str, Any]]] = None  # 工作经历/项目经验列表
    publications: Optional[List[Dict[str, Any]]] = None  # 发表论文/成果列表
    skills: Optional[List[str]] = None  # 技能标签列表
    interests: Optional[List[str]] = None  # 兴趣爱好列表
    personality: Optional[str] = None  # 自我性格描述（学生身份重点）
    bio: Optional[str] = None  # 个人简介
    contact_info: Optional[Dict[str, Any]] = None  # 联系方式（微信、电话等，可选公开）
    profile_visibility: Literal["public", "private", "friends"] = "public"  # 资料可见性设置
    college: Optional[str] = None  # 所属学院
    major: Optional[str] = None  # 所属专业
    
    @classmethod
    def validate_email(cls, v: str) -> str:
        """验证邮箱格式，允许 .local 域名用于开发环境"""
        # 基本的邮箱格式验证（标准格式）
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        # 允许 .local 域名（用于开发环境）
        local_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.local$'
        
        if re.match(email_pattern, v) or re.match(local_pattern, v):
            return v
        else:
            raise ValueError('无效的邮箱格式')


class UserInDB(User):
    """用户模型（包含密码哈希）"""
    hashed_password: str


class UserProfileUpdate(BaseModel):
    """用户资料更新模型"""
    full_name: Optional[str] = None
    research_fields: Optional[List[str]] = None
    education: Optional[Dict[str, Any]] = None
    work_experience: Optional[List[Dict[str, Any]]] = None
    publications: Optional[List[Dict[str, Any]]] = None
    skills: Optional[List[str]] = None
    interests: Optional[List[str]] = None
    personality: Optional[str] = None
    bio: Optional[str] = None
    contact_info: Optional[Dict[str, Any]] = None
    profile_visibility: Optional[Literal["public", "private", "friends"]] = None
    college: Optional[str] = None
    major: Optional[str] = None
    avatar_url: Optional[str] = None


class UserProfileFieldPriority(BaseModel):
    """用户资料字段优先级配置"""
    user_type: Literal["student", "teacher", "other"]
    field_priorities: List[Dict[str, Any]]  # 字段优先级列表，每个包含字段名、优先级、是否必填、引导文案等


class FieldPriorityConfig:
    """字段优先级配置类"""
    
    @staticmethod
    def get_teacher_priorities() -> List[Dict[str, Any]]:
        """获取教师身份的字段优先级配置"""
        return [
            {"field": "work_experience", "priority": 1, "required": False, "label": "工作经历/项目经验", "hint": "作为教师，您的工作经历和项目经验最能展现您的专业能力"},
            {"field": "publications", "priority": 2, "required": False, "label": "发表论文/成果", "hint": "展示您的研究成果和学术贡献"},
            {"field": "research_fields", "priority": 3, "required": False, "label": "研究领域", "hint": "帮助其他用户了解您的研究方向"},
            {"field": "education", "priority": 4, "required": False, "label": "教育背景", "hint": "您的学历、学校、专业等信息（默认博士学历）"},
            {"field": "skills", "priority": 5, "required": False, "label": "技能标签", "hint": "您的专业技能和特长"},
            {"field": "interests", "priority": 6, "required": False, "label": "兴趣爱好", "hint": "展示您的个人兴趣"},
            {"field": "bio", "priority": 7, "required": False, "label": "个人简介", "hint": "简要介绍您自己"},
        ]
    
    @staticmethod
    def get_student_priorities() -> List[Dict[str, Any]]:
        """获取学生身份的字段优先级配置"""
        return [
            {"field": "interests", "priority": 1, "required": False, "label": "兴趣爱好", "hint": "分享您的兴趣爱好，找到志同道合的伙伴"},
            {"field": "skills", "priority": 2, "required": False, "label": "技能标签", "hint": "展示您的技能和特长"},
            {"field": "personality", "priority": 3, "required": False, "label": "自我性格描述", "hint": "描述您的性格特点，帮助他人更好地了解您"},
            {"field": "education", "priority": 4, "required": False, "label": "教育背景", "hint": "您的学校、专业、学院、年级等信息"},
            {"field": "research_fields", "priority": 5, "required": False, "label": "研究领域", "hint": "如果您有研究兴趣或方向"},
            {"field": "work_experience", "priority": 6, "required": False, "label": "工作经历/项目经验", "hint": "您的实习、项目经验等"},
            {"field": "bio", "priority": 7, "required": False, "label": "个人简介", "hint": "简要介绍您自己"},
        ]
    
    @staticmethod
    def get_priorities(user_type: str) -> List[Dict[str, Any]]:
        """根据用户类型获取字段优先级配置"""
        if user_type == "teacher":
            return FieldPriorityConfig.get_teacher_priorities()
        elif user_type == "student":
            return FieldPriorityConfig.get_student_priorities()
        else:
            # 其他类型使用学生配置
            return FieldPriorityConfig.get_student_priorities()



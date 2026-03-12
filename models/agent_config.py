"""深度思考Agent配置模型"""
from pydantic import BaseModel
from typing import Optional, Dict


class AgentConfig(BaseModel):
    """单个Agent的配置模型"""
    agent_type: str  # Agent类型（如 coordinator, document_retrieval 等）
    inference_model: Optional[str] = None  # 推理模型名称（用于生成回复）
    embedding_model: Optional[str] = None  # 向量化模型名称（用于文档向量化）


class AgentConfigUpdate(BaseModel):
    """更新Agent配置请求模型"""
    inference_model: Optional[str] = None  # 推理模型名称（用于生成回复）
    embedding_model: Optional[str] = None  # 向量化模型名称（用于文档向量化）


class AgentConfigsResponse(BaseModel):
    """Agent配置列表响应模型"""
    configs: Dict[str, AgentConfig]  # key为agent_type，value为配置
    total: int


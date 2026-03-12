/** 聊天相关类型定义 */

export interface ChatMessage {
  message_id?: string;  // 消息唯一ID
  role: "user" | "assistant";
  content: string;
  timestamp?: string;
  sources?: SourceInfo[];  // 文档来源（普通模式）
  recommended_resources?: RecommendedResource[];  // 推荐的相关资源（普通模式）
  recommended_users?: RecommendedUser[];  // 推荐用户（网络模式）
  user_relationships?: UserRelationship[];  // 用户关系（网络模式）
  recommendation_reason?: string;  // 推荐理由（网络模式）
  cypher_queries?: CypherQuery[];  // Cypher查询思维链（网络模式）
}

export interface CypherQuery {
  step: string;  // 步骤名称
  description: string;  // 步骤描述
  query: string;  // Cypher查询语句
  result_count?: number;  // 查询结果数量
}

export interface RecommendedUser {
  user_id: string;
  username: string;
  user_type: string;
  score?: number;
  reason?: string;
  properties?: {
    full_name?: string;
    avatar_url?: string;
    research_fields?: string[];
    college?: string;
    major?: string;
    skills?: string[];
  };
}

export interface UserRelationship {
  from_user_id: string;
  from_username?: string;
  to_user_id: string;
  to_username?: string;
  relationship_type: string;
  properties?: Record<string, any>;
}

export interface RecommendedResource {
  resource_id: string;
  title: string;
  description: string;
  file_type: string;
  file_size: number;
  score: number;
}

export interface SourceInfo {
  chunk_id: string;
  document_id: string;
  score: number;
  retrieval_type: string;
  document_title?: string;  // 文档标题
  file_type?: string;  // 文件类型
  status?: string;  // 文档状态
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
  document_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  sources?: SourceInfo[];
}


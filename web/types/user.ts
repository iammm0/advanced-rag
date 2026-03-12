/** 用户相关类型定义 */

export type UserType = "student" | "teacher" | "other";
export type ProfileVisibility = "public" | "private" | "friends";
export type RelationshipType =
  | "TEACHER_COLLEAGUE"
  | "TEACHER_SUPERVISOR"
  | "TEACHER_RESEARCH_RELATED"
  | "STUDENT_SENIOR"
  | "STUDENT_CLASSMATE"
  | "STUDENT_GRADUATION_STATUS"
  | "TEACHER_STUDENT"
  | "TEACHER_STUDENT_RESEARCH_MATCH"
  | "SAME_COLLEGE"
  | "SAME_MAJOR"
  | "ACQUAINTANCE"
  | "FRIEND"
  | "CLOSE_FRIEND"
  | "ROOMMATE";

export interface Education {
  degree?: string;
  school?: string;
  major?: string;
  college?: string;
  graduation_year?: string;
}

export interface WorkExperience {
  company?: string;
  position?: string;
  start_date?: string;
  end_date?: string;
  description?: string;
  projects?: string[];
}

export interface Publication {
  title?: string;
  authors?: string[];
  journal?: string;
  year?: string;
  doi?: string;
}

export interface ContactInfo {
  wechat?: string;
  phone?: string;
  email?: string;
}

export interface UserProfile {
  id: string;
  username: string;
  email: string;
  full_name?: string;
  user_type: UserType;
  avatar_url?: string;
  research_fields?: string[];
  education?: Education;
  work_experience?: WorkExperience[];
  publications?: Publication[];
  skills?: string[];
  interests?: string[];
  personality?: string;
  bio?: string;
  contact_info?: ContactInfo;
  profile_visibility: ProfileVisibility;
  college?: string;
  major?: string;
}

export interface Relationship {
  from_user_id: string;
  from_username?: string;
  to_user_id: string;
  to_username?: string;
  relationship_type: RelationshipType;
  properties?: Record<string, any>;
}

export interface RecommendedUser {
  user_id: string;
  username: string;
  user_type: UserType;
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

export interface UserNetworkGraph {
  nodes: NetworkNode[];
  edges: NetworkEdge[];
}

export interface NetworkNode {
  id: string;
  label: string;
  title?: string;
  image?: string;
  shape?: string;
  user_type?: UserType;
  color?: string;
  properties?: Record<string, any>;
  is_online?: boolean; // 在线状态
}

export interface NetworkEdge {
  from: string;
  to: string;
  label?: string;
  color?: string;
  arrows?: string;
  relationship_type?: RelationshipType;
  properties?: Record<string, any>;
}

// 兼容旧类型
export interface UserRelationshipGraph {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface GraphNode {
  id: string;
  label: string;
  user_type?: UserType;
  properties?: Record<string, any>;
}

export interface GraphEdge {
  from_id: string;
  to_id: string;
  relationship_type: RelationshipType;
  properties?: Record<string, any>;
}

export interface FieldPriority {
  field: string;
  priority: number;
  required: boolean;
  label: string;
  hint: string;
}

export interface FieldPriorityConfig {
  user_type: UserType;
  field_priorities: FieldPriority[];
}

export interface UserProfileUpdate {
  full_name?: string;
  bio?: string;
  research_fields?: string[];
  skills?: string[];
  interests?: string[];
  college?: string;
  major?: string;
  education?: Education;
  work_experience?: WorkExperience[];
  publications?: Publication[];
  contact_info?: ContactInfo;
  profile_visibility?: ProfileVisibility;
  personality?: string;
}

export type UserProfileFieldPriorityConfig = FieldPriorityConfig;


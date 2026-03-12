export interface CourseAssistant {
  id: string;
  name: string;
  description?: string;
  system_prompt: string;
  collection_name: string;
  is_default: boolean;
  greeting_message?: string;
  quick_prompts?: string[];
  inference_model?: string; // 推理模型名称
  embedding_model?: string; // 向量化模型名称
  icon_url?: string; // 助手图标URL
  created_at: string;
  updated_at: string;
}

export interface CourseAssistantListResponse {
  assistants: CourseAssistant[];
  total: number;
}

export interface CourseAssistantCreate {
  name: string;
  description?: string;
  system_prompt: string;
  collection_name?: string;
  is_default?: boolean;
  greeting_message?: string;
  quick_prompts?: string[];
  icon_url?: string; // 助手图标URL
}

export interface CourseAssistantUpdate {
  name?: string;
  description?: string;
  system_prompt?: string;
  is_default?: boolean;
  greeting_message?: string;
  quick_prompts?: string[];
  inference_model?: string; // 推理模型名称
  embedding_model?: string; // 向量化模型名称
  icon_url?: string; // 助手图标URL
}


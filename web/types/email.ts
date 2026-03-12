export type EmailPriority = "low" | "normal" | "high" | "urgent";
export type EmailStatus = "draft" | "sent" | "deleted";
export type EmailFolder = "inbox" | "sent" | "draft" | "trash";
export type EmailTargetAudience = "all" | "students" | "teachers";

export interface EmailAttachment {
  filename: string;
  file_path: string;
  file_size: number;
  content_type: string;
}

export interface Email {
  id: string;
  from_user_id: string;
  from_username: string;
  to_user_ids: string[];
  to_user_type?: EmailTargetAudience;
  to_class_names?: string[];
  to_grades?: string[];
  subject: string;
  content: string;
  markdown_content?: string;
  attachments: EmailAttachment[];
  priority: EmailPriority;
  status: EmailStatus;
  is_relationship_required: boolean;
  relationship_invitation_id?: string;  // 关联的关系邀请ID（如果是关系邀请邮件）
  created_at: string;
  sent_at?: string;
  updated_at: string;
}

export interface EmailListItem {
  id: string;
  from_user_id: string;
  from_username: string;
  subject: string;
  content_preview: string;
  content?: string;  // 完整内容（用于对话视图）
  priority: EmailPriority;
  is_read: boolean;
  created_at: string;
  sent_at?: string;
  folder: EmailFolder;
}

export interface EmailListResponse {
  emails: EmailListItem[];
  total: number;
  unread_count: number;
  page: number;
  page_size: number;
}

export interface EmailCreateRequest {
  to_user_ids?: string[];
  to_user_type?: EmailTargetAudience;
  to_class_names?: string[];
  to_grades?: string[];
  subject: string;
  content: string;
  markdown_content?: string;
  priority?: EmailPriority;
  is_relationship_required?: boolean;
}

export interface EmailDraftCreateRequest {
  to_user_ids?: string[];
  to_user_type?: EmailTargetAudience;
  to_class_names?: string[];
  to_grades?: string[];
  subject: string;
  content: string;
  markdown_content?: string;
  priority?: EmailPriority;
}

export interface BatchEmailCreateRequest {
  to_user_type: EmailTargetAudience;
  to_class_names?: string[];
  to_grades?: string[];
  subject: string;
  content: string;
  markdown_content?: string;
  priority?: EmailPriority;
}


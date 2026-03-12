export interface Resource {
  id: string;
  title: string;
  description: string;
  file_type: string;
  file_size: number;
  created_at: string;
  updated_at: string;
  assistant_id?: string;
  url?: string;
  thumbnail_url?: string; // 视频封面URL
  cover_image?: string; // 资源封面图片路径
  tags?: string[];
  uploader_id?: string;
  uploader_username?: string;
  uploader_name?: string;
}

export interface ResourceDetail extends Resource {
  file_path?: string;
  uploader_id?: string;
  uploader_username?: string;
  uploader_name?: string;
  cover_image?: string; // 资源封面图片路径
}

export interface ResourceListResponse {
  resources: Resource[];
  total: number;
}

export interface RecommendedResource {
  resource_id: string;
  title: string;
  description: string;
  file_type: string;
  file_size: number;
  url?: string;  // 外部链接URL
  thumbnail_url?: string;  // 视频封面URL
  cover_image?: string;  // 资源封面图片路径
  score: number;
}


"use client";

import { useState, useRef } from "react";
import { apiClient } from "@/lib/api";

interface DocumentUploadProps {
  onUploadSuccess?: () => void;
  knowledgeSpaceId?: string;
}

export default function DocumentUpload({
  onUploadSuccess,
  knowledgeSpaceId,
}: DocumentUploadProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = e.dataTransfer.files;
    if (files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      handleFileUpload(files[0]);
    }
  };

  const handleFileUpload = async (file: File) => {
    if (!knowledgeSpaceId) {
      setError("请先选择要上传到的知识空间");
      return;
    }
    // 检查文件类型（包括可以转换的格式）
    const allowedTypes = [
      "application/pdf",
      "application/vnd.openxmlformats-officedocument.wordprocessingml.document", // .docx
      "application/msword", // .doc
      "text/markdown",
      "text/plain",
    ];
    const allowedExtensions = [".pdf", ".docx", ".doc", ".md", ".txt", ".markdown"];

    const fileExt = file.name.toLowerCase().split(".").pop();
    if (
      !allowedTypes.includes(file.type) &&
      !allowedExtensions.includes(`.${fileExt}`)
    ) {
      setError(
        `不支持的文件类型。支持的类型: PDF, Word (.doc/.docx), Markdown, TXT`
      );
      return;
    }

    // 检查文件大小（限制为200MB）
    if (file.size > 200 * 1024 * 1024) {
      setError("文件大小不能超过200MB");
      return;
    }

    setError("");
    setUploading(true);
    setProgress(0);

    try {
      // 使用真实的上传进度（基于文件大小）
      const formData = new FormData();
      formData.append("file", file);

      const xhr = new XMLHttpRequest();

      // 监听上传进度
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100);
          setProgress(Math.min(percentComplete, 95)); // 最多到95%，等待响应
        }
      });

      // 必须指定知识空间
      formData.append("knowledge_space_id", knowledgeSpaceId);

      // 创建 Promise 来处理上传
      const uploadPromise = new Promise<{ data?: any; error?: string }>((resolve) => {
        xhr.addEventListener("load", () => {
          if (xhr.status >= 200 && xhr.status < 300) {
            try {
              const data = JSON.parse(xhr.responseText);
              resolve({ data });
            } catch (e) {
              resolve({ error: "响应解析失败" });
            }
          } else {
            try {
              const error = JSON.parse(xhr.responseText);
              resolve({ error: error.detail || error.message || error.error || "上传失败" });
            } catch (e) {
              resolve({ error: `上传失败: ${xhr.statusText}` });
            }
          }
        });

        xhr.addEventListener("error", () => {
          resolve({ error: "网络错误" });
        });

        xhr.addEventListener("timeout", () => {
          resolve({ error: "上传超时" });
        });

        // 设置请求URL
        const url = "/api/documents/upload";
        
        xhr.open("POST", url);
        
        // 设置超时（15分钟，支持大文件上传）
        xhr.timeout = 15 * 60 * 1000;

        // 发送请求
        xhr.send(formData);
      });

      const result = await uploadPromise;

      setProgress(100);

      if (result.error) {
        setError(result.error);
      } else {
        setProgress(0);
        onUploadSuccess?.();
        if (fileInputRef.current) {
          fileInputRef.current.value = "";
        }
      }
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setUploading(false);
      setTimeout(() => setProgress(0), 1000);
    }
  };

  return (
    <div className="w-full">
      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
          isDragging
            ? "border-blue-500 dark:border-blue-400 bg-blue-50 dark:bg-blue-900/20"
            : "border-gray-300 dark:border-gray-600 hover:border-gray-400 dark:hover:border-gray-500"
        }`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.docx,.doc,.md,.txt,.markdown"
          onChange={handleFileSelect}
          className="hidden"
          disabled={uploading}
        />

        {uploading ? (
          <div className="space-y-2">
            <div 
              className="text-gray-600 dark:text-gray-300"
              suppressHydrationWarning
            >
              上传中... {progress}%
            </div>
            <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 dark:bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        ) : (
          <>
            <p 
              className="mt-2 text-sm text-gray-600 dark:text-gray-300"
              suppressHydrationWarning
            >
              <button
                onClick={() => fileInputRef.current?.click()}
                className="text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300"
                suppressHydrationWarning
              >
                点击上传
              </button>
              <span suppressHydrationWarning>或拖拽文件到此处</span>
            </p>
            <p 
              className="mt-1 text-xs text-gray-500 dark:text-gray-400"
              suppressHydrationWarning
            >
              支持 PDF, Word (.doc/.docx), Markdown, TXT (最大200MB)
            </p>
            <p 
              className="mt-1 text-xs text-blue-600 dark:text-blue-400"
              suppressHydrationWarning
            >
              提示：.doc 文件会自动转换为 .docx 后处理
            </p>
          </>
        )}
      </div>

      {error && (
        <div className="mt-2 p-3 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-sm">
          {error}
        </div>
      )}
    </div>
  );
}


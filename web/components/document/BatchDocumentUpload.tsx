"use client";

import { useState, useRef } from "react";
import { apiClient } from "@/lib/api";
import Toast, { ToastType } from "@/components/ui/Toast";

interface BatchDocumentUploadProps {
  onUploadSuccess?: () => void;
  knowledgeSpaceId?: string;
}

interface UploadFile {
  file: File;
  status: "pending" | "uploading" | "success" | "error";
  progress: number;
  error?: string;
}

export default function BatchDocumentUpload({
  onUploadSuccess,
  knowledgeSpaceId,
}: BatchDocumentUploadProps) {
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [toast, setToast] = useState<{ isOpen: boolean; message: string; type: ToastType }>({
    isOpen: false,
    message: "",
    type: "info",
  });

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

    const droppedFiles = Array.from(e.dataTransfer.files);
    addFiles(droppedFiles);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = e.target.files;
    if (selectedFiles && selectedFiles.length > 0) {
      addFiles(Array.from(selectedFiles));
    }
  };

  const addFiles = (newFiles: File[]) => {
    // 与后端保持一致：只允许可以被正确解析和分块的文档类型
    const allowedExtensions = [".pdf", ".docx", ".doc", ".md", ".txt", ".markdown"];
    const validFiles: UploadFile[] = [];

    newFiles.forEach((file) => {
      // 获取文件扩展名（不区分大小写）
      const fileName = file.name.toLowerCase();
      const fileExt = fileName.substring(fileName.lastIndexOf("."));
      
      // 检查文件扩展名
      if (!allowedExtensions.includes(fileExt)) {
        validFiles.push({
          file,
          status: "error",
          progress: 0,
          error: `不支持的文件类型 ${fileExt}。仅支持：PDF, Word (.doc/.docx), Markdown (.md/.markdown), TXT`,
        });
        return;
      }

      // 检查文件大小（200MB限制，与后端一致）
      if (file.size > 200 * 1024 * 1024) {
        validFiles.push({
          file,
          status: "error",
          progress: 0,
          error: `文件大小超过200MB限制（当前：${(file.size / (1024 * 1024)).toFixed(2)}MB）`,
        });
        return;
      }

      // 检查文件是否为空
      if (file.size === 0) {
        validFiles.push({
          file,
          status: "error",
          progress: 0,
          error: "文件不能为空",
        });
        return;
      }

      // 检查是否已存在相同文件（文件名和大小都相同）
      const exists = files.some(
        (f) => f.file.name === file.name && f.file.size === file.size
      );
      if (exists) {
        validFiles.push({
          file,
          status: "error",
          progress: 0,
          error: "文件已存在列表中",
        });
        return;
      }

      // 文件验证通过，添加到待上传列表
      validFiles.push({
        file,
        status: "pending",
        progress: 0,
      });
    });

    setFiles((prev) => [...prev, ...validFiles]);
  };

  const removeFile = (index: number) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const clearAll = () => {
    setFiles([]);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const uploadFile = async (uploadFile: UploadFile, index: number): Promise<void> => {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append("file", uploadFile.file);

      if (!knowledgeSpaceId) {
        reject(new Error("请先选择要上传到的知识空间"));
        return;
      }
      formData.append("knowledge_space_id", knowledgeSpaceId);

      const xhr = new XMLHttpRequest();

      // 更新状态为上传中
      setFiles((prev) => {
        const updated = [...prev];
        updated[index] = { ...updated[index], status: "uploading", progress: 0 };
        return updated;
      });

      // 监听上传进度
      xhr.upload.addEventListener("progress", (e) => {
        if (e.lengthComputable) {
          const percentComplete = Math.round((e.loaded / e.total) * 100);
          setFiles((prev) => {
            const updated = [...prev];
            updated[index] = { ...updated[index], progress: Math.min(percentComplete, 95) };
            return updated;
          });
        }
      });

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          setFiles((prev) => {
            const updated = [...prev];
            updated[index] = { ...updated[index], status: "success", progress: 100 };
            return updated;
          });
          resolve();
        } else {
          try {
            const error = JSON.parse(xhr.responseText);
            const errorMsg = error.detail || error.message || error.error || "上传失败";
            setFiles((prev) => {
              const updated = [...prev];
              updated[index] = {
                ...updated[index],
                status: "error",
                error: errorMsg,
              };
              return updated;
            });
            reject(new Error(errorMsg));
          } catch {
            setFiles((prev) => {
              const updated = [...prev];
              updated[index] = {
                ...updated[index],
                status: "error",
                error: `上传失败: ${xhr.statusText}`,
              };
              return updated;
            });
            reject(new Error(`上传失败: ${xhr.statusText}`));
          }
        }
      });

      xhr.addEventListener("error", () => {
        setFiles((prev) => {
          const updated = [...prev];
          updated[index] = {
            ...updated[index],
            status: "error",
            error: "网络错误",
          };
          return updated;
        });
        reject(new Error("网络错误"));
      });

      xhr.addEventListener("timeout", () => {
        setFiles((prev) => {
          const updated = [...prev];
          updated[index] = {
            ...updated[index],
            status: "error",
            error: "上传超时",
          };
          return updated;
        });
        reject(new Error("上传超时"));
      });

      const url = "/api/documents/upload";
      xhr.open("POST", url);

      xhr.timeout = 15 * 60 * 1000; // 15分钟超时
      xhr.send(formData);
    });
  };

  const handleBatchUpload = async () => {
    if (!knowledgeSpaceId) {
      setToast({ isOpen: true, message: "请先选择要上传到的知识空间", type: "warning" });
      return;
    }
    const pendingFiles = files.filter((f) => f.status === "pending" || f.status === "error");
    if (pendingFiles.length === 0) {
      return;
    }

    setUploading(true);

    try {
      // 顺序上传文件（避免服务器压力过大）
      for (let i = 0; i < files.length; i++) {
        if (files[i].status === "pending" || files[i].status === "error") {
          try {
            await uploadFile(files[i], i);
            // 每个文件上传后稍作延迟
            await new Promise((resolve) => setTimeout(resolve, 100));
          } catch (error) {
            // 继续上传其他文件
            console.error(`文件 ${files[i].file.name} 上传失败:`, error);
          }
        }
      }

      // 检查是否有成功上传的文件
      const successCount = files.filter((f) => f.status === "success").length;
      const errorCount = files.filter((f) => f.status === "error").length;
      
      if (successCount > 0) {
        if (errorCount > 0) {
          setToast({
            isOpen: true,
            message: `批量上传完成：成功 ${successCount} 个，失败 ${errorCount} 个`,
            type: "warning",
          });
        } else {
          setToast({
            isOpen: true,
            message: `批量上传完成：成功上传 ${successCount} 个文件`,
            type: "success",
          });
        }
        onUploadSuccess?.();
      } else if (errorCount > 0) {
        setToast({
          isOpen: true,
          message: `批量上传失败：所有 ${errorCount} 个文件上传失败`,
          type: "error",
        });
      }
    } catch (error) {
      console.error("批量上传失败:", error);
      setToast({
        isOpen: true,
        message: `批量上传失败: ${(error as Error).message || "未知错误"}`,
        type: "error",
      });
    } finally {
      setUploading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + " B";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + " KB";
    if (bytes < 1024 * 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " MB";
    return (bytes / (1024 * 1024 * 1024)).toFixed(1) + " GB";
  };

  const pendingCount = files.filter((f) => f.status === "pending").length;
  const successCount = files.filter((f) => f.status === "success").length;
  const errorCount = files.filter((f) => f.status === "error").length;
  const uploadingCount = files.filter((f) => f.status === "uploading").length;

  return (
    <div className="w-full space-y-4">
      {/* 文件选择区域 */}
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
          multiple
          onChange={handleFileSelect}
          className="hidden"
          disabled={uploading}
        />

        <svg
          className="mx-auto h-12 w-12 text-gray-400 dark:text-gray-500"
          stroke="currentColor"
          fill="none"
          viewBox="0 0 48 48"
        >
          <path
            d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
            strokeWidth={2}
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-300">
          <button
            onClick={() => fileInputRef.current?.click()}
            className="text-blue-500 dark:text-blue-400 hover:text-blue-600 dark:hover:text-blue-300 font-medium"
            disabled={uploading}
          >
            点击选择文件
          </button>
          <span className="mx-2">或拖拽文件到此处</span>
        </p>
        <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
          支持 PDF, Word (.doc/.docx), Markdown (.md/.markdown), TXT (最大200MB/文件)
        </p>
        <p className="mt-1 text-xs text-blue-600 dark:text-blue-400">
          提示：可以一次选择多个文件进行批量上传。系统会自动验证文件类型和内容，仅允许可正确解析和分块的文档。
        </p>
      </div>

      {/* 文件列表 */}
      {files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-medium text-gray-700 dark:text-gray-300">
              已选择文件 ({files.length})
            </h4>
            <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
              {pendingCount > 0 && <span>待上传: {pendingCount}</span>}
              {uploadingCount > 0 && <span>上传中: {uploadingCount}</span>}
              {successCount > 0 && <span className="text-green-600 dark:text-green-400">成功: {successCount}</span>}
              {errorCount > 0 && <span className="text-red-600 dark:text-red-400">失败: {errorCount}</span>}
            </div>
            <button
              onClick={clearAll}
              disabled={uploading}
              className="text-xs text-red-600 dark:text-red-400 hover:text-red-700 dark:hover:text-red-300 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              清空全部
            </button>
          </div>

          <div className="max-h-96 overflow-y-auto space-y-2">
            {files.map((uploadFile, index) => (
              <div
                key={`${uploadFile.file.name}-${index}`}
                className={`p-3 rounded-lg border ${
                  uploadFile.status === "success"
                    ? "bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800"
                    : uploadFile.status === "error"
                    ? "bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800"
                    : uploadFile.status === "uploading"
                    ? "bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800"
                    : "bg-gray-50 dark:bg-gray-800/50 border-gray-200 dark:border-gray-700"
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
                        {uploadFile.file.name}
                      </span>
                      {uploadFile.status === "success" && (
                        <svg className="w-4 h-4 text-green-600 dark:text-green-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                        </svg>
                      )}
                      {uploadFile.status === "error" && (
                        <svg className="w-4 h-4 text-red-600 dark:text-red-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      )}
                      {uploadFile.status === "uploading" && (
                        <svg className="w-4 h-4 text-blue-600 dark:text-blue-400 animate-spin flex-shrink-0" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      )}
                    </div>
                    <div className="mt-1 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                      <span>{formatFileSize(uploadFile.file.size)}</span>
                      {uploadFile.status === "uploading" && (
                        <span>{uploadFile.progress}%</span>
                      )}
                      {uploadFile.error && (
                        <span className="text-red-600 dark:text-red-400">{uploadFile.error}</span>
                      )}
                    </div>
                    {uploadFile.status === "uploading" && (
                      <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                        <div
                          className="bg-blue-600 dark:bg-blue-500 h-1.5 rounded-full transition-all duration-300"
                          style={{ width: `${uploadFile.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                  {uploadFile.status !== "uploading" && (
                    <button
                      onClick={() => removeFile(index)}
                      disabled={uploading}
                      className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 上传按钮 */}
      {files.length > 0 && (
        <div className="flex justify-end gap-3">
          <button
            onClick={clearAll}
            disabled={uploading}
            className="px-4 py-2 text-sm font-medium text-gray-700 dark:text-gray-200 bg-gray-100 dark:bg-gray-700 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            清空
          </button>
          <button
            onClick={handleBatchUpload}
            disabled={uploading || pendingCount === 0}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 dark:bg-blue-500 rounded-lg hover:bg-blue-700 dark:hover:bg-blue-600 disabled:bg-gray-400 dark:disabled:bg-gray-600 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
          >
            {uploading ? (
              <>
                <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                上传中...
              </>
            ) : (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                开始批量上传 ({pendingCount})
              </>
            )}
          </button>
        </div>
      )}

      {/* Toast 通知 */}
      <Toast
        isOpen={toast.isOpen}
        message={toast.message}
        type={toast.type}
        onClose={() => setToast({ ...toast, isOpen: false })}
      />
    </div>
  );
}


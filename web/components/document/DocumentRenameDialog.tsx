"use client";

import { useState, useEffect, useRef } from "react";

interface DocumentRenameDialogProps {
  isOpen: boolean;
  currentTitle: string;
  onConfirm: (newTitle: string) => void;
  onCancel: () => void;
  onError?: (message: string) => void;
}

export default function DocumentRenameDialog({
  isOpen,
  currentTitle,
  onConfirm,
  onCancel,
  onError,
}: DocumentRenameDialogProps) {
  const [newTitle, setNewTitle] = useState(currentTitle);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    setNewTitle(currentTitle);
  }, [currentTitle]);

  useEffect(() => {
    if (isOpen && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isOpen]);

  // ESC 键关闭
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onCancel();
      }
    };
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [isOpen, onCancel]);

  // 阻止背景滚动
  useEffect(() => {
    if (isOpen) {
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }
    return () => {
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedTitle = newTitle.trim();
    if (trimmedTitle && trimmedTitle !== currentTitle) {
      onConfirm(trimmedTitle);
    } else if (!trimmedTitle) {
      if (onError) {
        onError("文档标题不能为空");
      }
    } else {
      onCancel();
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* 背景遮罩 */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        style={{ animation: "fadeIn 0.2s ease-out" }}
        onClick={onCancel}
      />
      
      {/* 对话框 */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 pointer-events-none">
        <div
          className="bg-white dark:bg-gray-800 rounded-lg sm:rounded-xl shadow-2xl max-w-md w-full pointer-events-auto"
          style={{ animation: "zoomIn 0.2s ease-out" }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* 内容区域 */}
          <div className="p-4 sm:p-6">
            {/* 标题 */}
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3 sm:mb-4">
              重命名文档
            </h3>
            
            {/* 表单 */}
            <form onSubmit={handleSubmit}>
              <input
                ref={inputRef}
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                className="w-full px-3 sm:px-4 py-2 text-sm sm:text-base border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:ring-offset-2 bg-white dark:bg-gray-700 text-gray-800 dark:text-gray-100 mb-4 sm:mb-6 transition-colors"
                placeholder="输入文档标题..."
                maxLength={200}
              />
              
              {/* 按钮组 */}
              <div className="flex flex-col-reverse sm:flex-row justify-end gap-2 sm:gap-3">
                <button
                  type="button"
                  onClick={onCancel}
                  className="px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium text-gray-700 dark:text-gray-200 bg-white dark:bg-gray-700 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 dark:focus:ring-gray-400 focus:ring-offset-2 transition-colors"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-3 sm:px-4 py-2 text-xs sm:text-sm font-medium text-white bg-blue-500 dark:bg-blue-600 rounded-lg hover:bg-blue-600 dark:hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:ring-offset-2 transition-colors"
                >
                  确定
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </>
  );
}


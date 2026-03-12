"use client";

import { useState, useEffect } from "react";
import {
  fetchConversationsFromAPI,
  updateConversationFromAPI,
  deleteConversationFromAPI,
  saveConversations,
} from "@/lib/conversation";
import { Conversation } from "@/types/conversation";
import ConfirmDialog from "../ui/ConfirmDialog";
import RenameDialog from "../ui/RenameDialog";
import { formatDateTime } from "@/lib/timezone";

interface ChatSidebarProps {
  currentConversationId: string | undefined;
  onConversationSelect: (id: string | undefined) => void;
  onNewConversation: () => void;
  isOpen?: boolean;
  onOpenChange?: (isOpen: boolean) => void;
}

export default function ChatSidebar({
  currentConversationId,
  onConversationSelect,
  onNewConversation,
  isOpen: externalIsOpen,
  onOpenChange,
}: ChatSidebarProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [internalIsOpen, setInternalIsOpen] = useState(true);
  // 如果外部提供了 isOpen，使用外部的；否则使用内部的
  const isOpen = externalIsOpen !== undefined ? externalIsOpen : internalIsOpen;
  const setIsOpen = (value: boolean) => {
    if (onOpenChange) {
      onOpenChange(value);
    } else {
      setInternalIsOpen(value);
    }
  };
  const [mounted, setMounted] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(() => {
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("chatSidebarCollapsed");
      return saved === "true";
    }
    return false;
  });
  const [deleteDialog, setDeleteDialog] = useState<{
    isOpen: boolean;
    conversationId: string | null;
  }>({ isOpen: false, conversationId: null });
  
  const [renameDialog, setRenameDialog] = useState<{
    isOpen: boolean;
    conversationId: string | null;
    currentTitle: string;
  }>({ isOpen: false, conversationId: null, currentTitle: "" });

  useEffect(() => {
    setMounted(true);
    const loadConversations = async () => {
      try {
        // 从 API 获取对话列表
        const conversations = await fetchConversationsFromAPI();
        setConversations(conversations);
        // 同时更新 localStorage 作为缓存
        saveConversations(conversations);
      } catch (error) {
        console.error("加载对话列表失败:", error);
      }
    };
    
    loadConversations();
    
    // 定期刷新对话列表（每30秒）
    const interval = setInterval(loadConversations, 30000);
    
    return () => {
      clearInterval(interval);
    };
  }, []);

  const handleNewConversation = () => {
    onNewConversation();
  };

  const handleSelectConversation = (id: string) => {
    onConversationSelect(id);
  };

  const handleRenameConversation = (
    e: React.MouseEvent,
    id: string,
    currentTitle: string
  ) => {
    e.stopPropagation();
    setRenameDialog({ isOpen: true, conversationId: id, currentTitle });
  };

  const handleDeleteConversation = (
    e: React.MouseEvent,
    id: string
  ) => {
    e.stopPropagation();
    setDeleteDialog({ isOpen: true, conversationId: id });
  };

  const confirmDelete = async () => {
    if (deleteDialog.conversationId) {
      const success = await deleteConversationFromAPI(deleteDialog.conversationId);
      if (success) {
        // 重新加载对话列表
        const conversations = await fetchConversationsFromAPI();
        setConversations(conversations);
        saveConversations(conversations);
        
        if (currentConversationId === deleteDialog.conversationId) {
          onConversationSelect(undefined);
        }
      }
    }
    setDeleteDialog({ isOpen: false, conversationId: null });
  };

  const cancelDelete = () => {
    setDeleteDialog({ isOpen: false, conversationId: null });
  };

  const confirmRename = async (newTitle: string) => {
    if (renameDialog.conversationId) {
      const success = await updateConversationFromAPI(renameDialog.conversationId, newTitle);
      if (success) {
        // 重新加载对话列表
        const conversations = await fetchConversationsFromAPI();
        setConversations(conversations);
        saveConversations(conversations);
      }
    }
    setRenameDialog({ isOpen: false, conversationId: null, currentTitle: "" });
  };

  const cancelRename = () => {
    setRenameDialog({ isOpen: false, conversationId: null, currentTitle: "" });
  };

  const formatDate = (dateString: string) => {
    return formatDateTime(dateString);
  };
  
  // 保留原有的相对时间格式化逻辑（如果需要）
  const formatRelativeDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));

    if (days === 0) {
      return date.toLocaleTimeString("zh-CN", {
        hour: "2-digit",
        minute: "2-digit",
      });
    } else if (days === 1) {
      return "昨天";
    } else if (days < 7) {
      return `${days}天前`;
    } else {
      return date.toLocaleDateString("zh-CN", {
        month: "short",
        day: "numeric",
      });
    }
  };

  return (
    <>
      {/* 移动端遮罩层 */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black bg-opacity-20 dark:bg-opacity-25 z-40 md:hidden"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* 侧边栏 */}
      <div
        className={`fixed md:relative inset-y-0 left-0 z-50 md:z-auto ${
          isCollapsed ? "w-12 md:w-14" : "w-[280px] sm:w-64 md:w-72"
        } ${
          isCollapsed 
            ? "bg-gray-50 dark:bg-gray-800/50 border-r border-gray-200 dark:border-gray-700" 
            : "bg-white dark:bg-gray-800 rounded-lg shadow-sm border border-gray-200 dark:border-gray-700"
        } flex flex-col transition-all duration-300 ${
          isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        style={{ 
          maxWidth: isCollapsed ? '3.5rem' : 'calc(100vw - 2rem)',
          WebkitOverflowScrolling: 'touch'
        }}
      >
        {isCollapsed ? (
          /* 折叠状态：只显示恢复按钮 */
          <div className="flex flex-col items-center justify-start pt-4 px-2 h-full">
            <button
              onClick={() => {
                const newCollapsed = false;
                setIsCollapsed(newCollapsed);
                if (typeof window !== "undefined") {
                  localStorage.setItem("chatSidebarCollapsed", String(newCollapsed));
                }
              }}
              className="w-10 h-10 md:w-12 md:h-12 p-2 bg-gradient-to-br from-blue-500 to-blue-600 dark:from-blue-600 dark:to-blue-700 text-white rounded-xl hover:from-blue-600 hover:to-blue-700 dark:hover:from-blue-700 dark:hover:to-blue-800 transition-all duration-200 flex items-center justify-center shadow-lg hover:shadow-xl hover:scale-105 active:scale-95"
              title="展开侧边栏"
            >
              <svg className="w-5 h-5 md:w-6 md:h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        ) : (
          <>
            {/* 侧边栏头部 */}
            <div className="p-3 sm:p-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between bg-gray-50 dark:bg-gray-900 rounded-t-lg">
              <h2 className="text-sm sm:text-base font-semibold text-gray-900 dark:text-gray-100 truncate" suppressHydrationWarning>对话历史</h2>
              {mounted && (
                <div className="flex items-center gap-2">
                  {/* 桌面端折叠按钮 */}
                  <button
                    onClick={() => {
                      const newCollapsed = true;
                      setIsCollapsed(newCollapsed);
                      if (typeof window !== "undefined") {
                        localStorage.setItem("chatSidebarCollapsed", String(newCollapsed));
                      }
                    }}
                    className="hidden md:flex text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-200 text-sm p-1 rounded hover:bg-gray-100 dark:hover:bg-gray-700 min-w-[32px] min-h-[32px] items-center justify-center"
                    title="折叠侧边栏"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                    </svg>
                  </button>
                  {/* 移动端关闭按钮 */}
                  <button
                    onClick={() => setIsOpen(false)}
                    className="md:hidden text-gray-500 dark:text-gray-400 active:text-gray-700 dark:active:text-gray-200 text-sm px-2 py-1.5 min-h-[44px] min-w-[44px] flex items-center justify-center rounded active:bg-gray-100 dark:active:bg-gray-700"
                  >
                    关闭
                  </button>
                </div>
              )}
            </div>

            {/* 新建对话按钮 */}
            <div className="p-2 sm:p-3 md:p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900">
              <button
                onClick={handleNewConversation}
                className="w-full px-3 sm:px-4 py-2 sm:py-2.5 min-h-[44px] sm:min-h-0 bg-blue-500 dark:bg-blue-600 text-white rounded-lg active:bg-blue-600 dark:active:bg-blue-700 transition-colors text-xs sm:text-sm font-medium shadow-sm"
                suppressHydrationWarning
              >
                新建对话
              </button>
            </div>

            {/* 对话列表 */}
            <div className="flex-1 overflow-y-auto" style={{ WebkitOverflowScrolling: 'touch' }}>
              {!mounted ? (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400 text-sm" suppressHydrationWarning>
                  加载中...
                </div>
              ) : conversations.length === 0 ? (
                <div className="p-4 text-center text-gray-500 dark:text-gray-400 text-sm" suppressHydrationWarning>
                  暂无对话记录
                </div>
              ) : (
                <div className="p-1 sm:p-2">
                  {conversations.map((conversation) => (
                    <div
                      key={conversation.id}
                      onClick={() => {
                        handleSelectConversation(conversation.id);
                        // 移动端选择对话后自动关闭侧边栏
                        if (window.innerWidth < 768) {
                          setIsOpen(false);
                        }
                      }}
                      className={`group relative mb-1 rounded-md cursor-pointer transition-all p-2.5 sm:p-3 min-h-[60px] sm:min-h-0 ${
                        currentConversationId === conversation.id
                          ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-l-2 border-blue-500 dark:border-blue-400"
                          : "active:bg-gray-50 dark:active:bg-gray-700 text-gray-700 dark:text-gray-300 border-l-2 border-transparent"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div 
                          className="flex-1 min-w-0 cursor-pointer"
                          onDoubleClick={(e) => {
                            e.stopPropagation();
                            handleRenameConversation(e, conversation.id, conversation.title);
                          }}
                        >
                          <div className="text-xs sm:text-sm font-medium truncate leading-snug">
                            {conversation.title}
                          </div>
                          <div className="text-[10px] sm:text-xs text-gray-500 dark:text-gray-400 mt-1" suppressHydrationWarning>
                            {mounted ? formatDate(conversation.updatedAt) : ""}
                          </div>
                        </div>
                        <div className="ml-2 flex gap-1.5 sm:gap-1 opacity-100 sm:opacity-0 sm:group-hover:opacity-100 transition-opacity flex-shrink-0">
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRenameConversation(e, conversation.id, conversation.title);
                            }}
                            className="text-gray-400 dark:text-gray-500 active:text-blue-500 dark:active:text-blue-400 transition-colors text-[10px] sm:text-xs px-1.5 sm:px-1 py-1 sm:py-0.5 min-h-[32px] sm:min-h-0 rounded active:bg-gray-100 dark:active:bg-gray-700"
                            title="重命名"
                            suppressHydrationWarning
                          >
                            编辑
                          </button>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteConversation(e, conversation.id);
                            }}
                            className="text-gray-400 dark:text-gray-500 active:text-red-500 dark:active:text-red-400 transition-colors text-[10px] sm:text-xs px-1.5 sm:px-1 py-1 sm:py-0.5 min-h-[32px] sm:min-h-0 rounded active:bg-gray-100 dark:active:bg-gray-700"
                            title="删除"
                            suppressHydrationWarning
                          >
                            删除
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>

      {/* 移动端打开按钮 - 已移除，由 Navbar 控制 */}

      {/* 删除确认对话框 */}
      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        title="删除对话"
        message="确定要删除这个对话吗？删除后无法恢复。"
        confirmText="删除"
        cancelText="取消"
        onConfirm={confirmDelete}
        onCancel={cancelDelete}
        variant="danger"
      />

      {/* 重命名对话框 */}
      <RenameDialog
        isOpen={renameDialog.isOpen}
        currentTitle={renameDialog.currentTitle}
        onConfirm={confirmRename}
        onCancel={cancelRename}
      />
    </>
  );
}


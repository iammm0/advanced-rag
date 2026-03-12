"use client";

import { ReactNode } from "react";
import Navbar from "./Navbar";

interface LayoutProps {
  children: ReactNode;
  noPadding?: boolean;
  allowScroll?: boolean; // 是否允许页面滚动
}

export default function Layout({
  children,
  noPadding = false,
  allowScroll = false,
}: LayoutProps) {

  if (allowScroll) {
    // 允许滚动的布局：整个页面可以滚动
    // 使用自然文档流，让浏览器处理滚动，确保可以滚动到底部
    return (
      <div className="min-h-screen bg-gray-100 dark:bg-gray-900 flex flex-col transition-colors safe-area-inset">
        <Navbar />
        <main
          className={`flex-1 w-full ${
            !noPadding ? "px-3 sm:px-4 md:px-6 lg:px-8 py-3 sm:py-4 md:py-6" : "py-3 sm:py-4 md:py-6"
          } pb-16 sm:pb-20 md:pb-24`}
          style={{ 
            WebkitOverflowScrolling: 'touch',
            paddingBottom: 'calc(env(safe-area-inset-bottom) + 4rem)'
          }}
        >
          {children}
        </main>
      </div>
    );
  }

  // 不允许滚动的布局：固定高度，内部滚动（用于聊天页面）
  return (
    <div className="h-screen bg-gray-100 dark:bg-gray-900 flex flex-col overflow-hidden transition-colors safe-area-inset">
      <Navbar />
      <main
        className={`flex-1 overflow-hidden ${
          !noPadding ? "px-2 sm:px-4 md:px-6 lg:px-8 py-2 sm:py-3 md:py-6" : ""
        }`}
        style={{ 
          WebkitOverflowScrolling: 'touch',
          paddingTop: 'env(safe-area-inset-top)',
          paddingBottom: 'env(safe-area-inset-bottom)'
        }}
      >
        <div className="w-full h-full">
          {children}
        </div>
      </main>
    </div>
  );
}


"use client";

import { useState, useEffect } from "react";

interface LoadingProgressBarProps {
  /** 是否显示进度条 */
  isLoading: boolean;
  /** 加载进度（0-100），如果不提供则显示不确定进度 */
  progress?: number;
  /** 加载文本 */
  text?: string;
  /** 是否显示百分比 */
  showPercentage?: boolean;
  /** 自定义样式类 */
  className?: string;
}

/**
 * 加载进度条组件
 * 支持确定进度和不确定进度两种模式
 */
export default function LoadingProgressBar({
  isLoading,
  progress,
  text = "正在加载...",
  showPercentage = false,
  className = "",
}: LoadingProgressBarProps) {
  const [displayProgress, setDisplayProgress] = useState(0);

  // 平滑更新进度
  useEffect(() => {
    if (progress !== undefined) {
      const timer = setTimeout(() => {
        setDisplayProgress(progress);
      }, 50);
      return () => clearTimeout(timer);
    } else {
      // 不确定进度模式，使用动画
      setDisplayProgress(0);
    }
  }, [progress]);

  if (!isLoading) {
    return null;
  }

  return (
    <div className={`w-full ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm text-gray-600 dark:text-gray-400">{text}</span>
        {showPercentage && progress !== undefined && (
          <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
            {Math.round(displayProgress)}%
          </span>
        )}
      </div>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        {progress !== undefined ? (
          // 确定进度模式
          <div
            className="h-full bg-blue-600 dark:bg-blue-500 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${displayProgress}%` }}
          />
        ) : (
          // 不确定进度模式（动画）
          <div className="h-full bg-blue-600 dark:bg-blue-500 rounded-full animate-pulse" style={{ width: "40%" }}>
            <div className="h-full bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" />
          </div>
        )}
      </div>
    </div>
  );
}


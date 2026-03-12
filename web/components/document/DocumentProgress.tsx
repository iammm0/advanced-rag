"use client";

import { Document } from "@/lib/api";

interface DocumentProgressProps {
  document: Document;
  className?: string;
}

export default function DocumentProgress({
  document,
  className = "",
}: DocumentProgressProps) {
  const progress = document.progress_percentage ?? 0;
  const currentStage = document.current_stage || "处理中";
  const stageDetails = document.stage_details || "";

  if (document.status !== "processing") {
    return null;
  }

  return (
    <div className={`space-y-2 ${className}`}>
      {/* 进度条 */}
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2.5 overflow-hidden">
        <div
          className="bg-blue-500 dark:bg-blue-600 h-2.5 rounded-full transition-all duration-500 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>

      {/* 进度信息 */}
      <div className="flex items-center justify-between text-sm">
        <div className="flex items-center space-x-2">
          <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-blue-600 dark:border-blue-400"></div>
          <span className="text-gray-700 dark:text-gray-300 font-medium" suppressHydrationWarning>
            {currentStage}
          </span>
        </div>
        <div className="text-gray-600 dark:text-gray-400" suppressHydrationWarning>
          {progress}%
        </div>
      </div>

      {/* 详细信息 */}
      {stageDetails && (
        <div className="text-xs text-gray-500 dark:text-gray-400" suppressHydrationWarning>
          {stageDetails}
        </div>
      )}
    </div>
  );
}

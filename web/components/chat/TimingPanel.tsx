"use client";

import { useState, useEffect } from "react";

interface StepTiming {
  step: number;
  name: string;
  startTime: number;
  endTime?: number;
}

interface TimingPanelProps {
  stepTimings: StepTiming[];
  overallStartTime: number | null;
  isActive: boolean;
}

export default function TimingPanel({ stepTimings, overallStartTime, isActive }: TimingPanelProps) {
  const [currentTime, setCurrentTime] = useState(Date.now());

  // 实时更新时间（仅在活动时）
  useEffect(() => {
    if (!isActive || !overallStartTime) return;

    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 100); // 每100ms更新一次，显示更精确的时间

    return () => clearInterval(interval);
  }, [isActive, overallStartTime]);

  // 计算整体时间
  const getOverallTime = () => {
    if (!overallStartTime) return null;
    const endTime = stepTimings.length > 0 && stepTimings.every(t => t.endTime) 
      ? Math.max(...stepTimings.map(t => t.endTime || 0))
      : currentTime;
    const totalMs = endTime - overallStartTime;
    return formatTime(totalMs);
  };

  // 格式化时间（毫秒转可读格式）
  const formatTime = (ms: number): string => {
    if (ms < 1000) return `${ms}ms`;
    const seconds = Math.floor(ms / 1000);
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    if (minutes < 60) return `${minutes}m ${remainingSeconds}s`;
    const hours = Math.floor(minutes / 60);
    const remainingMinutes = minutes % 60;
    return `${hours}h ${remainingMinutes}m ${remainingSeconds}s`;
  };

  // 计算步骤时间
  const getStepTime = (timing: StepTiming): string => {
    const endTime = timing.endTime || currentTime;
    const duration = endTime - timing.startTime;
    return formatTime(duration);
  };

  if (!overallStartTime || stepTimings.length === 0) return null;

  const overallTime = getOverallTime();
  const allStepsCompleted = stepTimings.every(t => t.endTime);

  return (
    <div className="mb-3 p-3 bg-gradient-to-br from-white/80 via-blue-50/30 to-purple-50/20 dark:from-gray-800/80 dark:via-blue-900/20 dark:to-purple-900/10 backdrop-blur-sm rounded-lg border border-gray-200 dark:border-gray-700 shadow-sm">
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          <svg className="w-4 h-4 text-gray-600 dark:text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span className="text-xs font-semibold text-gray-700 dark:text-gray-300">执行时间</span>
        </div>
        {overallTime && (
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">总计:</span>
            <span className={`text-xs font-bold ${isActive && !allStepsCompleted ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'}`}>
              {overallTime}
            </span>
          </div>
        )}
      </div>
      
      {/* 步骤时间列表 */}
      <div className="space-y-1">
        {stepTimings.map((timing) => {
          const stepTime = getStepTime(timing);
          const isCompleted = !!timing.endTime;
          const stepIsActive = !isCompleted && isActive;
          
          return (
            <div
              key={timing.step}
              className="flex items-center justify-between text-xs py-1 px-2 rounded"
            >
              <span className={`flex-1 ${stepIsActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-600 dark:text-gray-400'}`}>
                {timing.name}
              </span>
              <span className={`font-medium ${stepIsActive ? 'text-blue-600 dark:text-blue-400' : 'text-gray-700 dark:text-gray-300'}`}>
                {stepTime}
              </span>
            </div>
          );
        })}
      </div>
    </div>
  );
}


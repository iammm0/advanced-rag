"use client";

import { useEffect, useState } from "react";

interface LoadingProgressProps {
  steps: string[];
  currentStep: number;
  message?: string;
  className?: string;
  currentStepProgress?: number; // 当前步骤的进度百分比（0-100），用于更精确的进度显示
}

export default function LoadingProgress({
  steps,
  currentStep,
  message,
  className = "",
  currentStepProgress,
}: LoadingProgressProps) {
  const [displayedStep, setDisplayedStep] = useState(0);

  useEffect(() => {
    // 平滑过渡到当前步骤
    if (currentStep > displayedStep) {
      const timer = setTimeout(() => {
        setDisplayedStep(currentStep);
      }, 200);
      return () => clearTimeout(timer);
    } else if (currentStep < displayedStep) {
      setDisplayedStep(currentStep);
    }
  }, [currentStep, displayedStep]);

  // 根据步骤计算实际进度（考虑各步骤的实际耗时）
  const getStepProgress = (step: number, totalSteps: number): number => {
    if (totalSteps === 0) return 0;
    
    // 各步骤的预估耗时权重（基于实际处理时间）
    // 创建对话和保存消息较快，检索和生成回复较慢
    const stepWeights = [
      0.05,  // 步骤0: 创建对话 - 5%
      0.05,  // 步骤1: 保存消息 - 5%
      0.15,  // 步骤2: 检索知识库 - 15%
      0.05,  // 步骤3: 增强上下文 - 5%
      0.60,  // 步骤4: 生成回复 - 60%（最耗时）
      0.10,  // 步骤5: 保存回复 - 10%
    ];
    
    // 如果步骤数不匹配，使用线性权重
    const weights = stepWeights.length === totalSteps 
      ? stepWeights 
      : Array(totalSteps).fill(1 / totalSteps);
    
    let progress = 0;
    
    // 计算已完成步骤的进度
    for (let i = 0; i < step && i < weights.length; i++) {
      progress += weights[i] * 100;
    }
    
    // 当前步骤的进度（根据步骤类型和实际进度设置）
    if (step < weights.length && step < totalSteps) {
      // 如果提供了当前步骤的精确进度，使用它
      if (currentStepProgress !== undefined && step === displayedStep) {
        progress += weights[step] * (currentStepProgress / 100);
      } else {
        // 否则使用默认进度
        // 生成回复步骤（步骤4）显示较少进度，因为耗时最长，需要更多时间
        if (step === 4) {
          progress += weights[step] * 20; // 生成回复步骤完成20%（表示刚开始）
        } else if (step === 5) {
          // 保存回复步骤通常很快完成
          progress += weights[step] * 80; // 保存回复步骤完成80%
        } else {
          progress += weights[step] * 60; // 其他步骤完成60%（表示正在进行中）
        }
      }
    } else if (step >= totalSteps - 1) {
      // 如果是最后一步，显示100%
      progress = 100;
    }
    
    return Math.min(Math.max(progress, 0), 100);
  };

  const progress = steps.length > 0 
    ? getStepProgress(displayedStep, steps.length)
    : 0;

  return (
    <div className={`flex flex-col items-center justify-center ${className}`}>
      <div className="w-full max-w-md space-y-3 sm:space-y-4 px-2">
        {/* 进度条 */}
        <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5 sm:h-2 overflow-hidden">
          <div
            className="bg-blue-500 dark:bg-blue-600 h-1.5 sm:h-2 rounded-full transition-all duration-300 ease-out"
            style={{ width: `${progress}%` }}
          />
        </div>

        {/* 当前步骤信息 */}
        <div className="text-center">
          <div className="flex items-center justify-center gap-1.5 sm:gap-2 mb-1.5 sm:mb-2">
            <div className="animate-spin rounded-full h-4 w-4 sm:h-5 sm:w-5 border-b-2 border-blue-600 dark:border-blue-400"></div>
            <p className="text-xs sm:text-sm text-gray-700 dark:text-gray-200 font-medium" suppressHydrationWarning>
              {steps[displayedStep] || message || "加载中..."}
            </p>
          </div>
          
          {/* 步骤列表 */}
          {steps.length > 1 && (
            <div className="mt-3 sm:mt-4 space-y-1 text-xs sm:text-sm text-gray-500 dark:text-gray-400">
              {steps.map((step, index) => (
                <div
                  key={index}
                  className={`flex items-center gap-1.5 sm:gap-2 transition-opacity duration-300 ${
                    index <= displayedStep ? "opacity-100" : "opacity-40"
                  }`}
                >
                  <div
                    className={`w-1.5 h-1.5 sm:w-2 sm:h-2 rounded-full transition-all duration-300 flex-shrink-0 ${
                      index < displayedStep
                        ? "bg-green-500 dark:bg-green-400"
                        : index === displayedStep
                        ? "bg-blue-500 dark:bg-blue-400 animate-pulse"
                        : "bg-gray-300 dark:bg-gray-600"
                    }`}
                  />
                  <span className="text-left" suppressHydrationWarning>{step}</span>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
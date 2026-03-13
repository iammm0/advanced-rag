"use client";

import { useState, useEffect } from "react";

interface AgentStatus {
  agent_type: string;
  status: "pending" | "running" | "completed" | "error" | "skipped";
  progress?: number;
  current_step?: string;
  details?: string;
  started_at?: number;
  completed_at?: number;
  reason?: string;
}

interface AgentStatusPanelProps {
  agents: AgentStatus[];
}

const agentTitles: Record<string, string> = {
  coordinator: "协调型Agent",
  document_retrieval: "文档检索专家",
  concept_explanation: "概念解释专家",
  summary: "总结专家",
  critic: "批判性思维专家",
};

const agentDescriptions: Record<string, string> = {
  coordinator: "分析用户问题，规划研究任务，协调各Agent工作",
  document_retrieval: "从知识库中检索相关文档和资料",
  concept_explanation: "深入解释专业概念和理论",
  summary: "总结和归纳各Agent的研究结果",
  critic: "验证信息准确性，检查幻觉，提供批判性分析",
};

// Agent工作流程顺序（包含所有Agent）
const agentWorkflowOrder = [
  "coordinator",
  "document_retrieval",
  "concept_explanation",
  "critic",
  "summary",
];

// 获取所有Agent的完整列表（用于确保所有Agent都显示）
const getAllAgents = (): Array<{ type: string; title: string; description: string }> => {
  return agentWorkflowOrder.map(type => ({
    type,
    title: agentTitles[type] || type,
    description: agentDescriptions[type] || ""
  }));
};

export default function AgentStatusPanel({ agents }: AgentStatusPanelProps) {
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [isExpanded, setIsExpanded] = useState(false); // 默认折叠，节省空间

  // 实时更新时间（用于显示运行时长）
  useEffect(() => {
    const hasRunningAgent = agents.some(a => a.status === "running");
    if (!hasRunningAgent) return;

    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000); // 每1秒更新一次，减少更新频率

    return () => clearInterval(interval);
  }, [agents]);
  
  // 格式化时间
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

  // 获取所有Agent的完整列表
  const allAgentsList = getAllAgents();
  
  // 创建Agent状态映射
  const agentStatusMap = new Map(agents.map(a => [a.agent_type, a]));
  
  // 确保所有Agent都显示（合并已有状态和默认状态）
  const sortedAgents = allAgentsList.map((agentInfo) => {
    const existingStatus = agentStatusMap.get(agentInfo.type);
    if (existingStatus) {
      return existingStatus;
    }
    // 如果Agent还没有状态，创建默认的pending状态
    return {
      agent_type: agentInfo.type,
      status: "pending" as const,
      progress: undefined,
      current_step: undefined,
      details: undefined,
      started_at: undefined,
      completed_at: undefined,
    };
  });

  // 计算总体进度（基于所有Agent）
  const completedCount = sortedAgents.filter(a => a.status === "completed").length;
  const totalCount = sortedAgents.length;
  const overallProgress = totalCount > 0 ? (completedCount / totalCount) * 100 : 0;

  // 获取当前正在执行的Agent
  const runningAgent = sortedAgents.find(a => a.status === "running");
  const currentStep = runningAgent 
    ? `${agentTitles[runningAgent.agent_type] || runningAgent.agent_type}正在工作...`
    : completedCount === totalCount 
      ? "所有Agent已完成工作" 
      : "等待开始...";

  // 获取活跃的Agent（正在运行或刚完成的）
  const activeAgents = sortedAgents.filter(a => 
    a.status === "running" || 
    (a.status === "completed" && a.completed_at && (currentTime - a.completed_at < 5000))
  );

  return (
    <div className="mb-3 p-4 bg-gradient-to-br from-white/80 via-blue-50/30 to-purple-50/20 dark:from-gray-800/80 dark:via-blue-900/20 dark:to-purple-900/10 backdrop-blur-sm rounded-xl border border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-xl transition-all duration-300 relative overflow-hidden">
      {/* 背景装饰动画 */}
      {runningAgent && (
        <div className="absolute inset-0 opacity-5">
          <div className="absolute top-0 left-0 w-64 h-64 bg-blue-500 rounded-full blur-3xl animate-pulse"></div>
          <div className="absolute bottom-0 right-0 w-64 h-64 bg-purple-500 rounded-full blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        </div>
      )}
      
      {/* 紧凑的头部 */}
      <div className="flex items-center justify-between mb-3 relative z-10">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          {/* 进度条 - 增强视觉效果 */}
          <div className="flex-1 min-w-0">
            <div className="w-full bg-gray-200/50 dark:bg-gray-700/50 rounded-full h-2 overflow-hidden shadow-inner">
              <div
                className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 transition-all duration-500 ease-out relative overflow-hidden"
                style={{ width: `${overallProgress}%` }}
              >
                {/* 进度条光效动画 */}
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-shimmer" 
                     style={{ 
                       width: '50%',
                       animation: 'shimmer 2s infinite',
                       transform: 'translateX(-100%)'
                     }}></div>
              </div>
            </div>
          </div>
          
          {/* 当前状态 - 增强视觉效果 */}
          <div className="flex items-center gap-2 ml-2 flex-shrink-0">
            {runningAgent ? (
              <div className="flex items-center gap-2 px-2 py-1 bg-blue-100/80 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-800">
                <div className="relative">
                  <div className="w-2 h-2 rounded-full bg-blue-500 animate-ping absolute"></div>
                  <div className="w-2 h-2 rounded-full bg-blue-600 relative"></div>
                </div>
                <span className="text-xs text-blue-700 dark:text-blue-300 font-semibold truncate max-w-[120px] animate-pulse">
                  {agentTitles[runningAgent.agent_type] || runningAgent.agent_type}
                </span>
              </div>
            ) : completedCount === totalCount ? (
              <div className="flex items-center gap-1.5 px-2 py-1 bg-green-100/80 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-800">
                <svg className="w-3 h-3 text-green-600 dark:text-green-400 animate-bounce" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                </svg>
                <span className="text-xs text-green-600 dark:text-green-400 font-semibold">完成</span>
              </div>
            ) : (
              <span className="text-xs text-gray-500 dark:text-gray-400 px-2 py-1 bg-gray-100/50 dark:bg-gray-700/50 rounded-lg">等待中</span>
            )}
            <div className="px-2 py-1 bg-gray-100/50 dark:bg-gray-700/50 rounded-lg">
              <span className="text-xs text-gray-700 dark:text-gray-300 font-medium">
                {completedCount}/{totalCount}
              </span>
            </div>
          </div>
        </div>
        
        {/* 展开/折叠按钮 - 增强视觉效果 */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="ml-2 p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-all duration-200 flex-shrink-0 hover:scale-110"
          title={isExpanded ? "折叠" : "展开详情"}
        >
          <svg 
            className={`w-4 h-4 text-gray-600 dark:text-gray-300 transition-transform duration-300 ${isExpanded ? 'rotate-180' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>
      
      {/* 当前执行步骤（仅在运行中时显示，且未展开时） */}
      {!isExpanded && runningAgent && runningAgent.current_step && (
        <div className="mt-3 pt-3 border-t border-gray-200/50 dark:border-gray-700/50 relative z-10">
          <div className="flex items-center gap-2 animate-fade-in">
            <div className="flex items-center gap-1.5">
              <div className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse"></div>
              <div className="w-1.5 h-1.5 rounded-full bg-purple-500 animate-pulse" style={{ animationDelay: '0.2s' }}></div>
              <div className="w-1.5 h-1.5 rounded-full bg-pink-500 animate-pulse" style={{ animationDelay: '0.4s' }}></div>
            </div>
            <span className="text-xs text-gray-700 dark:text-gray-300 truncate font-medium">
              {runningAgent.current_step}
            </span>
          </div>
        </div>
      )}

      {/* Agent详细列表（可折叠，紧凑设计） */}
      {isExpanded && (
        <div className="mt-2 space-y-1.5">
          {sortedAgents.map((agent, index) => {
            const title = agentTitles[agent.agent_type] || agent.agent_type;
            const isActive = agent.status === "running";
            const isCompleted = agent.status === "completed";
            const isError = agent.status === "error";
            const isSkipped = agent.status === "skipped";

            // 计算运行时长
            let duration = "";
            if (agent.started_at) {
              const endTime = agent.completed_at || currentTime;
              const seconds = Math.floor((endTime - agent.started_at) / 1000);
              if (seconds > 0) {
                duration = `${seconds}s`;
              }
            }

            return (
              <div
                key={agent.agent_type}
                className={`flex items-center gap-2 py-2 px-3 rounded-lg transition-all duration-300 relative overflow-hidden group ${
                  isActive
                    ? "bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-900/30 dark:to-purple-900/20 border-l-4 border-blue-500 shadow-md scale-[1.02]"
                    : isCompleted
                    ? "bg-gradient-to-r from-green-50/70 to-emerald-50/50 dark:from-green-900/15 dark:to-emerald-900/10 border-l-2 border-green-500"
                    : isError
                    ? "bg-gradient-to-r from-red-50/70 to-rose-50/50 dark:from-red-900/15 dark:to-rose-900/10 border-l-2 border-red-500"
                    : isSkipped
                    ? "opacity-50 border-l-2 border-gray-300 dark:border-gray-600"
                    : "border-l-2 border-transparent hover:bg-gray-50/50 dark:hover:bg-gray-700/30"
                }`}
              >
                {/* 活跃Agent的背景光效 */}
                {isActive && (
                  <div className="absolute inset-0 bg-gradient-to-r from-blue-400/10 via-purple-400/10 to-pink-400/10 animate-pulse"></div>
                )}
                {/* 状态图标（增强视觉效果） */}
                <div className="flex-shrink-0 w-5 h-5 relative z-10">
                  {isCompleted ? (
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-green-400 to-green-600 flex items-center justify-center shadow-lg animate-scale-in">
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                  ) : isError ? (
                    <div className="w-5 h-5 rounded-full bg-gradient-to-br from-red-400 to-red-600 flex items-center justify-center shadow-lg animate-shake">
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                  ) : isActive ? (
                    <div className="relative">
                      <div className="w-5 h-5 rounded-full bg-gradient-to-br from-blue-400 to-purple-600 flex items-center justify-center shadow-lg animate-pulse">
                        <svg className="w-3 h-3 text-white animate-spin" fill="none" viewBox="0 0 24 24">
                          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                        </svg>
                      </div>
                      {/* 外圈光晕 */}
                      <div className="absolute inset-0 rounded-full bg-blue-400/30 animate-ping"></div>
                    </div>
                  ) : isSkipped ? (
                    <div className="w-5 h-5 rounded-full bg-gray-400 dark:bg-gray-600 flex items-center justify-center opacity-60">
                      <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </div>
                  ) : (
                    <div className="w-5 h-5 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center border-2 border-gray-400 dark:border-gray-500">
                      <div className="w-2 h-2 rounded-full bg-gray-500 dark:bg-gray-400"></div>
                    </div>
                  )}
                </div>

                {/* Agent名称和状态 */}
                <div className="flex-1 min-w-0 flex items-center justify-between gap-2">
                  <div className="flex-1 min-w-0">
                    <span className={`text-xs font-medium truncate ${
                      isActive
                        ? "text-blue-700 dark:text-blue-300"
                        : isCompleted
                        ? "text-green-700 dark:text-green-300"
                        : isError
                        ? "text-red-700 dark:text-red-300"
                        : isSkipped
                        ? "text-gray-400 dark:text-gray-500 line-through"
                        : "text-gray-600 dark:text-gray-400"
                    }`}>
                      {title}
                    </span>
                    {isActive && agent.current_step && (
                      <div className="mt-0.5">
                        <span className="text-[10px] text-gray-500 dark:text-gray-400 truncate block">
                          {agent.current_step}
                        </span>
                      </div>
                    )}
                  </div>
                  
                  {/* 右侧信息 */}
                  <div className="flex items-center gap-1.5 flex-shrink-0">
                    {duration && (
                      <span className="text-[10px] text-gray-500 dark:text-gray-400">
                        {duration}
                      </span>
                    )}
                    {agent.progress !== undefined && isActive && (
                      <div className="w-12 h-1 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                        <div
                          className="h-full bg-blue-500 transition-all duration-300"
                          style={{ width: `${agent.progress}%` }}
                        />
                      </div>
                    )}
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}


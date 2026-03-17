"use client";

import { useState } from "react";
import type { RAGEvaluationMetrics } from "@/types/chat";

/** 阈值：与评测层文档一致，用于异常标注 */
const THRESHOLD_RESPONSE_MS = 500;
const THRESHOLD_RECALL_LOW = 80; // 召回条数过少时的提示（条数 < 某值可提示）
const THRESHOLD_RETRIEVAL_MS = 300; // 检索耗时告警（毫秒）

interface RAGEvaluationPanelProps {
  /** 评测指标（可选；无则仅根据 sources 展示召回数） */
  metrics?: RAGEvaluationMetrics | null;
  /** 来源条数（当无 metrics 时用此展示召回数） */
  sourceCount?: number;
}

function RAGEvaluationPanel({ metrics, sourceCount = 0 }: RAGEvaluationPanelProps) {
  const [expanded, setExpanded] = useState(false);

  const retrievalTriggered = metrics?.retrieval_triggered ?? (sourceCount > 0);
  const count = metrics?.source_count ?? sourceCount;
  const contextLen = metrics?.context_length ?? 0;
  const retrievalMs = metrics?.retrieval_time_ms;
  const responseMs = metrics?.response_time_ms;
  const ttftMs = metrics?.time_to_first_token_ms;
  const warnings = metrics?.warnings ?? [];

  // 根据阈值生成告警文案
  const derivedWarnings: string[] = [...warnings];
  if (responseMs != null && responseMs > THRESHOLD_RESPONSE_MS) {
    derivedWarnings.push(`响应时间 > ${THRESHOLD_RESPONSE_MS}ms`);
  }
  if (retrievalMs != null && retrievalMs > THRESHOLD_RETRIEVAL_MS) {
    derivedWarnings.push(`检索耗时 > ${THRESHOLD_RETRIEVAL_MS}ms`);
  }
  if (retrievalTriggered && count < 3 && count >= 0) {
    derivedWarnings.push("召回条数较少");
  }

  const hasAnyMetric =
    retrievalTriggered ||
    count > 0 ||
    contextLen > 0 ||
    retrievalMs != null ||
    responseMs != null ||
    ttftMs != null ||
    derivedWarnings.length > 0;

  if (!hasAnyMetric) return null;

  return (
    <div className="mt-2 w-full border border-gray-200 dark:border-gray-600 rounded-lg overflow-hidden bg-gray-50 dark:bg-gray-800/60">
      <button
        type="button"
        onClick={() => setExpanded((e) => !e)}
        className="w-full px-3 py-2 flex items-center justify-between text-left text-xs font-medium text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700/60 transition-colors"
      >
        <span className="flex items-center gap-2">
          <span className="text-gray-500 dark:text-gray-400">RAG 评测指标</span>
          {derivedWarnings.length > 0 && (
            <span className="px-1.5 py-0.5 rounded bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300 text-[10px]">
              {derivedWarnings.length} 项异常
            </span>
          )}
        </span>
        <svg
          className={`w-4 h-4 text-gray-400 transition-transform ${expanded ? "rotate-180" : ""}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {expanded && (
        <div className="px-3 py-2 border-t border-gray-200 dark:border-gray-600 text-xs text-gray-600 dark:text-gray-400 space-y-1.5">
          <div className="grid grid-cols-[auto_1fr] gap-x-3 gap-y-1">
            <span className="text-gray-500 dark:text-gray-500">是否检索</span>
            <span>{retrievalTriggered ? "是" : "否"}</span>
            <span className="text-gray-500 dark:text-gray-500">召回条数</span>
            <span>{count}</span>
            <span className="text-gray-500 dark:text-gray-500">上下文长度</span>
            <span>{contextLen > 0 ? `${contextLen} 字符` : "—"}</span>
            {retrievalMs != null && (
              <>
                <span className="text-gray-500 dark:text-gray-500">检索耗时</span>
                <span>{retrievalMs} ms</span>
              </>
            )}
            {ttftMs != null && (
              <>
                <span className="text-gray-500 dark:text-gray-500">首 token 耗时</span>
                <span>{ttftMs} ms</span>
              </>
            )}
            {responseMs != null && (
              <>
                <span className="text-gray-500 dark:text-gray-500">总响应耗时</span>
                <span>{responseMs} ms</span>
              </>
            )}
          </div>
          {derivedWarnings.length > 0 && (
            <div className="pt-1.5 mt-1.5 border-t border-gray-200 dark:border-gray-600">
              <div className="font-medium text-amber-700 dark:text-amber-400 mb-1">异常 / 告警</div>
              <ul className="list-disc list-inside space-y-0.5 text-amber-700/90 dark:text-amber-300/90">
                {derivedWarnings.map((w, i) => (
                  <li key={i}>{w}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default RAGEvaluationPanel;

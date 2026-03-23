"use client";

import { useEffect, useRef, useState } from "react";
import { useDeepResearchAgents } from "@/contexts/DeepResearchAgentsContext";
import ConfigModalFrame from "./ConfigModalFrame";
import Toast, { ToastType } from "@/components/ui/Toast";

export default function DeepResearchConfigModal({
  open,
  onClose,
  focusAgentType,
}: {
  open: boolean;
  onClose: () => void;
  focusAgentType?: string | null;
}) {
  const { agents, draft, modelNames, loading, saving, setDraftField, saveAll, resetPromptBuiltin, dirtyAgentTypes } =
    useDeepResearchAgents();
  const [toast, setToast] = useState<{ open: boolean; message: string; type: ToastType }>({
    open: false,
    message: "",
    type: "info",
  });

  const coordinatorRef = useRef<HTMLDivElement>(null);
  const cardRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (!open || !focusAgentType) return;
    const t = window.setTimeout(() => {
      if (focusAgentType === "coordinator") {
        coordinatorRef.current?.scrollIntoView({ behavior: "smooth", block: "center" });
      } else {
        cardRefs.current[focusAgentType]?.scrollIntoView({ behavior: "smooth", block: "center" });
      }
    }, 120);
    return () => clearTimeout(t);
  }, [open, focusAgentType]);

  if (!open) return null;

  const coordinator = agents.find((a) => a.agent_type === "coordinator");
  const experts = agents.filter((a) => a.role === "expert");

  const handleSaveAll = async () => {
    const ok = await saveAll();
    if (ok) {
      setToast({ open: true, message: "已全部保存", type: "success" });
      onClose();
    } else {
      setToast({ open: true, message: "保存失败", type: "error" });
    }
  };

  return (
    <>
      <ConfigModalFrame
        open
        panelClassName="max-w-4xl"
        title="深度研究 · 多智能体"
        subtitle="协调器与各子智能体统一在此编辑；底部「保存全部」一次性提交所有变更。"
        onClose={onClose}
        footer={
          <div className="flex flex-wrap items-center justify-between gap-2">
            <span className="text-xs text-gray-500 dark:text-gray-400">
              {dirtyAgentTypes.length > 0 ? `未保存：${dirtyAgentTypes.length} 项` : "无未保存更改"}
            </span>
            <div className="flex gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100"
              >
                取消
              </button>
              <button
                type="button"
                disabled={saving || loading || dirtyAgentTypes.length === 0}
                onClick={() => handleSaveAll()}
                className="px-3 py-2 rounded-lg text-sm bg-blue-600 text-white disabled:opacity-50"
              >
                {saving ? "保存中…" : "保存全部"}
              </button>
            </div>
          </div>
        }
      >
        {loading ? (
          <p className="text-sm text-gray-500">加载中…</p>
        ) : (
          <div className="space-y-6 max-h-[min(70vh,640px)] overflow-y-auto pr-1">
            {coordinator && draft.coordinator ? (
              <div ref={coordinatorRef} className="rounded-lg border border-indigo-200 dark:border-indigo-800 bg-indigo-50/50 dark:bg-indigo-950/20 p-4">
                <div className="text-sm font-semibold text-indigo-900 dark:text-indigo-100 mb-3">
                  {coordinator.label}
                  <span className="ml-2 text-xs font-normal text-indigo-700/80 dark:text-indigo-300/80">协调 · coordinator</span>
                </div>
                <AgentFields
                  agent={coordinator}
                  row={draft.coordinator}
                  modelNames={modelNames}
                  lockedEnable
                  onField={setDraftField}
                  onResetPrompt={() => resetPromptBuiltin("coordinator")}
                  saving={saving}
                  hideTitle
                />
              </div>
            ) : null}

            <div>
              <div className="text-xs font-semibold text-gray-600 dark:text-gray-300 mb-2">子智能体（专家）</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {experts.map((a) => {
                  const row = draft[a.agent_type];
                  if (!row) return null;
                  const isFocus = Boolean(focusAgentType && focusAgentType === a.agent_type);
                  return (
                    <div
                      key={a.agent_type}
                      ref={(el) => {
                        cardRefs.current[a.agent_type] = el;
                      }}
                      className={`rounded-lg border p-3 ${
                        isFocus
                          ? "border-blue-400 dark:border-blue-500 ring-2 ring-blue-200 dark:ring-blue-900/50"
                          : "border-gray-200 dark:border-gray-700"
                      } bg-white dark:bg-gray-900/50`}
                    >
                      <div className="text-xs font-medium text-gray-800 dark:text-gray-100 mb-2">
                        {a.label}
                        <span className="ml-1.5 text-[10px] font-normal text-gray-500">{a.agent_type}</span>
                      </div>
                      <AgentFields
                        agent={a}
                        row={row}
                        modelNames={modelNames}
                        lockedEnable={false}
                        onField={setDraftField}
                        onResetPrompt={() => resetPromptBuiltin(a.agent_type)}
                        saving={saving}
                        hideTitle
                      />
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </ConfigModalFrame>
      <Toast
        isOpen={toast.open}
        message={toast.message}
        type={toast.type}
        duration={3500}
        onClose={() => setToast((t) => ({ ...t, open: false }))}
      />
    </>
  );
}

function AgentFields({
  agent,
  row,
  modelNames,
  lockedEnable,
  onField,
  onResetPrompt,
  saving,
  hideTitle,
}: {
  agent: { agent_type: string; label: string; builtin_system_prompt: string };
  row: { inference_model: string; embedding_model: string; system_prompt: string; enabled: boolean };
  modelNames: string[];
  lockedEnable: boolean;
  onField: (
    agentType: string,
    field: "inference_model" | "embedding_model" | "system_prompt" | "enabled",
    value: string | boolean
  ) => void;
  onResetPrompt: () => void;
  saving: boolean;
  hideTitle?: boolean;
}) {
  return (
    <div className="space-y-3 text-sm">
      {!hideTitle ? (
        <div className="text-xs font-medium text-gray-800 dark:text-gray-100 mb-1">
          {agent.label}
          <span className="ml-1.5 text-[10px] font-normal text-gray-500">{agent.agent_type}</span>
        </div>
      ) : null}
      <label className="flex items-center justify-between gap-2">
        <span className="text-xs text-gray-600 dark:text-gray-300">启用</span>
        <input
          type="checkbox"
          disabled={lockedEnable || saving}
          checked={row.enabled}
          onChange={(e) => onField(agent.agent_type, "enabled", e.target.checked)}
        />
      </label>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        <div>
          <span className="text-xs text-gray-500 block mb-0.5">推理模型</span>
          <input
            list={`m-${agent.agent_type}`}
            className="w-full px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-xs"
            value={row.inference_model}
            onChange={(e) => onField(agent.agent_type, "inference_model", e.target.value)}
            placeholder="留空=默认"
          />
          <datalist id={`m-${agent.agent_type}`}>
            {modelNames.map((n) => (
              <option key={n} value={n} />
            ))}
          </datalist>
        </div>
        <div>
          <span className="text-xs text-gray-500 block mb-0.5">向量化模型</span>
          <input
            list={`e-${agent.agent_type}`}
            className="w-full px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-xs"
            value={row.embedding_model}
            onChange={(e) => onField(agent.agent_type, "embedding_model", e.target.value)}
            placeholder="可选"
          />
          <datalist id={`e-${agent.agent_type}`}>
            {modelNames.map((n) => (
              <option key={n} value={n} />
            ))}
          </datalist>
        </div>
      </div>
      <div>
        <span className="text-xs text-gray-500">系统提示词</span>
        <textarea
          className="mt-1 w-full min-h-[88px] px-2 py-1.5 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-xs font-mono"
          value={row.system_prompt}
          onChange={(e) => onField(agent.agent_type, "system_prompt", e.target.value)}
          placeholder="留空使用内置"
        />
        <details className="mt-1 text-[10px] text-gray-500">
          <summary className="cursor-pointer">内置提示（只读）</summary>
          <pre className="mt-1 p-2 rounded bg-gray-50 dark:bg-gray-800/80 max-h-24 overflow-auto whitespace-pre-wrap">
            {agent.builtin_system_prompt || "—"}
          </pre>
        </details>
      </div>
      <button
        type="button"
        disabled={saving}
        onClick={onResetPrompt}
        className="text-xs px-2 py-1 rounded bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200"
      >
        恢复内置提示词
      </button>
    </div>
  );
}

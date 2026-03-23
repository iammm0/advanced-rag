"use client";

import { useDeepResearchAgents } from "@/contexts/DeepResearchAgentsContext";
import Toast, { ToastType } from "@/components/ui/Toast";
import { useState } from "react";

/** 备用：与深度研究弹窗同源数据 */
export default function MultiAgentSettingsPanel() {
  const { agents, draft, modelNames, loading, saving, setDraftField, saveAgent, resetPromptBuiltin } =
    useDeepResearchAgents();
  const [toast, setToast] = useState<{ isOpen: boolean; message: string; type: ToastType }>({
    isOpen: false,
    message: "",
    type: "info",
  });

  const showToast = (message: string, type: ToastType) => setToast({ isOpen: true, message, type });

  if (loading && agents.length === 0) {
    return (
      <div className="rounded-xl border border-gray-200 dark:border-gray-700 p-6 text-sm text-gray-500 dark:text-gray-400">
        正在加载多智能体配置…
      </div>
    );
  }

  return (
    <>
      <div className="space-y-3">
        <p className="text-xs text-gray-500 dark:text-gray-400">
          以下为与弹窗相同的数据源；每项可单独保存。主入口仍为架构图节点弹窗中的「保存全部」。
        </p>

        <div className="grid grid-cols-1 gap-4">
          {agents.map((a) => {
            const row = draft[a.agent_type];
            if (!row) return null;
            const locked = a.enable_locked;
            return (
              <div
                key={a.agent_type}
                className="rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 p-4 min-w-0"
              >
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-2 mb-3">
                  <div>
                    <div className="text-sm font-medium text-gray-900 dark:text-gray-100">
                      {a.label}
                      <span className="ml-2 text-xs font-normal text-gray-500 dark:text-gray-400">
                        {a.role === "coordinator" ? "协调" : "专家"} · {a.agent_type}
                      </span>
                    </div>
                  </div>
                  <label className="flex items-center gap-2 text-xs text-gray-600 dark:text-gray-300 shrink-0">
                    <span>启用</span>
                    <input
                      type="checkbox"
                      disabled={locked || saving}
                      checked={row.enabled}
                      onChange={(e) => setDraftField(a.agent_type, "enabled", e.target.checked)}
                    />
                    {locked ? <span className="text-gray-400">（协调器必选）</span> : null}
                  </label>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">推理模型</label>
                    <input
                      list={`models-${a.agent_type}`}
                      className="w-full px-3 py-2 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100"
                      value={row.inference_model}
                      onChange={(e) => setDraftField(a.agent_type, "inference_model", e.target.value)}
                      placeholder="留空=默认 / 对话模型"
                    />
                    <datalist id={`models-${a.agent_type}`}>
                      {modelNames.map((name) => (
                        <option key={name} value={name} />
                      ))}
                    </datalist>
                  </div>
                  <div>
                    <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">向量化模型（可选）</label>
                    <input
                      list={`emb-${a.agent_type}`}
                      className="w-full px-3 py-2 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100"
                      value={row.embedding_model}
                      onChange={(e) => setDraftField(a.agent_type, "embedding_model", e.target.value)}
                      placeholder="通常留空"
                    />
                    <datalist id={`emb-${a.agent_type}`}>
                      {modelNames.map((name) => (
                        <option key={name} value={name} />
                      ))}
                    </datalist>
                  </div>
                </div>

                <div className="mt-3">
                  <label className="block text-xs text-gray-500 dark:text-gray-400 mb-1">系统提示词（覆盖内置）</label>
                  <textarea
                    className="w-full min-h-[120px] px-3 py-2 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 font-mono"
                    value={row.system_prompt}
                    onChange={(e) => setDraftField(a.agent_type, "system_prompt", e.target.value)}
                    placeholder="留空表示使用下方内置文案"
                  />
                  <details className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                    <summary className="cursor-pointer select-none">查看内置提示词（只读）</summary>
                    <pre className="mt-2 p-2 rounded bg-gray-50 dark:bg-gray-800/80 overflow-x-auto whitespace-pre-wrap max-h-40">
                      {a.builtin_system_prompt || "（无）"}
                    </pre>
                  </details>
                </div>

                <div className="mt-3 flex flex-wrap gap-2">
                  <button
                    type="button"
                    disabled={saving}
                    onClick={async () => {
                      const ok = await saveAgent(a.agent_type);
                      showToast(ok ? "已保存" : "保存失败", ok ? "success" : "error");
                    }}
                    className="px-3 py-2 rounded-lg text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
                  >
                    {saving ? "保存中…" : "保存此项"}
                  </button>
                  <button
                    type="button"
                    disabled={saving}
                    onClick={async () => {
                      const ok = await resetPromptBuiltin(a.agent_type);
                      showToast(ok ? "已恢复内置提示词" : "失败", ok ? "success" : "error");
                    }}
                    className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-60"
                  >
                    恢复内置提示词
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <Toast
        isOpen={toast.isOpen}
        message={toast.message}
        type={toast.type}
        duration={4000}
        onClose={() => setToast((t) => ({ ...t, isOpen: false }))}
      />
    </>
  );
}

"use client";

import { useRuntimeSettings } from "@/contexts/RuntimeSettingsContext";
import Toast, { ToastType } from "@/components/ui/Toast";
import { useState } from "react";
import type { RuntimeMode } from "@/lib/api";

/** 备用：完整运行时表单（与架构图弹窗共用同一份 Context 数据） */
export default function RuntimeSettingsPanel() {
  const {
    config,
    loading,
    saving,
    error,
    refresh,
    applyPreset,
    saveModules,
    saveParams,
    setLocalConfig,
  } = useRuntimeSettings();
  const [toast, setToast] = useState<{ isOpen: boolean; message: string; type: ToastType }>({
    isOpen: false,
    message: "",
    type: "info",
  });

  const showToast = (message: string, type: ToastType) => setToast({ isOpen: true, message, type });

  const updateModuleToggle = async (key: string, value: boolean) => {
    const ok = await saveModules({ [key]: value });
    showToast(ok === true ? "已保存（自定义）" : "保存失败", ok === true ? "success" : "error");
  };

  const updateParam = async (key: string, raw: string) => {
    const n = Number(raw);
    const v = raw.trim() === "" ? undefined : Number.isFinite(n) ? n : raw;
    const ok = await saveParams({ [key]: v });
    showToast(ok === true ? "已保存（自定义）" : "保存失败", ok === true ? "success" : "error");
  };

  const onApplyPreset = async (mode: RuntimeMode) => {
    const ok = await applyPreset(mode);
    showToast(
      ok === true ? `已切换为${mode === "low" ? "低配" : mode === "high" ? "高配" : "自定义"}模式` : "保存失败",
      ok === true ? "success" : "error"
    );
  };

  return (
    <>
      <div
        id="config-runtime-pipeline"
        className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4 min-w-0 flex flex-col scroll-mt-24"
      >
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="text-sm font-semibold text-gray-800 dark:text-gray-100">性能与流水线（备用表单）</div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
              与架构图弹窗操作同一套配置；亦可在此批量查看与修改。
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2 shrink-0">
            <button
              type="button"
              disabled={saving}
              onClick={() => refresh().then(() => showToast("已刷新", "success"))}
              className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-60"
            >
              重新加载
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => onApplyPreset("low")}
              className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-60"
            >
              低配
            </button>
            <button
              type="button"
              disabled={saving}
              onClick={() => onApplyPreset("high")}
              className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-60"
            >
              高配
            </button>
          </div>
        </div>

        {error && (
          <div className="mt-3 p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800 text-sm">
            {error}
          </div>
        )}

        {loading && !config ? (
          <div className="mt-3 text-sm text-gray-500 dark:text-gray-400">正在加载运行时配置…</div>
        ) : null}

        {config ? (
          <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 min-h-0">
            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 min-w-0">
              <div className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2 break-words">
                当前模式：{config.mode}
                {config.updated_at ? (
                  <span className="block sm:inline sm:ml-2 mt-1 sm:mt-0 font-normal text-gray-500 dark:text-gray-400">
                    更新：{config.updated_at}
                  </span>
                ) : null}
              </div>
              <div className="space-y-2 text-sm">
                {[
                  ["kg_extract_enabled", "图谱构建（入库三元组抽取）"],
                  ["kg_retrieve_enabled", "图谱检索（查询阶段）"],
                  ["rerank_enabled", "重排（CrossEncoder）"],
                  ["query_analyze_enabled", "查询分析（是否需要检索）"],
                  ["ocr_image_enabled", "OCR（图片/扫描件）"],
                  ["table_parse_enabled", "表格解析增强"],
                ].map(([k, label]) => (
                  <label
                    key={k}
                    id={`config-mod-${k}`}
                    className="flex flex-col gap-1.5 min-[420px]:flex-row min-[420px]:items-center min-[420px]:justify-between min-w-0 scroll-mt-24"
                  >
                    <span className="text-gray-700 dark:text-gray-200 min-w-0 flex-1 break-words min-[420px]:pr-2">{label}</span>
                    <input
                      type="checkbox"
                      disabled={saving}
                      checked={Boolean(config.modules?.[k])}
                      onChange={(e) => updateModuleToggle(k, e.target.checked)}
                      className="shrink-0 self-start min-[420px]:self-auto"
                    />
                  </label>
                ))}
                <div className="text-xs text-gray-500 dark:text-gray-400 pt-1">
                  注意：embedding（向量化）为基础能力，系统会强制保持开启。
                </div>
              </div>
            </div>

            <div className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 min-w-0">
              <div className="text-xs font-semibold text-gray-700 dark:text-gray-200 mb-2">高级参数</div>
              <div className="grid grid-cols-1 min-[480px]:grid-cols-2 gap-2 text-sm">
                {[
                  ["kg_concurrency", "图谱并发"],
                  ["kg_chunk_timeout_s", "图谱单块超时(s)"],
                  ["kg_max_chunks", "图谱最大处理块数(0不限)"],
                  ["embedding_batch_size", "向量化batch"],
                  ["embedding_concurrency", "向量化并发(预留)"],
                  ["ocr_concurrency", "OCR并发(预留)"],
                ].map(([k, label]) => (
                  <label
                    key={k}
                    id={`config-param-${k}`}
                    className="flex flex-col gap-1 min-[360px]:flex-row min-[360px]:items-center min-[360px]:justify-between gap-x-2 min-w-0 scroll-mt-24"
                  >
                    <span className="text-gray-600 dark:text-gray-300 min-w-0 shrink break-words">{label}</span>
                    <input
                      className="w-full min-[360px]:w-24 min-[480px]:w-28 max-w-full min-w-0 px-2 py-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 shrink-0"
                      disabled={saving}
                      value={String(config.params?.[k] ?? "")}
                      onChange={(e) => {
                        setLocalConfig((prev) =>
                          prev ? { ...prev, params: { ...(prev.params || {}), [k]: e.target.value } } : prev
                        );
                      }}
                      onBlur={(e) => updateParam(k, e.target.value)}
                      placeholder="留空=默认"
                    />
                  </label>
                ))}
              </div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                参数修改会切换到 custom 模式并立即生效；部分并发项目前仅预留。
              </div>
            </div>
          </div>
        ) : null}
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

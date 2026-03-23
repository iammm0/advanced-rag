"use client";

import { useEffect, useState } from "react";
import { useRuntimeSettings } from "@/contexts/RuntimeSettingsContext";
import ConfigModalFrame from "./ConfigModalFrame";
import Toast, { ToastType } from "@/components/ui/Toast";

const MODULE_LABELS: Record<string, string> = {
  query_analyze_enabled: "查询分析（是否需要检索）",
  kg_extract_enabled: "图谱构建（入库三元组抽取）",
  kg_retrieve_enabled: "图谱检索（查询阶段）",
  rerank_enabled: "重排（CrossEncoder）",
  ocr_image_enabled: "OCR（图片/扫描件）",
  table_parse_enabled: "表格解析增强",
};

const PARAM_FIELDS: Record<"embedding" | "kg" | "ocr", [string, string][]> = {
  embedding: [
    ["embedding_batch_size", "向量化 batch"],
    ["embedding_concurrency", "向量化并发（预留）"],
  ],
  kg: [
    ["kg_concurrency", "图谱并发"],
    ["kg_chunk_timeout_s", "图谱单块超时(s)"],
    ["kg_max_chunks", "图谱最大处理块数(0不限)"],
  ],
  ocr: [["ocr_concurrency", "OCR 并发（预留）"]],
};

export type RuntimeModalState =
  | { kind: "closed" }
  | { kind: "presets" }
  | { kind: "module"; key: string }
  | { kind: "params"; group: "embedding" | "kg" | "ocr" }
  | { kind: "view"; title: string; body: string };

export function RuntimeSettingsModals({
  state,
  onClose,
}: {
  state: RuntimeModalState;
  onClose: () => void;
}) {
  const { config, saving, refresh, applyPreset, saveModules, saveParams } = useRuntimeSettings();
  const [toast, setToast] = useState<{ open: boolean; message: string; type: ToastType }>({
    open: false,
    message: "",
    type: "info",
  });
  const toastOk = (message: string) => setToast({ open: true, message, type: "success" });
  const toastErr = (message: string) => setToast({ open: true, message, type: "error" });

  const [modChecked, setModChecked] = useState(false);
  const [paramDraft, setParamDraft] = useState<Record<string, string>>({});

  useEffect(() => {
    if (state.kind !== "module" || !config) return;
    setModChecked(Boolean(config.modules?.[state.key]));
  }, [state, config]);

  useEffect(() => {
    if (state.kind !== "params" || !config) return;
    const fields = PARAM_FIELDS[state.group];
    const d: Record<string, string> = {};
    for (const [k] of fields) {
      d[k] = String(config.params?.[k] ?? "");
    }
    setParamDraft(d);
  }, [state, config]);

  if (state.kind === "closed") return null;

  if (state.kind === "view") {
    return (
      <>
        <ConfigModalFrame open title={state.title} onClose={onClose}>
          <p className="text-sm text-gray-600 dark:text-gray-300 whitespace-pre-wrap">{state.body}</p>
        </ConfigModalFrame>
        <Toast
          isOpen={toast.open}
          message={toast.message}
          type={toast.type}
          duration={3000}
          onClose={() => setToast((t) => ({ ...t, open: false }))}
        />
      </>
    );
  }

  if (state.kind === "presets") {
    return (
      <>
        <ConfigModalFrame
          open
          title="性能预设"
          subtitle="切换低配/高配或从服务端重新加载配置"
          onClose={onClose}
          footer={
            <div className="flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200"
              >
                关闭
              </button>
            </div>
          }
        >
          <div className="space-y-3 text-sm">
            <div className="text-gray-600 dark:text-gray-300">
              当前模式：<span className="font-mono">{config?.mode ?? "…"}</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                disabled={saving}
                onClick={async () => {
                  const ok = await applyPreset("low");
                  if (ok === true) toastOk("已切换为低配");
                  else toastErr("保存失败");
                }}
                className="px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 disabled:opacity-50"
              >
                低配
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={async () => {
                  const ok = await applyPreset("high");
                  if (ok === true) toastOk("已切换为高配");
                  else toastErr("保存失败");
                }}
                className="px-3 py-2 rounded-lg bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-100 disabled:opacity-50"
              >
                高配
              </button>
              <button
                type="button"
                disabled={saving}
                onClick={async () => {
                  await refresh();
                  toastOk("已重新加载");
                }}
                className="px-3 py-2 rounded-lg bg-blue-600 text-white disabled:opacity-50"
              >
                重新加载
              </button>
            </div>
          </div>
        </ConfigModalFrame>
        <Toast
          isOpen={toast.open}
          message={toast.message}
          type={toast.type}
          duration={3000}
          onClose={() => setToast((t) => ({ ...t, open: false }))}
        />
      </>
    );
  }

  if (state.kind === "module") {
    const label = MODULE_LABELS[state.key] || state.key;
    return (
      <>
        <ConfigModalFrame
          open
          title={label}
          subtitle="模块开关（保存后生效）"
          onClose={onClose}
          footer={
            <div className="flex justify-end gap-2">
              <button type="button" onClick={onClose} className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800">
                取消
              </button>
              <button
                type="button"
                disabled={saving || !config}
                onClick={async () => {
                  const ok = await saveModules({ [state.key]: modChecked });
                  if (ok === true) {
                    toastOk("已保存");
                    onClose();
                  } else toastErr("保存失败");
                }}
                className="px-3 py-2 rounded-lg text-sm bg-blue-600 text-white disabled:opacity-50"
              >
                确认保存
              </button>
            </div>
          }
        >
          <label className="flex items-center justify-between gap-3">
            <span className="text-sm text-gray-700 dark:text-gray-200">启用该模块</span>
            <input
              type="checkbox"
              className="w-4 h-4"
              checked={modChecked}
              onChange={(e) => setModChecked(e.target.checked)}
            />
          </label>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-3">向量化（embedding）为基础能力，无法在界面关闭。</p>
        </ConfigModalFrame>
        <Toast
          isOpen={toast.open}
          message={toast.message}
          type={toast.type}
          duration={3000}
          onClose={() => setToast((t) => ({ ...t, open: false }))}
        />
      </>
    );
  }

  if (state.kind === "params") {
    const fields = PARAM_FIELDS[state.group];
    const title =
      state.group === "embedding" ? "向量化参数" : state.group === "kg" ? "图谱参数" : "OCR 参数";
    return (
      <>
        <ConfigModalFrame
          open
          title={title}
          subtitle="编辑后点击确认保存（将切换为 custom 模式）"
          onClose={onClose}
          footer={
            <div className="flex justify-end gap-2">
              <button type="button" onClick={onClose} className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800">
                取消
              </button>
              <button
                type="button"
                disabled={saving || !config}
                onClick={async () => {
                  const patch: Record<string, unknown> = {};
                  for (const [k] of fields) {
                    const raw = paramDraft[k] ?? "";
                    const n = Number(raw);
                    patch[k] = raw.trim() === "" ? undefined : Number.isFinite(n) ? n : raw;
                  }
                  const ok = await saveParams(patch);
                  if (ok === true) {
                    toastOk("已保存");
                    onClose();
                  } else toastErr("保存失败");
                }}
                className="px-3 py-2 rounded-lg text-sm bg-blue-600 text-white disabled:opacity-50"
              >
                确认保存
              </button>
            </div>
          }
        >
          <div className="space-y-3">
            {fields.map(([k, lab]) => (
              <label key={k} className="block">
                <span className="text-xs text-gray-500 dark:text-gray-400">{lab}</span>
                <input
                  className="mt-1 w-full px-3 py-2 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800"
                  value={paramDraft[k] ?? ""}
                  onChange={(e) => {
                    const v = e.target.value;
                    setParamDraft((p) => ({ ...p, [k]: v }));
                  }}
                  placeholder="留空=默认"
                />
              </label>
            ))}
          </div>
        </ConfigModalFrame>
        <Toast
          isOpen={toast.open}
          message={toast.message}
          type={toast.type}
          duration={3000}
          onClose={() => setToast((t) => ({ ...t, open: false }))}
        />
      </>
    );
  }

  return null;
}

"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Layout from "@/components/ui/Layout";
import DocumentUpload from "@/components/document/DocumentUpload";
import LoadingProgress from "@/components/ui/LoadingProgress";
import Toast, { ToastType } from "@/components/ui/Toast";
import { apiClient, Document } from "@/lib/api";
import type { KnowledgeSpace } from "@/lib/api";
import { formatDateTime } from "@/lib/timezone";

export default function DocumentsPage() {
  const [loading, setLoading] = useState(true);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState<string>("");

  const [knowledgeSpaces, setKnowledgeSpaces] = useState<KnowledgeSpace[]>([]);
  const [selectedKnowledgeSpaceId, setSelectedKnowledgeSpaceId] = useState<string | undefined>(undefined);
  const [creatingSpace, setCreatingSpace] = useState(false);
  const [newSpaceName, setNewSpaceName] = useState("");
  const [newSpaceDesc, setNewSpaceDesc] = useState("");

  const [documents, setDocuments] = useState<Document[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [pageSize] = useState(20);

  const pollingTimerRef = useRef<NodeJS.Timeout | null>(null);
  const [toast, setToast] = useState<{ isOpen: boolean; message: string; type: ToastType }>({
    isOpen: false,
    message: "",
    type: "info",
  });

  const loadingSteps = ["正在加载知识空间列表...", "正在加载文档列表...", "准备就绪"];

  const showToast = (message: string, type: ToastType) => setToast({ isOpen: true, message, type });

  const loadKnowledgeSpaces = useCallback(async () => {
    const result = await apiClient.listKnowledgeSpaces();
    if (result.error) throw new Error(result.error);
    const list = result.data?.knowledge_spaces || [];
    setKnowledgeSpaces(list);
    const defaultSpace = list.find((s) => s.is_default);
    setSelectedKnowledgeSpaceId((prev) => prev || defaultSpace?.id || list[0]?.id);
  }, []);

  const loadDocuments = useCallback(
    async (knowledgeSpaceId?: string, nextPage: number = page) => {
      const skip = nextPage * pageSize;
      const result = await apiClient.listDocuments(knowledgeSpaceId, skip, pageSize);
      if (result.error) throw new Error(result.error);
      setDocuments(result.data?.documents || []);
      setTotal(result.data?.total || 0);
    },
    [page, pageSize]
  );

  const hasProcessingDocs = useMemo(
    () => documents.some((d) => d.status && ["uploading", "processing", "parsing", "chunking", "embedding"].includes(d.status)),
    [documents]
  );

  useEffect(() => {
    let mounted = true;
    const init = async () => {
      try {
        setLoading(true);
        setLoadingStep(0);
        await loadKnowledgeSpaces();
        if (!mounted) return;

        setLoadingStep(1);
        await loadDocuments(undefined, 0);
        if (!mounted) return;

        setLoadingStep(2);
        setLoading(false);
      } catch (e) {
        if (!mounted) return;
        setError((e as Error).message || "初始化失败");
        setLoading(false);
      }
    };
    init();
    return () => {
      mounted = false;
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    };
  }, [loadKnowledgeSpaces, loadDocuments]);

  useEffect(() => {
    if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
    pollingTimerRef.current = null;

    if (!hasProcessingDocs) return;

    pollingTimerRef.current = setInterval(() => {
      loadDocuments(selectedKnowledgeSpaceId, page).catch(() => {});
    }, 3000);

    return () => {
      if (pollingTimerRef.current) clearInterval(pollingTimerRef.current);
      pollingTimerRef.current = null;
    };
  }, [hasProcessingDocs, loadDocuments, page, selectedKnowledgeSpaceId]);

  const handleRefresh = async () => {
    try {
      await loadDocuments(selectedKnowledgeSpaceId, page);
      showToast("已刷新", "success");
    } catch (e) {
      showToast((e as Error).message || "刷新失败", "error");
    }
  };

  const handleDelete = async (docId: string) => {
    if (!confirm("确认删除该文档及其向量数据？")) return;
    const result = await apiClient.deleteDocument(docId);
    if (result.error) {
      showToast(result.error, "error");
      return;
    }
    showToast("已删除", "success");
    await loadDocuments(selectedKnowledgeSpaceId, page);
  };

  const handleCreateSpace = async () => {
    const name = newSpaceName.trim();
    if (!name) {
      showToast("知识空间名称不能为空", "warning");
      return;
    }
    setCreatingSpace(true);
    try {
      const result = await apiClient.createKnowledgeSpace({
        name,
        description: newSpaceDesc.trim() || undefined,
      });
      if (result.error) throw new Error(result.error);
      showToast("已创建知识空间", "success");
      setNewSpaceName("");
      setNewSpaceDesc("");
      await loadKnowledgeSpaces();
    } catch (e) {
      showToast((e as Error).message || "创建失败", "error");
    } finally {
      setCreatingSpace(false);
    }
  };

  if (loading) {
    return (
      <Layout allowScroll>
        <div className="flex min-h-[40vh] items-center justify-center">
          <LoadingProgress steps={loadingSteps} currentStep={loadingStep} className="min-h-[40vh]" />
        </div>
      </Layout>
    );
  }

  return (
    <Layout allowScroll>
      <div className="max-w-6xl mx-auto space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="text-xl font-bold text-gray-900 dark:text-gray-100">知识库</div>
            <div className="text-sm text-gray-500 dark:text-gray-400">上传文档入库后，可在聊天中开启“知识库检索”进行RAG检索增强。</div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700"
            >
              刷新
            </button>
          </div>
        </div>

        {error && (
          <div className="p-3 rounded-lg bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 border border-red-200 dark:border-red-800">
            {error}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="flex items-center gap-2">
            <span className="text-sm text-gray-600 dark:text-gray-300 whitespace-nowrap">知识空间</span>
            <select
              value={selectedKnowledgeSpaceId || ""}
              onChange={(e) => {
                const v = e.target.value || undefined;
                setSelectedKnowledgeSpaceId(v);
                setPage(0);
                loadDocuments(v, 0).catch(() => {});
              }}
              className="px-3 py-2 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100"
            >
              {knowledgeSpaces.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                  {s.is_default ? "（默认）" : ""}
                </option>
              ))}
            </select>
          </div>
          <div className="flex-1" />
          <button
            onClick={handleCreateSpace}
            disabled={creatingSpace}
            className="px-3 py-2 rounded-lg text-sm bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-60"
          >
            新增知识空间
          </button>
        </div>

        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-3">创建知识空间</div>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
            <input
              value={newSpaceName}
              onChange={(e) => setNewSpaceName(e.target.value)}
              placeholder="知识空间名称（必填）"
              className="px-3 py-2 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100"
            />
            <input
              value={newSpaceDesc}
              onChange={(e) => setNewSpaceDesc(e.target.value)}
              placeholder="描述（可选）"
              className="px-3 py-2 rounded-lg text-sm border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100"
            />
            <button
              onClick={handleCreateSpace}
              disabled={creatingSpace}
              className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 hover:bg-gray-200 dark:hover:bg-gray-700 disabled:opacity-60"
            >
              {creatingSpace ? "创建中..." : "创建"}
            </button>
          </div>
          <div className="text-xs text-gray-500 dark:text-gray-400 mt-2">
            上传文档/对话附件前需要先选择目标知识空间。
          </div>
        </div>

        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl p-4">
          <div className="text-sm font-semibold text-gray-800 dark:text-gray-100 mb-3">上传入库</div>
          <DocumentUpload
            knowledgeSpaceId={selectedKnowledgeSpaceId}
            onUploadSuccess={async () => {
              showToast("上传成功，正在后台处理", "success");
              await loadDocuments(selectedKnowledgeSpaceId, page);
            }}
          />
        </div>

        <div className="bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-xl overflow-hidden">
          <div className="px-4 py-3 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
            <div className="text-sm font-semibold text-gray-800 dark:text-gray-100">
              文档列表 <span className="text-gray-500 dark:text-gray-400 font-normal">({total})</span>
            </div>
          </div>

          <div className="divide-y divide-gray-100 dark:divide-gray-800">
            {documents.length === 0 ? (
              <div className="p-6 text-sm text-gray-500 dark:text-gray-400">暂无文档</div>
            ) : (
              documents.map((d) => (
                <div key={d.id} className="p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div className="min-w-0">
                    <div className="font-medium text-gray-900 dark:text-gray-100 truncate">{d.title}</div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {d.file_type} · {(d.file_size / 1024 / 1024).toFixed(2)} MB · {formatDateTime(d.created_at)}
                    </div>
                    <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      状态：{d.status || "unknown"}
                      {typeof d.progress_percentage === "number" ? `（${d.progress_percentage}%）` : ""}
                      {d.current_stage ? ` · ${d.current_stage}` : ""}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => handleDelete(d.id)}
                      className="px-3 py-2 rounded-lg text-sm bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300 hover:bg-red-100 dark:hover:bg-red-900/30"
                    >
                      删除
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>

          <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 flex items-center justify-between text-sm">
            <div className="text-gray-500 dark:text-gray-400">
              第 {page + 1} 页 / 共 {Math.max(1, Math.ceil(total / pageSize))} 页
            </div>
            <div className="flex gap-2">
              <button
                disabled={page === 0}
                onClick={() => {
                  const p = Math.max(0, page - 1);
                  setPage(p);
                  loadDocuments(selectedAssistantId, p).catch(() => {});
                }}
                className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 disabled:opacity-50"
              >
                上一页
              </button>
              <button
                disabled={(page + 1) * pageSize >= total}
                onClick={() => {
                  const p = page + 1;
                  setPage(p);
                  loadDocuments(selectedAssistantId, p).catch(() => {});
                }}
                className="px-3 py-2 rounded-lg text-sm bg-gray-100 dark:bg-gray-800 text-gray-700 dark:text-gray-200 disabled:opacity-50"
              >
                下一页
              </button>
            </div>
          </div>
        </div>
      </div>

      <Toast
        isOpen={toast.isOpen}
        message={toast.message}
        type={toast.type}
        duration={4000}
        onClose={() => setToast((t) => ({ ...t, isOpen: false }))}
      />
    </Layout>
  );
}


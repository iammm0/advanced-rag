import type { Edge, Node } from "@xyflow/react";

export type ArchNodeKind =
  | "view"
  | "presets"
  | "runtime-module"
  | "runtime-params-embedding"
  | "runtime-params-kg"
  | "runtime-params-ocr"
  | "deep-research"
  | "deep-agent";

export type ArchNodeData = {
  label: string;
  subtitle?: string;
  kind: ArchNodeKind;
  moduleKey?: string;
  agentType?: string;
  variant?: "default" | "accent" | "muted";
};

const EXPERT_LAYOUT: { agentType: string; label: string; x: number; y: number }[] = [
  { agentType: "document_retrieval", label: "文档检索", x: 600, y: 220 },
  { agentType: "formula_analysis", label: "公式分析", x: 780, y: 220 },
  { agentType: "code_analysis", label: "代码分析", x: 600, y: 330 },
  { agentType: "concept_explanation", label: "概念解释", x: 780, y: 330 },
  { agentType: "example_generation", label: "示例生成", x: 600, y: 440 },
  { agentType: "exercise", label: "习题", x: 780, y: 440 },
  { agentType: "scientific_coding", label: "科学计算", x: 600, y: 550 },
  { agentType: "summary", label: "总结", x: 780, y: 550 },
];

export function buildNodesAndEdges(): { nodes: Node<ArchNodeData>[]; edges: Edge[] } {
  const nodes: Node<ArchNodeData>[] = [
    {
      id: "n_presets",
      type: "arch",
      position: { x: 40, y: 40 },
      data: {
        kind: "presets",
        label: "性能预设",
        subtitle: "低配 / 高配 / 重载",
        variant: "accent",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_user",
      position: { x: 320, y: 40 },
      data: { kind: "view", label: "用户查询", subtitle: "Query 入口", variant: "muted" },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_qa",
      position: { x: 320, y: 150 },
      data: {
        kind: "runtime-module",
        label: "查询分析",
        subtitle: "是否需要检索",
        moduleKey: "query_analyze_enabled",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_emb",
      position: { x: 320, y: 260 },
      data: {
        kind: "runtime-params-embedding",
        label: "向量化",
        subtitle: "batch · 并发",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_kg_params",
      position: { x: 40, y: 260 },
      data: { kind: "runtime-params-kg", label: "图谱参数", subtitle: "并发 · 超时 · 块数" },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_kg_ext",
      position: { x: 40, y: 150 },
      data: {
        kind: "runtime-module",
        label: "图谱构建",
        subtitle: "入库三元组",
        moduleKey: "kg_extract_enabled",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_kg_ret",
      position: { x: 320, y: 380 },
      data: {
        kind: "runtime-module",
        label: "图谱检索",
        subtitle: "查询阶段",
        moduleKey: "kg_retrieve_enabled",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_rr",
      position: { x: 320, y: 500 },
      data: {
        kind: "runtime-module",
        label: "重排",
        subtitle: "CrossEncoder",
        moduleKey: "rerank_enabled",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_ocr",
      position: { x: 40, y: 500 },
      data: {
        kind: "runtime-module",
        label: "OCR",
        subtitle: "图像 / 扫描件",
        moduleKey: "ocr_image_enabled",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_table",
      position: { x: 40, y: 620 },
      data: {
        kind: "runtime-module",
        label: "表格解析",
        subtitle: "结构化",
        moduleKey: "table_parse_enabled",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_ocr_params",
      position: { x: 40, y: 380 },
      data: { kind: "runtime-params-ocr", label: "OCR 并发", subtitle: "预留参数" },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_out",
      position: { x: 320, y: 640 },
      data: { kind: "view", label: "生成与回答", subtitle: "LLM 输出", variant: "muted" },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_deep",
      position: { x: 600, y: 40 },
      data: {
        kind: "deep-research",
        label: "深度研究",
        subtitle: "多智能体 · 总配置",
        variant: "accent",
      },
      draggable: false,
      selectable: false,
    },
    {
      type: "arch",
      id: "n_coordinator",
      position: { x: 600, y: 130 },
      data: {
        kind: "deep-agent",
        label: "协调 Agent",
        subtitle: "coordinator",
        agentType: "coordinator",
        variant: "accent",
      },
      draggable: false,
      selectable: false,
    },
  ];

  for (const ex of EXPERT_LAYOUT) {
    nodes.push({
      id: `n_ex_${ex.agentType}`,
      type: "arch",
      position: { x: ex.x, y: ex.y },
      data: {
        kind: "deep-agent",
        label: ex.label,
        subtitle: ex.agentType,
        agentType: ex.agentType,
      },
      draggable: false,
      selectable: false,
    });
  }

  const edges: Edge[] = [
    { id: "e_u_q", source: "n_user", target: "n_qa", animated: true },
    { id: "e_q_e", source: "n_qa", target: "n_emb", animated: true },
    { id: "e_e_kr", source: "n_emb", target: "n_kg_ret", animated: true },
    { id: "e_kr_rr", source: "n_kg_ret", target: "n_rr", animated: true },
    { id: "e_rr_o", source: "n_rr", target: "n_out", animated: true },
    { id: "e_kgx_kr", source: "n_kg_ext", target: "n_kg_ret", animated: false },
    { id: "e_ocr_e", source: "n_ocr", target: "n_emb", animated: false },
    { id: "e_tbl_e", source: "n_table", target: "n_emb", animated: false },
    { id: "e_q_dr", source: "n_qa", target: "n_deep", animated: false, style: { strokeDasharray: "4 4" } },
    { id: "e_dr_co", source: "n_deep", target: "n_coordinator", animated: false },
  ];

  for (const ex of EXPERT_LAYOUT) {
    edges.push({
      id: `e_co_${ex.agentType}`,
      source: "n_coordinator",
      target: `n_ex_${ex.agentType}`,
      animated: false,
    });
  }

  return { nodes, edges };
}

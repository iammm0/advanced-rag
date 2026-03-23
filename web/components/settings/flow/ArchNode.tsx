"use client";

import { Handle, Position, type NodeProps } from "@xyflow/react";
import type { ArchNodeData } from "./buildArchitectureFlow";

export default function ArchNode(props: NodeProps) {
  const data = props.data as ArchNodeData;
  const muted = data.variant === "muted";
  const accent = data.variant === "accent";
  return (
    <div
      className={`rounded-lg border px-2.5 py-2 shadow-sm min-w-[128px] max-w-[160px] text-left transition-shadow ${
        muted
          ? "bg-gray-100/95 dark:bg-gray-800/90 border-gray-200 dark:border-gray-600 border-dashed cursor-default"
          : accent
            ? "bg-indigo-50 dark:bg-indigo-950/40 border-indigo-300 dark:border-indigo-700 cursor-pointer hover:shadow-md"
            : "bg-white dark:bg-gray-900 border-gray-200 dark:border-gray-600 cursor-pointer hover:shadow-md hover:border-blue-300 dark:hover:border-blue-600"
      }`}
    >
      <Handle type="target" position={Position.Top} className="!w-2 !h-2 !bg-slate-400 dark:!bg-slate-500 !border-0" />
      <div
        className={`text-[11px] font-semibold leading-snug ${
          muted ? "text-gray-600 dark:text-gray-300" : accent ? "text-indigo-900 dark:text-indigo-100" : "text-gray-900 dark:text-gray-100"
        }`}
      >
        {data.label}
      </div>
      {data.subtitle ? (
        <div className="text-[9px] text-gray-500 dark:text-gray-400 mt-0.5 leading-tight line-clamp-2">{data.subtitle}</div>
      ) : null}
      <Handle type="source" position={Position.Bottom} className="!w-2 !h-2 !bg-slate-400 dark:!bg-slate-500 !border-0" />
    </div>
  );
}

"use client";

import type { ReactNode } from "react";

export default function ConfigModalFrame({
  open,
  title,
  subtitle,
  children,
  footer,
  onClose,
  panelClassName = "max-w-lg",
}: {
  open: boolean;
  title: string;
  subtitle?: string;
  children: ReactNode;
  footer?: ReactNode;
  onClose: () => void;
  /** 例如 max-w-4xl 用于宽表单 */
  panelClassName?: string;
}) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
      <button
        type="button"
        className="absolute inset-0 bg-black/40 backdrop-blur-[1px]"
        aria-label="关闭"
        onClick={onClose}
      />
      <div
        role="dialog"
        aria-modal
        className={`relative z-[101] w-full ${panelClassName} max-h-[min(90vh,720px)] flex flex-col rounded-xl border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 shadow-xl`}
      >
        <div className="px-4 py-3 border-b border-gray-100 dark:border-gray-800 flex items-start justify-between gap-2 shrink-0">
          <div>
            <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">{title}</h3>
            {subtitle ? <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">{subtitle}</p> : null}
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded-lg text-gray-500 hover:bg-gray-100 dark:hover:bg-gray-800"
            aria-label="关闭"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
        <div className="px-4 py-3 overflow-y-auto flex-1 min-h-0">{children}</div>
        {footer ? <div className="px-4 py-3 border-t border-gray-100 dark:border-gray-800 shrink-0">{footer}</div> : null}
      </div>
    </div>
  );
}

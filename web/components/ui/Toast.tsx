"use client";

import { useEffect } from "react";

export type ToastType = "success" | "error" | "info" | "warning";

interface ToastProps {
  isOpen: boolean;
  message: string;
  type?: ToastType;
  duration?: number;
  onClose: () => void;
}

export default function Toast({
  isOpen,
  message,
  type = "info",
  duration = 3000,
  onClose,
}: ToastProps) {
  useEffect(() => {
    if (isOpen && duration > 0) {
      const timer = setTimeout(() => {
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [isOpen, duration, onClose]);

  if (!isOpen) return null;

  const typeStyles = {
    success: "bg-green-500 dark:bg-green-600 text-white",
    error: "bg-red-500 dark:bg-red-600 text-white",
    info: "bg-blue-500 dark:bg-blue-600 text-white",
    warning: "bg-yellow-500 dark:bg-yellow-600 text-white",
  };

  const icons = {
    success: "✓",
    error: "✗",
    info: "ℹ",
    warning: "⚠",
  };

  return (
    <div className="fixed top-4 right-4 z-50 pointer-events-none">
      <div
        className={`${typeStyles[type]} rounded-xl shadow-2xl px-6 py-4 min-w-[300px] max-w-md pointer-events-auto flex items-center gap-3 animate-slideIn`}
        style={{ animation: "slideIn 0.3s ease-out" }}
      >
        <span className="text-xl font-bold flex-shrink-0">{icons[type]}</span>
        <p className="text-sm font-medium flex-1">{message}</p>
        <button
          onClick={onClose}
          className="flex-shrink-0 text-white/80 hover:text-white transition-colors"
        >
          ✕
        </button>
      </div>
    </div>
  );
}


"use client";

import { useState, useEffect } from "react";

interface DeepResearchToggleProps {
  enabled: boolean;
  onChange: (enabled: boolean) => void;
}

export default function DeepResearchToggle({
  enabled,
  onChange,
}: DeepResearchToggleProps) {
  const [isBeta, setIsBeta] = useState(true); // BETA状态

  useEffect(() => {
    // 从localStorage读取状态
    if (typeof window !== "undefined") {
      const saved = localStorage.getItem("deepResearchEnabled");
      if (saved !== null) {
        onChange(saved === "true");
      }
    }
  }, [onChange]);

  const handleToggle = (newValue: boolean) => {
    onChange(newValue);
    if (typeof window !== "undefined") {
      localStorage.setItem("deepResearchEnabled", String(newValue));
    }
  };

  return (
    <div className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-800 rounded-lg">
      <label className="flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={enabled}
          onChange={(e) => handleToggle(e.target.checked)}
          className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500"
        />
        <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
          深度研究模式
        </span>
        {isBeta && (
          <span className="px-2 py-0.5 text-xs font-semibold text-white bg-orange-500 rounded">
            BETA
          </span>
        )}
      </label>
      {enabled && (
        <span className="text-xs text-gray-500 dark:text-gray-400">
          多Agent协作，生成深度研究结果
        </span>
      )}
    </div>
  );
}


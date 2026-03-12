"use client";

/**
 * 思考中的圆点闪烁动画组件
 * 用于GPU预热期间显示"内容即将生成"的视觉反馈
 */
export default function ThinkingDots() {
  return (
    <div className="flex items-center gap-1.5 py-1">
      <span 
        className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full thinking-dot"
        style={{ animationDelay: '0ms' }}
      ></span>
      <span 
        className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full thinking-dot"
        style={{ animationDelay: '200ms' }}
      ></span>
      <span 
        className="w-2 h-2 bg-gray-400 dark:bg-gray-500 rounded-full thinking-dot"
        style={{ animationDelay: '400ms' }}
      ></span>
    </div>
  );
}


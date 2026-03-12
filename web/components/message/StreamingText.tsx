"use client";

import { useEffect, useRef, useState } from "react";
import FormattedMessage from "./FormattedMessage";

interface StreamingTextProps {
  text: string;
  className?: string;
  onContentChange?: () => void; // 内容变化时的回调，用于触发滚动
}

/**
 * 流式文本组件
 * 优化：减少重新渲染，改进光标动画，支持自动滚动
 */
export default function StreamingText({
  text,
  className = "",
  onContentChange,
}: StreamingTextProps) {
  const [displayedText, setDisplayedText] = useState(text);
  const prevTextRef = useRef(text);
  const containerRef = useRef<HTMLDivElement>(null);
  const [showCursor, setShowCursor] = useState(true);

  // 当文本更新时，平滑更新显示内容
  useEffect(() => {
    if (text !== prevTextRef.current) {
      // 如果文本变长，说明是流式更新
      if (text.length > prevTextRef.current.length) {
        setDisplayedText(text);
        // 触发滚动回调
        if (onContentChange) {
          // 使用 requestAnimationFrame 确保在 DOM 更新后执行
          requestAnimationFrame(() => {
            onContentChange();
          });
        }
      } else {
        // 如果文本变短或完全改变，立即更新
        setDisplayedText(text);
      }
      prevTextRef.current = text;
    }
  }, [text, onContentChange]);

  // 光标闪烁动画
  useEffect(() => {
    const interval = setInterval(() => {
      setShowCursor((prev) => !prev);
    }, 530); // 稍微慢一点，更自然

    return () => clearInterval(interval);
  }, []);

  return (
    <div ref={containerRef} className={className}>
      <FormattedMessage content={displayedText} />
      {showCursor && (
        <span 
          className="inline-block ml-1 w-0.5 h-[1.2em] bg-blue-500 dark:bg-blue-400 align-middle"
          style={{ 
            animation: 'blink 1s step-end infinite',
            verticalAlign: 'baseline'
          }}
          aria-hidden="true"
        />
      )}
      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}


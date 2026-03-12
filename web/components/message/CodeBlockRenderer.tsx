"use client";

import { useState } from "react";
import rehypeHighlight from "rehype-highlight";
import "highlight.js/styles/github-dark.css";

interface CodeBlockRendererProps {
  language: string;
  code: string;
  codeElement?: any;
}

/**
 * 代码块渲染组件
 * 职责：处理多语言代码块的语法高亮和复制功能
 * 保留完整的语法高亮逻辑
 */
export default function CodeBlockRenderer({
  language,
  code,
  codeElement
}: CodeBlockRendererProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error("复制失败:", err);
    }
  };

  // 语言显示名称映射
  const languageNames: Record<string, string> = {
    python: "Python",
    javascript: "JavaScript",
    js: "JavaScript",
    typescript: "TypeScript",
    ts: "TypeScript",
    java: "Java",
    cpp: "C++",
    c: "C",
    csharp: "C#",
    go: "Go",
    rust: "Rust",
    php: "PHP",
    ruby: "Ruby",
    swift: "Swift",
    kotlin: "Kotlin",
    html: "HTML",
    css: "CSS",
    json: "JSON",
    xml: "XML",
    yaml: "YAML",
    sql: "SQL",
    bash: "Bash",
    shell: "Shell",
    sh: "Shell",
    matlab: "MATLAB",
    r: "R",
    scala: "Scala",
    lua: "Lua",
    perl: "Perl",
    dockerfile: "Dockerfile",
    markdown: "Markdown",
    md: "Markdown",
  };

  const displayLanguage = languageNames[language.toLowerCase()] || language || "Code";

  return (
    <div className="relative my-3 sm:my-4 group code-block-wrapper" role="region" aria-label={`${displayLanguage}代码块`}>
      {/* 代码块头部 */}
      <div className="flex items-center justify-between bg-gray-800 dark:bg-gray-900 text-gray-300 dark:text-gray-200 px-3 sm:px-4 py-1.5 sm:py-2 rounded-t-lg border-b border-gray-700 dark:border-gray-600">
        <div className="flex items-center gap-1.5 sm:gap-2 min-w-0 flex-1">
          <svg className="w-3.5 sm:w-4 h-3.5 sm:h-4 text-gray-400 dark:text-gray-300 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
          </svg>
          <span className="text-[10px] sm:text-xs font-medium truncate">{displayLanguage}</span>
        </div>
        <button
          onClick={handleCopy}
          className="flex items-center gap-1 sm:gap-1.5 px-2 sm:px-2.5 py-1 min-h-[32px] sm:min-h-0 text-[10px] sm:text-xs text-gray-400 dark:text-gray-300 active:text-white dark:active:text-gray-100 active:bg-gray-700 dark:active:bg-gray-700 rounded transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 dark:focus:ring-blue-400 focus:ring-offset-2 dark:focus:ring-offset-gray-800 flex-shrink-0"
          title="复制代码"
          aria-label="复制代码到剪贴板"
        >
          {copied ? (
            <>
              <svg className="w-3 sm:w-3.5 h-3 sm:h-3.5 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
              <span className="text-green-400 hidden sm:inline">已复制</span>
            </>
          ) : (
            <>
              <svg className="w-3 sm:w-3.5 h-3 sm:h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <span className="hidden sm:inline">复制</span>
            </>
          )}
        </button>
      </div>
      
      {/* 代码内容 */}
      <div className="relative">
        <pre className="bg-gray-900 dark:bg-gray-950 text-gray-100 dark:text-gray-200 rounded-b-lg p-3 sm:p-4 overflow-x-auto border border-gray-700 dark:border-gray-600 border-t-0 shadow-lg code-block" role="textbox" aria-readonly="true" style={{ WebkitOverflowScrolling: 'touch' }}>
          <code className={`language-${language} hljs text-xs sm:text-sm`}>
            {codeElement || code}
          </code>
        </pre>
      </div>
    </div>
  );
}


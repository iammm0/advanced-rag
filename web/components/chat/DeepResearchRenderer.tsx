"use client";

import { useMemo } from "react";
import FormattedMessage from "../message/FormattedMessage";

interface AgentResult {
  agent_type: string;
  content: string;
  title?: string;
}

interface DeepResearchRendererProps {
  agentResults: AgentResult[];
  className?: string;
}

// Agent类型的中文名称映射
const agentTypeNames: Record<string, string> = {
  coordinator: "协调规划",
  document_retrieval: "文档检索",
  formula_analysis: "公式分析",
  code_analysis: "代码分析",
  concept_explanation: "概念解释",
  example_generation: "示例生成",
  summary: "总结",
  exercise: "练习",
  scientific_coding: "科学编程",
};

/**
 * 检测内容是否是HTML格式
 */
function isHTML(content: string): boolean {
  if (!content || typeof content !== "string") return false;
  const trimmed = content.trim();
  return (
    trimmed.startsWith("<!DOCTYPE") ||
    trimmed.startsWith("<html") ||
    trimmed.startsWith("<div") ||
    (trimmed.includes("<") && trimmed.includes(">") && /<[a-z][\s\S]*>/i.test(trimmed))
  );
}

/**
 * 从HTML中提取文本内容（简单版本）
 * 将HTML标签转换为markdown格式
 */
function htmlToMarkdown(html: string): string {
  if (typeof window === "undefined") {
    // 服务端：简单处理，移除HTML标签
    return html
      .replace(/<!DOCTYPE[\s\S]*?>/gi, "")
      .replace(/<html[\s\S]*?>/gi, "")
      .replace(/<\/html>/gi, "")
      .replace(/<head>[\s\S]*?<\/head>/gi, "")
      .replace(/<body[\s\S]*?>/gi, "")
      .replace(/<\/body>/gi, "")
      .replace(/<h([1-6])>([\s\S]*?)<\/h\1>/gi, (_, level, text) => {
        return `${"#".repeat(parseInt(level))} ${text.trim()}\n\n`;
      })
      .replace(/<p>([\s\S]*?)<\/p>/gi, "$1\n\n")
      .replace(/<div[\s\S]*?>/gi, "\n")
      .replace(/<\/div>/gi, "\n")
      .replace(/<pre>([\s\S]*?)<\/pre>/gi, (_, code) => {
        return `\n\`\`\`\n${code.trim()}\n\`\`\`\n\n`;
      })
      .replace(/<code>([\s\S]*?)<\/code>/gi, "`$1`")
      .replace(/<strong>([\s\S]*?)<\/strong>/gi, "**$1**")
      .replace(/<em>([\s\S]*?)<\/em>/gi, "*$1*")
      .replace(/<a[\s\S]*?href=["']([^"']+)["'][\s\S]*?>([\s\S]*?)<\/a>/gi, "[$2]($1)")
      .replace(/<[^>]+>/g, "")
      .replace(/\n{3,}/g, "\n\n")
      .trim();
  }

  // 客户端：使用DOM API提取文本
  try {
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    
    // 移除script和style标签
    const scripts = doc.querySelectorAll("script, style");
    scripts.forEach((el) => el.remove());
    
    // 提取body内容
    const body = doc.body || doc.documentElement;
    if (!body) return html;
    
    // 简单的HTML到Markdown转换
    let markdown = body.innerText || body.textContent || "";
    
    // 尝试保留一些结构
    const headings = body.querySelectorAll("h1, h2, h3, h4, h5, h6");
    headings.forEach((heading) => {
      const level = parseInt(heading.tagName.charAt(1));
      const text = heading.textContent || "";
      markdown = markdown.replace(text, `${"#".repeat(level)} ${text}\n\n`);
    });
    
    // 处理代码块
    const codeBlocks = body.querySelectorAll("pre code, pre");
    codeBlocks.forEach((code) => {
      const codeText = code.textContent || "";
      const language = code.className.match(/language-(\w+)/)?.[1] || "";
      markdown = markdown.replace(
        codeText,
        `\n\`\`\`${language}\n${codeText}\n\`\`\`\n\n`
      );
    });
    
    return markdown.trim() || html;
  } catch (error) {
    console.warn("HTML转换失败，返回原始内容:", error);
    return html;
  }
}

export default function DeepResearchRenderer({
  agentResults,
  className = "",
}: DeepResearchRendererProps) {
  // 处理HTML内容，转换为markdown
  const processedResults = useMemo(() => {
    return agentResults.map((result) => {
      if (!result.content || result.content.trim() === "") {
        return result;
      }
      
      // 如果内容是HTML格式，转换为markdown
      if (isHTML(result.content)) {
        return {
          ...result,
          content: htmlToMarkdown(result.content),
        };
      }
      
      return result;
    });
  }, [agentResults]);

  if (!processedResults || processedResults.length === 0) {
    return null;
  }

  return (
    <div className={`deep-research-renderer ${className}`}>
      {processedResults.map((result, index) => {
        if (!result.content || result.content.trim() === "") {
          return null;
        }

        const agentName = result.title || agentTypeNames[result.agent_type] || result.agent_type;

        return (
          <div
            key={`${result.agent_type}-${index}`}
            className="mb-8 pb-8 border-b border-gray-200/50 dark:border-gray-700/50 last:border-b-0 last:pb-0 last:mb-0 animate-fade-in-up relative group"
            style={{ animationDelay: `${index * 0.1}s` }}
          >
            {/* 左侧装饰线 */}
            <div className="absolute left-0 top-0 bottom-0 w-1 bg-gradient-to-b from-blue-500 via-purple-500 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 rounded-full"></div>
            
            {/* Agent标题 - 增强视觉效果 */}
            <div className="flex items-center gap-3 mb-4 relative">
              <div className="flex items-center gap-3 px-4 py-2.5 bg-gradient-to-r from-blue-50 via-purple-50 to-pink-50 dark:from-blue-900/30 dark:via-purple-900/20 dark:to-pink-900/20 rounded-xl border-2 border-blue-200 dark:border-blue-800 shadow-md hover:shadow-lg transition-all duration-300 hover:scale-[1.02] relative overflow-hidden">
                {/* 背景光效 */}
                <div className="absolute inset-0 bg-gradient-to-r from-blue-400/10 via-purple-400/10 to-pink-400/10 animate-pulse"></div>
                
                {/* Agent图标 */}
                <div className="relative z-10">
                  <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center shadow-lg">
                    <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
                    </svg>
                  </div>
                  {/* 图标光晕 */}
                  <div className="absolute inset-0 rounded-lg bg-blue-400/30 animate-ping opacity-75"></div>
                </div>
                
                {/* Agent名称 */}
                <div className="relative z-10">
                  <span className="text-sm font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 dark:from-blue-400 dark:via-purple-400 dark:to-pink-400">
                    {agentName}
                  </span>
                  <div className="absolute -bottom-1 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                </div>
                
                {/* 完成标记（如果有） */}
                <div className="ml-auto relative z-10">
                  <div className="w-5 h-5 rounded-full bg-green-500 flex items-center justify-center shadow-md animate-scale-in">
                    <svg className="w-3 h-3 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                </div>
              </div>
            </div>

            {/* Agent内容 - 增强视觉效果 */}
            <div className="pl-4 relative">
              {/* 内容区域装饰 */}
              <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-to-b from-blue-200 via-purple-200 to-transparent dark:from-blue-800 dark:via-purple-800 opacity-50"></div>
              
              <div className="bg-white/50 dark:bg-gray-800/30 rounded-lg p-4 border border-gray-200/50 dark:border-gray-700/50 shadow-sm hover:shadow-md transition-all duration-300">
                <FormattedMessage
                  content={result.content}
                  className="text-gray-800 dark:text-gray-100"
                />
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}


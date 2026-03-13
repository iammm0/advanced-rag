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
  concept_explanation: "概念解释",
  summary: "总结",
  critic: "批判性分析",
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
    <div className={`deep-research-renderer space-y-6 ${className}`}>
      {processedResults.map((result, index) => {
        if (!result.content || result.content.trim() === "") {
          return null;
        }

        const agentName = result.title || agentTypeNames[result.agent_type] || result.agent_type;

        return (
          <div
            key={`${result.agent_type}-${index}`}
            className="animate-fade-in"
          >
            {/* Agent标题 - 纯文本样式 */}
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-bold text-blue-600 dark:text-blue-400 uppercase tracking-wider">
                {agentName}
              </span>
              <div className="h-px flex-1 bg-gray-200 dark:bg-gray-700"></div>
            </div>

            {/* Agent内容 */}
            <div className="pl-0">
              <FormattedMessage
                content={result.content}
                className="text-gray-800 dark:text-gray-100"
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}


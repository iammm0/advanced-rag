"use client";

import React from "react";
import ReactMarkdown, { Components } from "react-markdown";
import remarkGfm from "remark-gfm";
import rehypeRaw from "rehype-raw";
import rehypeHighlight from "rehype-highlight";
import FormulaRenderer from "./FormulaRenderer";
import CodeBlockRenderer from "./CodeBlockRenderer";

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * Markdown 渲染组件
 * 职责：处理纯文本 Markdown 渲染
 * 使用 react-markdown 进行基础渲染，公式和代码块委托给专门组件
 */
export default function MarkdownRenderer({ content, className = "" }: MarkdownRendererProps) {
  // 辅助函数：检查内容是否包含数学公式
  const containsMathFormula = (content: any): boolean => {
    if (typeof content === 'string') {
      return /(\$[^$\n]+\$)|(\$\$[\s\S]*?\$\$)/.test(content);
    }
    if (Array.isArray(content)) {
      return content.some(item => containsMathFormula(item));
    }
    if (content && typeof content === 'object' && content.props) {
      return containsMathFormula(content.props.children);
    }
    return false;
  };

  // 辅助函数：提取文本内容
  const extractTextContent = (content: any): string => {
    if (typeof content === 'string') return content;
    if (Array.isArray(content)) return content.map(extractTextContent).join('');
    if (content && typeof content === 'object' && content.props) {
      return extractTextContent(content.props.children);
    }
    return String(content || '');
  };

  // 定义组件映射
  const components: Components = {
    // 代码块处理
    code({ inline, className: codeClassName, children, ...props }: any) {
      const match = /language-(\w+)/.exec(codeClassName || "");
      const language = match ? match[1] : "";

      // 行内代码
      if (inline) {
        return (
          <code
            className="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 px-1 sm:px-1.5 py-0.5 rounded text-xs sm:text-sm font-mono border border-gray-300 dark:border-gray-600"
            {...props}
          >
            {children}
          </code>
        );
      }

      // 块级代码块
      if (!inline && match) {
        const extractText = (node: any): string => {
          if (typeof node === 'string') return node;
          if (Array.isArray(node)) return node.map(extractText).join('');
          if (node?.props?.children) return extractText(node.props.children);
          return String(node || '');
        };

        const codeContent = extractText(children).replace(/\n$/, '');

        // 数学公式代码块（math）使用 FormulaRenderer
        if (language === 'math') {
          const cleanFormula = codeContent.trim();
          return (
            <div className="my-4">
              <FormulaRenderer content={`$$${cleanFormula}$$`} />
            </div>
          );
        }

        // 其他代码块使用 CodeBlockRenderer
        return (
          <CodeBlockRenderer
            language={language || 'text'}
            code={codeContent}
            codeElement={children}
          />
        );
      }

      // 默认行内代码
      return (
        <code
          className="bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 px-1 sm:px-1.5 py-0.5 rounded text-xs sm:text-sm font-mono border border-gray-300 dark:border-gray-600"
          {...props}
        >
          {children}
        </code>
      );
    },

    // 段落处理
    p({ children }: any) {
      // 检查是否包含块级元素
      const childrenArray = React.Children.toArray(children);
      const hasBlockCode = childrenArray.some((child: any) => {
        if (child && typeof child === 'object' && child.type === 'code' && child.props) {
          const className = child.props.className || '';
          if (className.includes('language-') || child.props.inline === false) {
            return true;
          }
        }
        return false;
      });

      if (hasBlockCode) {
        return (
          <div className="mb-3 leading-relaxed text-gray-900 dark:text-gray-100">
            {children}
          </div>
        );
      }

      // 检查是否包含数学公式
      const hasMath = containsMathFormula(children);

      if (hasMath) {
        const textContent = extractTextContent(children);
        return (
          <div className="mb-3 leading-relaxed text-gray-900 dark:text-gray-100">
            <FormulaRenderer content={textContent} />
          </div>
        );
      }

      return (
        <p className="mb-3 leading-relaxed text-gray-900 dark:text-gray-100">
          {children}
        </p>
      );
    },

    // 标题样式
    h1({ children }: any) {
      return (
        <h1 className="text-xl sm:text-2xl font-bold mt-4 sm:mt-6 mb-3 sm:mb-4 pb-2 border-b-2 border-blue-400 dark:border-blue-500 text-gray-800 dark:text-gray-200">
          {children}
        </h1>
      );
    },
    h2({ children }: any) {
      return (
        <h2 className="text-lg sm:text-xl font-bold mt-4 sm:mt-5 mb-2 sm:mb-3 pb-2 border-b border-blue-300 dark:border-blue-600 text-gray-800 dark:text-gray-200">
          {children}
        </h2>
      );
    },
    h3({ children }: any) {
      return <h3 className="text-base sm:text-lg font-semibold mt-3 sm:mt-4 mb-2 text-gray-800 dark:text-gray-200">{children}</h3>;
    },
    h4({ children }: any) {
      return <h4 className="text-sm sm:text-base font-semibold mt-2 sm:mt-3 mb-1.5 sm:mb-2 text-gray-700 dark:text-gray-300">{children}</h4>;
    },

    // 列表样式
    ul({ children, depth }: any) {
      return (
        <ul className="list-disc list-inside mb-3 space-y-2 ml-0" style={{ paddingLeft: `${(depth || 0) * 1.5}rem` }}>
          {children}
        </ul>
      );
    },
    ol({ children, depth }: any) {
      return (
        <ol className="list-decimal list-inside mb-3 space-y-2 ml-0" style={{ paddingLeft: `${(depth || 0) * 1.5}rem` }}>
          {children}
        </ol>
      );
    },
    li({ children }: any) {
      const hasMath = containsMathFormula(children);
      if (hasMath) {
        const textContent = extractTextContent(children);
        return (
          <li className="ml-2 leading-relaxed text-gray-900 dark:text-gray-100">
            <FormulaRenderer content={textContent} />
          </li>
        );
      }
      return (
        <li className="ml-2 leading-relaxed text-gray-900 dark:text-gray-100">
          {children}
        </li>
      );
    },

    // 引用样式
    blockquote({ children }: any) {
      const hasMath = containsMathFormula(children);
      if (hasMath) {
        const textContent = extractTextContent(children);
        return (
          <blockquote className="border-l-4 border-blue-500 dark:border-blue-400 pl-4 my-2 italic text-gray-700 dark:text-gray-300 bg-blue-50 dark:bg-blue-900/20 py-2 rounded-r">
            <FormulaRenderer content={textContent} />
          </blockquote>
        );
      }
      return (
        <blockquote className="border-l-4 border-blue-500 dark:border-blue-400 pl-4 my-2 italic text-gray-700 dark:text-gray-300 bg-blue-50 dark:bg-blue-900/20 py-2 rounded-r">
          {children}
        </blockquote>
      );
    },

    // 表格样式
    table({ children }: any) {
      return (
        <div className="overflow-x-auto my-3 sm:my-4 shadow-md rounded-lg -mx-2 sm:mx-0" style={{ WebkitOverflowScrolling: 'touch' }}>
          <table className="min-w-full border-collapse border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm sm:text-base">
            {children}
          </table>
        </div>
      );
    },
    thead({ children }: any) {
      return <thead className="bg-gray-100 dark:bg-gray-700">{children}</thead>;
    },
    th({ children }: any) {
      const hasMath = containsMathFormula(children);
      if (hasMath) {
        const textContent = extractTextContent(children).replace(/\n+/g, ' ').trim();
        return (
          <th className="border border-gray-300 dark:border-gray-600 px-4 py-2 text-left font-semibold bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-200">
            <FormulaRenderer content={textContent} />
          </th>
        );
      }
      return (
        <th className="border border-gray-300 dark:border-gray-600 px-2 sm:px-4 py-1.5 sm:py-2 text-left font-semibold bg-gray-50 dark:bg-gray-700 text-gray-900 dark:text-gray-200 text-xs sm:text-sm">
          {children}
        </th>
      );
    },
    td({ children }: any) {
      const hasMath = containsMathFormula(children);
      if (hasMath) {
        const textContent = extractTextContent(children).replace(/\n+/g, ' ').trim();
        return (
          <td className="border border-gray-300 dark:border-gray-600 px-2 sm:px-4 py-1.5 sm:py-2 text-gray-900 dark:text-gray-200 text-xs sm:text-sm">
            <FormulaRenderer content={textContent} />
          </td>
        );
      }
      return (
        <td className="border border-gray-300 dark:border-gray-600 px-2 sm:px-4 py-1.5 sm:py-2 text-gray-900 dark:text-gray-200 text-xs sm:text-sm">
          {children}
        </td>
      );
    },

    // 链接样式
    a({ href, children }: any) {
      return (
        <a
          href={href}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline"
        >
          {children}
        </a>
      );
    },

    // 分隔线
    hr() {
      return <hr className="my-6 border-gray-300 dark:border-gray-600" />;
    },

    // 强调样式
    strong({ children }: any) {
      return <strong className="font-semibold text-gray-900 dark:text-gray-100">{children}</strong>;
    },
    em({ children }: any) {
      return <em className="italic text-gray-700 dark:text-gray-300">{children}</em>;
    },
  };

  return (
    <div className={`prose prose-sm max-w-none ${className}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw, rehypeHighlight]}
        components={components}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}


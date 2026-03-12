"use client";

import { useEffect, useRef, useState } from "react";

// 动态导入DOMPurify（仅在客户端）
let DOMPurify: any = null;
if (typeof window !== "undefined") {
  import("isomorphic-dompurify").then((mod) => {
    DOMPurify = mod.default;
  });
}

interface DeepResearchHTMLRendererProps {
  htmlContent: string;
}

export default function DeepResearchHTMLRenderer({
  htmlContent,
}: DeepResearchHTMLRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (containerRef.current && htmlContent) {
      setIsLoading(true);
      
      // 使用DOMPurify清理HTML内容，防止XSS攻击
      const sanitizeHTML = async () => {
        try {
          // 如果DOMPurify还未加载，等待加载
          if (!DOMPurify) {
            const dompurifyModule = await import("isomorphic-dompurify");
            DOMPurify = dompurifyModule.default;
          }
          
          const sanitizedHTML = DOMPurify.sanitize(htmlContent, {
            ALLOWED_TAGS: [
              "div",
              "h1",
              "h2",
              "h3",
              "h4",
              "h5",
              "h6",
              "p",
              "span",
              "ul",
              "ol",
              "li",
              "pre",
              "code",
              "strong",
              "em",
              "b",
              "i",
              "u",
              "a",
              "table",
              "thead",
              "tbody",
              "tfoot",
              "tr",
              "th",
              "td",
              "img",
              "blockquote",
              "hr",
              "br",
              "section",
              "article",
              "header",
              "footer",
              "aside",
            ],
            ALLOWED_ATTR: [
              "class",
              "id",
              "href",
              "src",
              "alt",
              "title",
              "data-agent",
              "data-source",
              "style",
              "target",
              "rel",
            ],
            ALLOW_DATA_ATTR: true,
            ALLOW_UNKNOWN_PROTOCOLS: false,
          });

          if (containerRef.current) {
            containerRef.current.innerHTML = sanitizedHTML;

            // 添加代码高亮（如果使用了highlight.js）
            if (typeof window !== "undefined" && (window as any).hljs) {
              containerRef.current
                .querySelectorAll("pre code")
                .forEach((block) => {
                  try {
                    (window as any).hljs.highlightElement(block);
                  } catch (e) {
                    console.warn("代码高亮失败:", e);
                  }
                });
            }

            // 处理公式渲染（如果使用了KaTeX或MathJax）
            if (typeof window !== "undefined") {
              // KaTeX支持
              if ((window as any).katex) {
                const katex = (window as any).katex;
                containerRef.current
                  .querySelectorAll(".formula-block, .formula-inline, [data-formula]")
                  .forEach((element) => {
                    try {
                      const formula = element.getAttribute("data-formula") || element.textContent || "";
                      const isBlock = element.classList.contains("formula-block");
                      katex.render(formula, element as HTMLElement, {
                        displayMode: isBlock,
                        throwOnError: false,
                      });
                    } catch (e) {
                      console.warn("KaTeX公式渲染失败:", e);
                    }
                  });
              }
              
              // MathJax支持
              if ((window as any).MathJax) {
                const MathJax = (window as any).MathJax;
                if (MathJax.typesetPromise) {
                  MathJax.typesetPromise([containerRef.current]).catch((err: any) => {
                    // 捕获字体加载失败等错误，但不阻止显示内容
                    const errorMessage = err?.message || String(err || '');
                    if (errorMessage.includes('Failed to fetch') || 
                        errorMessage.includes('getFontsForString') ||
                        errorMessage.includes('font')) {
                      console.debug("MathJax 字体加载失败（不影响显示）:", errorMessage);
                    } else {
                      console.warn("MathJax渲染失败:", errorMessage);
                    }
                  });
                }
              }
            }

            // 处理表格响应式
            containerRef.current
              .querySelectorAll("table")
              .forEach((table) => {
                const wrapper = document.createElement("div");
                wrapper.className = "overflow-x-auto my-4";
                wrapper.style.cssText = "max-width: 100%;";
                table.parentNode?.insertBefore(wrapper, table);
                wrapper.appendChild(table);
              });

            // 处理图片懒加载和响应式
            containerRef.current
              .querySelectorAll("img")
              .forEach((img) => {
                (img as HTMLImageElement).loading = "lazy";
                (img as HTMLImageElement).style.maxWidth = "100%";
                (img as HTMLImageElement).style.height = "auto";
              });

            // 处理链接（在新标签页打开外部链接）
            containerRef.current
              .querySelectorAll("a[href]")
              .forEach((link) => {
                const href = (link as HTMLAnchorElement).href;
                if (href && !href.startsWith(window.location.origin) && !href.startsWith("#")) {
                  (link as HTMLAnchorElement).target = "_blank";
                  (link as HTMLAnchorElement).rel = "noopener noreferrer";
                }
              });

            setIsLoading(false);
          }
        } catch (error) {
          console.error("HTML渲染失败:", error);
          if (containerRef.current) {
            containerRef.current.innerHTML = htmlContent; // 降级处理
          }
          setIsLoading(false);
        }
      };

      sanitizeHTML();
    }
  }, [htmlContent]);

  if (!htmlContent) {
    return null;
  }

  return (
    <div className="deep-research-content-wrapper w-full">
      {isLoading && (
        <div className="flex items-center justify-center py-4 text-gray-500 dark:text-gray-400">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-500"></div>
          <span className="ml-2 text-sm">正在渲染内容...</span>
        </div>
      )}
      <div
        ref={containerRef}
        className="deep-research-content prose prose-sm sm:prose-base max-w-none dark:prose-invert
          prose-headings:font-semibold prose-headings:text-gray-900 dark:prose-headings:text-gray-100
          prose-p:text-gray-700 dark:prose-p:text-gray-300 prose-p:leading-relaxed
          prose-a:text-blue-600 dark:prose-a:text-blue-400 prose-a:no-underline hover:prose-a:underline
          prose-strong:text-gray-900 dark:prose-strong:text-gray-100 prose-strong:font-semibold
          prose-code:text-blue-600 dark:prose-code:text-blue-400 prose-code:bg-gray-100 dark:prose-code:bg-gray-800
          prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:text-sm
          prose-pre:bg-gray-100 dark:prose-pre:bg-gray-800 prose-pre:border prose-pre:border-gray-300 dark:prose-pre:border-gray-700
          prose-pre:rounded-lg prose-pre:p-4 prose-pre:overflow-x-auto
          prose-table:w-full prose-table:border-collapse prose-table:my-4
          prose-th:bg-gray-100 dark:prose-th:bg-gray-800 prose-th:font-semibold prose-th:p-3 prose-th:text-left
          prose-th:border prose-th:border-gray-300 dark:prose-th:border-gray-700
          prose-td:p-3 prose-td:border prose-td:border-gray-300 dark:prose-td:border-gray-700
          prose-img:rounded-lg prose-img:shadow-md prose-img:my-4
          prose-blockquote:border-l-4 prose-blockquote:border-blue-500 prose-blockquote:pl-4 prose-blockquote:italic
          prose-blockquote:text-gray-600 dark:prose-blockquote:text-gray-400
          prose-ul:list-disc prose-ul:pl-6 prose-ol:list-decimal prose-ol:pl-6
          prose-li:my-2"
        style={{
          fontFamily:
            "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', 'Helvetica Neue', Arial, sans-serif",
        }}
      />
    </div>
  );
}


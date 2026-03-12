"use client";

import React, { useEffect, useRef } from "react";
import katex from "katex";
import "katex/dist/katex.min.css";

// 声明 MathJax 全局类型
declare global {
  interface Window {
    MathJax?: {
      typesetPromise: (elements: HTMLElement[]) => Promise<void>;
      startup?: {
        ready: () => void;
        document?: any;
        defaultReady?: () => void;
      };
      config?: any;
      loader?: {
        ready: () => Promise<void>;
      };
    };
    __MATHJAX_INITIALIZED__?: boolean;
  }
}

interface FormulaRendererProps {
  content: string;
  className?: string;
}

/**
 * 公式渲染组件
 * 职责：处理标准的 LaTeX 公式格式
 * - 行内公式：$...$
 * - 块级公式：$$...$$
 * 优先使用 KaTeX 渲染（更快、更轻量、无需加载扩展），不支持的功能回退到 MathJax
 */
export default function FormulaRenderer({ content, className = "" }: FormulaRendererProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const renderedContentRef = useRef<string>("");
  const isRenderingRef = useRef<boolean>(false);
  const needsMathJaxRef = useRef<boolean>(false); // 是否需要使用 MathJax（使用 ref 避免循环依赖）

  // 初始化 MathJax（按需加载）
  useEffect(() => {
    if (typeof window === 'undefined') return;

    // 添加全局错误处理，捕获未处理的Promise错误（如字体加载失败）
    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      // 检查是否是MathJax字体加载相关的错误
      const errorMessage = event.reason?.message || String(event.reason || '');
      const errorString = String(event.reason || '');
      
      if (errorMessage.includes('Failed to fetch') || 
          errorMessage.includes('getFontsForString') ||
          errorMessage.includes('font') ||
          errorString.includes('Failed to fetch') ||
          errorString.includes('getFontsForString')) {
        console.debug('MathJax 字体加载失败（已捕获）:', errorMessage || errorString);
        event.preventDefault(); // 阻止错误冒泡到控制台
        return;
      }
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);
    
    // 监听需要 MathJax 的事件
    const handleMathJaxNeeded = () => {
      needsMathJaxRef.current = true;
      // 如果 MathJax 未加载，触发加载
      if (!window.MathJax) {
        loadMathJax();
      }
    };
    
    window.addEventListener('mathjax-needed', handleMathJaxNeeded);
    
    // 如果已经需要 MathJax，立即加载
    if (needsMathJaxRef.current && !window.MathJax) {
      loadMathJax();
    }
    
    function loadMathJax() {
      if (window.MathJax) {
        initializeMathJax();
        return;
      }
      
      const existingScript = document.querySelector('script[src*="mathjax"]');
      if (existingScript) {
        existingScript.addEventListener('load', initializeMathJax);
        return;
      }

      const script = document.createElement('script');
      // 使用多个CDN源以提高可靠性
      const cdnSources = [
        'https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js',
        'https://cdnjs.cloudflare.com/ajax/libs/mathjax/3.2.2/es5/tex-mml-chtml.js'
      ];
      let currentSourceIndex = 0;
      
      script.async = true;
      script.id = 'mathjax-script';
      script.crossOrigin = 'anonymous';
      // 添加错误处理属性
      script.onerror = null; // 将在后面设置
      script.src = cdnSources[currentSourceIndex];
      
      const loadTimeout = setTimeout(() => {
        if (!window.MathJax) {
          // 尝试备用CDN
          if (currentSourceIndex < cdnSources.length - 1) {
            currentSourceIndex++;
            script.src = cdnSources[currentSourceIndex];
            console.debug(`MathJax 主CDN加载超时，尝试备用CDN: ${cdnSources[currentSourceIndex]}`);
          } else {
            console.warn('MathJax 所有CDN源加载超时，将使用KaTeX渲染');
            window.__MATHJAX_INITIALIZED__ = false;
          }
        }
      }, 10000); // 减少超时时间到10秒
      
      script.onload = () => {
        clearTimeout(loadTimeout);
        initializeMathJax();
      };
      
      script.onerror = () => {
        clearTimeout(loadTimeout);
        // 尝试备用CDN
        if (currentSourceIndex < cdnSources.length - 1) {
          currentSourceIndex++;
          script.src = cdnSources[currentSourceIndex];
          console.debug(`MathJax CDN加载失败，尝试备用CDN: ${cdnSources[currentSourceIndex]}`);
          // 重新添加脚本（移除旧的，添加新的）
          script.remove();
          document.head.appendChild(script);
        } else {
          console.warn('MathJax 所有CDN源加载失败，将使用KaTeX渲染');
          window.__MATHJAX_INITIALIZED__ = false;
        }
      };
      
      document.head.appendChild(script);
    }
    
    function initializeMathJax() {
      if (!window.MathJax) return;

      try {
        window.MathJax.config = {
          tex: {
            inlineMath: [['$', '$'], ['\\(', '\\)']],
            displayMath: [['$$', '$$'], ['\\[', '\\]']],
            processEscapes: true,
            processEnvironments: true,
            packages: {
              '[+]': ['base', 'ams']
            }
          },
          svg: {
            fontCache: 'none', // 禁用字体缓存，避免字体加载失败
            displayAlign: 'center',
            displayIndent: '0'
          },
          startup: {
            ready: () => {
              if (window.MathJax?.startup?.document && window.MathJax.startup.defaultReady) {
                window.MathJax.startup.defaultReady();
              }
            }
          },
          loader: {
            load: ['[tex]/ams'],
            failed: () => {
              console.debug('MathJax 扩展加载失败，继续使用基础功能');
            }
          },
          // 禁用localStorage使用，避免Tracking Prevention错误
          options: {
            skipHtmlTags: ['script', 'noscript', 'style', 'textarea', 'pre', 'code'],
            ignoreHtmlClass: 'tex2jax_ignore',
            processHtmlClass: 'tex2jax_process',
            // 禁用localStorage
            enableMenu: false
          }
        };

        // 添加全局错误处理，捕获字体加载失败
        if (window.MathJax && window.MathJax.startup) {
          const originalReady = window.MathJax.startup.ready;
          window.MathJax.startup.ready = () => {
            try {
              if (originalReady) {
                originalReady();
              }
            } catch (err: any) {
              // 捕获字体加载等错误，但不阻止渲染
              const errorMessage = err?.message || String(err || '');
              if (errorMessage.includes('Failed to fetch') || 
                  errorMessage.includes('getFontsForString') ||
                  errorMessage.includes('font')) {
                console.debug('MathJax 字体加载失败（不影响渲染）:', errorMessage);
              } else {
                console.warn('MathJax 初始化警告:', errorMessage);
              }
            }
          };
        }

        // 确保MathJax不使用localStorage
        if (window.MathJax.startup && window.MathJax.startup.document) {
          const doc = window.MathJax.startup.document;
          if (doc.options) {
            doc.options.enableMenu = false;
          }
        }

        window.__MATHJAX_INITIALIZED__ = true;
      } catch (err) {
        console.warn('MathJax 初始化失败:', err);
        window.__MATHJAX_INITIALIZED__ = false;
      }
    }
    
    return () => {
      window.removeEventListener('mathjax-needed', handleMathJaxNeeded);
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);

  // 辅助函数：为行内公式添加标识圈（用于 MathJax 渲染后）
  const addFormulaBadges = (container: HTMLElement) => {
    // 查找所有 MathJax 行内公式（不是块级公式）
    const mathElements = container.querySelectorAll('.MathJax:not(.MathJax_Display)');
    mathElements.forEach((mathEl) => {
      // 检查是否已经有标识圈
      if (mathEl.parentElement?.classList.contains('inline-formula-wrapper')) {
        return;
      }
      // 创建包装器
      const wrapper = document.createElement('span');
      wrapper.className = 'inline-formula-wrapper';
      // 创建标识圈
      const badge = document.createElement('span');
      badge.className = 'formula-badge';
      badge.textContent = '公式';
      // 包装公式元素
      mathEl.parentNode?.insertBefore(wrapper, mathEl);
      wrapper.appendChild(badge);
      wrapper.appendChild(mathEl);
    });
  };

  // 渲染公式（优先使用 KaTeX）
  useEffect(() => {
    // 幂等性检查
    if (renderedContentRef.current === content && containerRef.current?.hasAttribute('data-rendered')) {
      return;
    }

    if (isRenderingRef.current || !containerRef.current) return;

    isRenderingRef.current = true;
    containerRef.current.removeAttribute('data-rendered');

    // 提取公式内容
    const extractFormulas = (text: string): { inline: string[], block: string[] } => {
      const inline: string[] = [];
      const block: string[] = [];
      
      // 提取行内公式 $...$（不跨行）
      const inlinePattern = /\$([^$\n]+?)\$/g;
      let match;
      while ((match = inlinePattern.exec(text)) !== null) {
        const formula = match[1].trim();
        if (formula) inline.push(formula);
      }
      
      // 提取块级公式 $$...$$
      const blockPattern = /\$\$([\s\S]*?)\$\$/g;
      while ((match = blockPattern.exec(text)) !== null) {
        const formula = match[1].trim();
        if (formula) block.push(formula);
      }
      
      return { inline, block };
    };

    const { inline, block } = extractFormulas(content);
    const hasFormulas = inline.length > 0 || block.length > 0;

    // 如果没有公式，直接显示原始内容
    if (!hasFormulas) {
      containerRef.current.innerHTML = content;
      containerRef.current.setAttribute('data-rendered', 'true');
      renderedContentRef.current = content;
      isRenderingRef.current = false;
      return;
    }

    // 尝试使用 KaTeX 渲染
    try {
      let renderedContent = content;
      let katexError = false;
      const katexErrors: string[] = [];

      // 渲染块级公式
      block.forEach((formula) => {
        try {
          const rendered = katex.renderToString(formula, {
            displayMode: true,
            throwOnError: false,
            errorColor: '#cc0000',
            strict: false
          });
          // 检查是否包含错误标记
          if (rendered.includes('ParseError') || rendered.includes('KaTeX parse error')) {
            katexError = true;
            katexErrors.push(formula);
          } else {
            renderedContent = renderedContent.replace(
              `$$${formula}$$`,
              rendered
            );
          }
        } catch (err) {
          katexError = true;
          katexErrors.push(formula);
        }
      });

      // 渲染行内公式
      inline.forEach((formula) => {
        try {
          const rendered = katex.renderToString(formula, {
            displayMode: false,
            throwOnError: false,
            errorColor: '#cc0000',
            strict: false
          });
          if (rendered.includes('ParseError') || rendered.includes('KaTeX parse error')) {
            katexError = true;
            katexErrors.push(formula);
          } else {
            // 转义特殊字符用于正则替换
            const escaped = formula.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
            // 为行内公式添加标识圈包装
            const wrappedRendered = `<span class="inline-formula-wrapper"><span class="formula-badge">公式</span>${rendered}</span>`;
            renderedContent = renderedContent.replace(
              new RegExp(`\\$${escaped}\\$`, 'g'),
              wrappedRendered
            );
          }
        } catch (err) {
          katexError = true;
          katexErrors.push(formula);
        }
      });

      // 如果 KaTeX 渲染成功，直接使用
      if (!katexError) {
        containerRef.current.innerHTML = renderedContent;
        // 为 KaTeX 渲染的行内公式添加标识圈（如果还没有）
        if (containerRef.current) {
          const wrappers = containerRef.current.querySelectorAll('.inline-formula-wrapper');
          // 如果已经有包装器，说明已经添加了标识圈
          if (wrappers.length === 0 && inline.length > 0) {
            // 如果没有包装器，说明需要手动添加（可能是正则替换失败）
            // 查找所有可能的行内公式元素
            const katexElements = containerRef.current.querySelectorAll('.katex:not(.katex-display)');
            katexElements.forEach((katexEl) => {
              if (!katexEl.parentElement?.classList.contains('inline-formula-wrapper')) {
                const wrapper = document.createElement('span');
                wrapper.className = 'inline-formula-wrapper';
                const badge = document.createElement('span');
                badge.className = 'formula-badge';
                badge.textContent = '公式';
                katexEl.parentNode?.insertBefore(wrapper, katexEl);
                wrapper.appendChild(badge);
                wrapper.appendChild(katexEl);
              }
            });
          }
        }
        containerRef.current.setAttribute('data-rendered', 'true');
        renderedContentRef.current = content;
        isRenderingRef.current = false;
        return;
      } else {
        // KaTeX 无法渲染某些公式，需要使用 MathJax
        console.debug('KaTeX 无法渲染部分公式，使用 MathJax 降级:', katexErrors);
      }
    } catch (err) {
      // KaTeX 渲染失败，回退到 MathJax
      console.debug('KaTeX 渲染失败，回退到 MathJax:', err);
    }

    // 使用 MathJax 渲染（延迟执行，等待 MathJax 加载）
    needsMathJaxRef.current = true; // 标记需要 MathJax
    
    // 触发 MathJax 初始化（如果需要）
    if (needsMathJaxRef.current && !window.MathJax) {
      // MathJax 未加载，触发加载
      const event = new CustomEvent('mathjax-needed');
      window.dispatchEvent(event);
    }
    
    if (window.MathJax) {
      const renderWithMathJax = () => {
        if (!window.MathJax || !containerRef.current) {
          // MathJax 未加载，直接显示原始内容
          containerRef.current!.innerHTML = content;
          containerRef.current!.setAttribute('data-rendered', 'true');
          renderedContentRef.current = content;
          isRenderingRef.current = false;
          return;
        }

        containerRef.current.innerHTML = content;

        const timeoutId = setTimeout(() => {
          if (isRenderingRef.current) {
            console.warn("MathJax 渲染超时");
            isRenderingRef.current = false;
            if (containerRef.current) {
              containerRef.current.setAttribute('data-rendered', 'true');
            }
          }
        }, 10000);

        window.MathJax.typesetPromise([containerRef.current])
          .then(() => {
            clearTimeout(timeoutId);
            if (containerRef.current) {
              // 为行内公式添加标识圈（MathJax 渲染后）
              addFormulaBadges(containerRef.current);
              containerRef.current.setAttribute('data-rendered', 'true');
              renderedContentRef.current = content;
            }
            isRenderingRef.current = false;
          })
          .catch((err: any) => {
            clearTimeout(timeoutId);
            // 捕获字体加载失败等错误，但不阻止显示内容
            const errorMessage = err?.message || String(err || '');
            if (errorMessage.includes('Failed to fetch') || 
                errorMessage.includes('getFontsForString') ||
                errorMessage.includes('font')) {
              console.debug("MathJax 字体加载失败（不影响显示）:", errorMessage);
              // 即使字体加载失败，内容已经渲染，继续执行
              if (containerRef.current) {
                addFormulaBadges(containerRef.current);
                containerRef.current.setAttribute('data-rendered', 'true');
                renderedContentRef.current = content;
              }
            } else {
              console.warn("MathJax 渲染错误:", errorMessage);
              if (containerRef.current) {
                containerRef.current.innerHTML = content; // 显示原始内容
                renderedContentRef.current = content;
              }
            }
            isRenderingRef.current = false;
            if (containerRef.current) {
              containerRef.current.setAttribute('data-rendered', 'true');
            }
          });
      };

      if (window.MathJax && window.__MATHJAX_INITIALIZED__) {
        renderWithMathJax();
      } else {
        // 等待 MathJax 加载
        const checkInterval = setInterval(() => {
          if (window.MathJax && window.__MATHJAX_INITIALIZED__) {
            clearInterval(checkInterval);
            renderWithMathJax();
          }
        }, 100);
        
        // 最多等待 5 秒
        setTimeout(() => {
          clearInterval(checkInterval);
          if (isRenderingRef.current) {
            renderWithMathJax();
          }
        }, 5000);
      }
    } else {
      // 不需要 MathJax，直接显示原始内容
      containerRef.current.innerHTML = content;
      containerRef.current.setAttribute('data-rendered', 'true');
      renderedContentRef.current = content;
      isRenderingRef.current = false;
    }
  }, [content]);

  return (
    <>
      <style jsx global>{`
        /* 行内公式标识圈样式 */
        .inline-formula-wrapper {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          vertical-align: middle;
        }
        
        .formula-badge {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 1.25rem;
          height: 1.25rem;
          border-radius: 50%;
          background: #3b82f6;
          color: white;
          font-size: 0.625rem;
          font-weight: 600;
          line-height: 1;
          flex-shrink: 0;
          box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }
        
        @media (prefers-color-scheme: dark) {
          .formula-badge {
            background: #60a5fa;
            color: #1e293b;
          }
        }
        
        /* 确保公式和标识圈对齐 */
        .inline-formula-wrapper .MathJax,
        .inline-formula-wrapper .katex {
          display: inline-block;
          vertical-align: middle;
        }
        
        /* 深色模式下公式颜色优化 */
        .dark .MathJax,
        .dark .MathJax * {
          color: #e2e8f0 !important;
        }
        
        .dark .MathJax_Display {
          color: #e2e8f0 !important;
        }
        
        .dark .MathJax_Display * {
          color: #e2e8f0 !important;
        }
        
        .dark .MathJax_SVG,
        .dark .MathJax_SVG * {
          fill: #e2e8f0 !important;
          stroke: #e2e8f0 !important;
        }
        
        /* KaTeX 深色模式优化 */
        .dark .katex {
          color: #e2e8f0 !important;
        }
        
        .dark .katex * {
          color: #e2e8f0 !important;
        }
        
        .dark .katex-display {
          color: #e2e8f0 !important;
        }
        
        .dark .katex-display * {
          color: #e2e8f0 !important;
        }
        
        .dark .katex .mord,
        .dark .katex .mop,
        .dark .katex .mbin,
        .dark .katex .mrel,
        .dark .katex .mopen,
        .dark .katex .mclose,
        .dark .katex .mpunct,
        .dark .katex .minner,
        .dark .katex .mord.mrel,
        .dark .katex .mord.mbin {
          color: #e2e8f0 !important;
        }
        
        /* 公式容器背景优化 */
        .dark .MathJax_Display {
          background: rgba(30, 41, 59, 0.8) !important;
          border-left-color: #60a5fa !important;
        }
        
        .dark .katex-display {
          background: rgba(30, 41, 59, 0.8) !important;
          padding: 1em 1.5em;
          border-radius: 8px;
          border-left: 4px solid #60a5fa;
          margin: 1.5em auto;
        }
      `}</style>
      <div
        ref={containerRef}
        className={className}
      />
    </>
  );
}

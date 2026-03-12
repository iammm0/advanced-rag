import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 启用 standalone 输出模式，用于 Docker 部署
  output: "standalone",
  
  // 实验性配置：支持大文件上传（200MB）
  experimental: {
    proxyClientMaxBodySize: "200mb",
  },
  
  // 代理配置：将所有 /api/* 请求代理到后端服务
  async rewrites() {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
    const isDev = process.env.NODE_ENV === "development";

    // 开发环境未配置时默认代理到 localhost:8000，便于本地联调
    const effectiveUrl = apiUrl || (isDev ? "http://localhost:8000" : "");

    if (!effectiveUrl) {
      // 生产且未配置：使用相对路径，由 nginx 等反向代理处理
      return [
        { source: "/api/:path*", destination: "/api/:path*" },
      ];
    }

    const destination = effectiveUrl.endsWith("/api") || effectiveUrl.endsWith("/api/")
      ? `${effectiveUrl}/:path*`
      : `${effectiveUrl}/api/:path*`;

    return [
      { source: "/api/:path*", destination },
    ];
  },
  // 开发环境配置
  ...(process.env.NODE_ENV === "development" && {
    // 在开发环境中，如果后端服务未运行，不阻塞前端
    onDemandEntries: {
      // 页面在内存中保持的时间（秒）
      maxInactiveAge: 60 * 1000,
      // 同时保持的页面数
      pagesBufferLength: 5,
    },
  }),
};

export default nextConfig;

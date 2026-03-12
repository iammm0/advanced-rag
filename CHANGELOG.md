# Changelog

本项目所有显著变更均记录于此文件。

格式遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/) 规范，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/) 规范。

---

## [Unreleased]

### 待开发

- GitHub Actions CI/CD 流水线
- 单元测试覆盖率提升
- 多模型切换 UI 支持

---

## [0.8.5] - 2026-03-12

### 新增

- 对话附件上传与入库功能（`POST /api/chat/conversation-attachment`）
- 对话附件处理状态查询接口
- 深度研究（deep-research）多 Agent 协作模式
- 知识空间管理 API（`/api/knowledge-spaces`）

### 变更

- 移除认证/用户系统、网络图谱、邮件通知、后台管理、资源社区、mph-agent 等非 RAG 功能
- 所有 API 改为匿名访问，无需登录
- 优化 Uvicorn 多 Worker 配置（生产环境支持最多 24 个 Worker）

### 修复

- 修复 jieba 库 `pkg_resources` 弃用警告
- 修复大文件上传超时问题（keep-alive 延长至 15 分钟）

---

## [0.8.0] - 2026-02-01

### 新增

- 多 Agent 协作框架（`agents/`）
  - CoordinatorAgent 协调器
  - DocumentRetrievalAgent 文档检索专家
  - ConceptExplanationAgent 概念解释专家
  - CodeAnalysisAgent 代码分析专家
  - FormulaAnalysisAgent 公式分析专家
  - SummaryAgent 摘要专家
- 智能分块路由（`chunking/router/`）
- 文档解析路由（`parsers/router/`）
- Unstructured 解析器支持复杂格式
- 语义分块器（基于 LangChain）

### 变更

- 重构 RAG 检索流程，提升向量检索精度
- 优化 PaddleOCR 集成方式

---

## [0.7.0] - 2025-12-15

### 新增

- Qdrant 向量数据库集成
- 文档解析支持 PDF、Word、Markdown、TXT
- 嵌入服务（`embedding/`）支持 Ollama 向量模型
- 滑动窗口分块器（`chunking/sliding_window_chunker.py`）

### 变更

- 切换向量数据库从 FAISS 到 Qdrant
- 优化文档上传流水线

---

## [0.6.0] - 2025-11-01

### 新增

- FastAPI 应用骨架搭建
- MongoDB 集成（对话历史、知识空间）
- 基础 RAG 检索实现
- Next.js 前端初版（聊天界面 + 知识库管理）
- Docker Compose 一键部署配置

---

[Unreleased]: https://github.com/iammm0/advanced-rag/compare/v0.8.5...HEAD
[0.8.5]: https://github.com/iammm0/advanced-rag/compare/v0.8.0...v0.8.5
[0.8.0]: https://github.com/iammm0/advanced-rag/compare/v0.7.0...v0.8.0
[0.7.0]: https://github.com/iammm0/advanced-rag/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/iammm0/advanced-rag/releases/tag/v0.6.0

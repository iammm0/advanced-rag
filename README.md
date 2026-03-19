# advanced-rag - 高级RAG系统

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)
[![Changelog](https://img.shields.io/badge/Changelog-Keep%20a%20Changelog-orange.svg)](CHANGELOG.md)

`advanced-rag` 是一个"纯粹的开源高级RAG系统"，基于 FastAPI + Next.js 构建，仅保留 **AI 助手对话（含深度研究/深度思考）** 与 **知识库检索/入库** 两大能力，所有 API **匿名访问**。

## ✨ 功能特性

### 核心功能
- **匿名对话**：无需登录即可使用对话与对话历史（全局）
- **深度研究（deep-research）**：多 Agent 协作输出深度研究结果
- **高阶 RAG 引擎**：
  - **混合分块**：规则分块（代码/公式）+ 语义分块（Ollama）
  - **双路索引**：向量索引（Qdrant）+ 知识图谱索引（Neo4j）
  - **混合检索**：向量 + 关键词 + 图谱关联检索
  - **精准重排**：引入 BGE-reranker 进行结果重排
- **知识库入库**：前端上传文档（PDF/Word/Markdown/TXT）→ 解析/混合分块/知识抽取/向量化 → 入库

### 说明
- 已移除：认证/用户系统/网络图谱/邮件/通知/后台管理/资源社区/Comsol(mph-agent) 等非 RAG 功能。

## 🛠️ 技术栈

### 后端技术
- **框架**: FastAPI 0.104+
- **数据库**: 
  - MongoDB - 用户数据和对话历史
  - Qdrant - 向量数据库
  - Neo4j - 图数据库（知识图谱）
  - Redis - 缓存服务
- **AI模型**: Ollama（支持本地模型推理）
- **文档处理**: 
  - PyPDF2, PyMuPDF - PDF解析
  - python-docx - Word文档解析
  - PaddleOCR - OCR识别
  - Unstructured - 复杂格式解析
- **文本处理**: 
  - LangChain - 文本分块和语义处理
  - sentence-transformers - 重排模型
  - jieba - 中文分词

### 核心模块
- **代理系统** (`agents/`): 多代理协作框架
- **解析器** (`parsers/`): 多格式文档解析
- **分块器** (`chunking/`): 智能文本分块（含混合分块器）
- **检索系统** (`retrieval/`): RAG检索实现（含图谱检索与重排）
- **服务层** (`services/`): 业务逻辑服务（含知识抽取）
- **路由层** (`routers/`): API路由定义
- **评测系统** (`eval/`): 自动化评测脚本

## 📁 项目结构（简要）

```
advanced-rag/
├── main.py            # FastAPI 应用入口
├── agents/            # 多Agent协作框架
├── routers/           # 核心API路由（聊天 / 文档 / 知识空间 / 检索 / 健康检查）
├── database/          # MongoDB / Qdrant 等数据库客户端
├── parsers/           # 文档解析器
├── chunking/          # 文本分块
├── embedding/         # 向量化服务
├── utils/             # 通用工具与监控
├── middleware/        # 日志等中间件
├── web/               # Next.js 前端（聊天 + 知识空间）
└── scripts/           # 辅助脚本与迁移工具

## 🚀 快速开始

### 环境要求
- Python 3.9+
- MongoDB 4.4+（**启动时若未连接不会阻止进程**，服务会先启动，依赖 MongoDB 的接口在连接前不可用）
- Qdrant（可通过Docker运行；未连接时仅告警，不阻止启动）
- Redis（可选，用于缓存）
- Neo4j（可选，用于知识图谱）
- Ollama（本地AI模型服务）

### 安装依赖

#### 1. 安装Python依赖
```bash
pip install -r requirements.txt
```

#### 2. 下载第三方依赖（构建前必需）
项目使用 PaddleOCR 等第三方库，需要先下载到本地：

**Linux/macOS:**
```bash
chmod +x download_dependencies.sh
./download_dependencies.sh
```

**Windows CMD:**
```cmd
download_dependencies.cmd
```

**Windows PowerShell:**
```powershell
.\download_dependencies.ps1
```

#### 3. 安装系统依赖（可选）
如果需要在资源上传时自动生成视频封面，需要安装 `ffmpeg`：

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
下载并安装 ffmpeg: https://ffmpeg.org/download.html
确保 ffmpeg 在系统 PATH 中。

### 环境配置

创建 `.env` 文件并配置相关环境变量：

```bash
# 应用配置
ENVIRONMENT=development
SECRET_KEY=your-secret-key-here  # 生产环境必须修改
API_HOST=0.0.0.0
API_PORT=8000

# MongoDB配置
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=advanced_rag

# Qdrant配置
QDRANT_URL=http://localhost:6333
QDRANT_API_KEY=  # 可选

# Neo4j配置（可选）
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password

# Redis配置（可选）
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gpt-oss:20b  # 默认模型
OLLAMA_EMBEDDING_MODEL=nomic-embed-text  # 向量化模型

# 文件上传配置
MAX_UPLOAD_SIZE=104857600  # 100MB
UPLOAD_DIR=./uploads

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/advanced-rag.log
```

### 启动服务

#### 开发模式
```bash
python main.py
```

或使用 uvicorn：
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### 使用 Docker Compose
```bash
docker-compose up -d
```

服务启动后，访问：
- API文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health

## 📚 核心API接口（当前版本）

- `POST /api/chat` - 常规对话（流式SSE）
- `POST /api/chat/deep-research` - 深度研究模式
- `POST /api/chat/conversation-attachment` - 对话附件上传并入库
- `GET /api/chat/conversation-attachment/{conversation_id}/{file_id}/status` - 对话附件处理状态
- `POST /api/documents/upload` - 文档上传入库
- `GET /api/documents` - 文档列表
- `GET /api/knowledge-spaces` - 知识空间列表
- `GET /health` - 健康检查

## 🐳 Docker 部署

### 构建镜像

**重要：构建前需要先下载GitHub依赖**

为了避免构建时从GitHub拉取依赖（与国内镜像源冲突），需要先下载依赖到本地（见上方"下载第三方依赖"部分）。

下载完成后，进行Docker构建：
```bash
docker build -t advanced-rag .
```

### 运行容器
```bash
docker run -d \
  -p 8000:8000 \
  --name advanced-rag \
  --env-file .env \
  advanced-rag
```

### 使用 Docker Compose
```bash
docker-compose up -d
```

Docker Compose 会自动启动 MongoDB、Qdrant、Redis、Neo4j 等服务。

## 🔧 开发指南

### 代码结构说明
- **路由层** (`routers/`): 处理HTTP请求，参数验证
- **服务层** (`services/`): 业务逻辑实现
- **模型层** (`models/`): 数据模型定义
- **数据库层** (`database/`): 数据库连接和操作
- **工具层** (`utils/`): 通用工具函数

### 添加新功能
1. 在 `models/` 中定义数据模型
2. 在 `services/` 中实现业务逻辑
3. 在 `routers/` 中添加API路由
4. 在 `main.py` 中注册路由

### 测试
运行测试脚本：
```bash
python test_agent_workflow.py
```

查看测试文档：
```bash
cat TESTING.md
```

## 📖 相关文档

- [测试文档](TESTING.md) - 测试指南和示例
- [变更日志](CHANGELOG.md) - 版本发布历史
- [贡献指南](CONTRIBUTING.md) - 如何参与贡献
- [行为准则](CODE_OF_CONDUCT.md) - 社区行为规范
- [Redis配置](REDIS_CONFIG.md) - Redis缓存配置说明
- [分块器文档](chunking/README.md) - 文本分块功能说明
- [解析器文档](parsers/README.md) - 文档解析功能说明
- [工具文档](utils/README.md) - 工具函数说明
- [迁移脚本文档](scripts/README_MIGRATIONS.md) - 数据迁移指南

## 🤝 贡献指南

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feat/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feat/AmazingFeature`)
5. 开启 Pull Request

## 📝 许可证

本项目采用 [MIT 许可证](LICENSE)，版权所有 © 2026 [iammm0](https://github.com/iammm0)。

## 🙏 致谢

- FastAPI - 现代、快速的Web框架
- Ollama - 本地AI模型运行
- Qdrant - 向量数据库
- LangChain - LLM应用框架
- PaddleOCR - OCR识别引擎

---

如有问题或建议，请提交 Issue 或 Pull Request。

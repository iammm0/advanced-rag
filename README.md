# advanced-rag - 高级RAG系统

`advanced-rag` 是一个“纯粹的高级RAG系统”，基于 FastAPI + Next.js 构建，仅保留 **AI 助手对话（含深度研究/深度思考）** 与 **知识库检索/入库** 两大能力，所有 API **匿名访问**。

## ✨ 功能特性

### 核心功能
- **匿名对话**：无需登录即可使用对话与对话历史（全局）
- **深度研究（deep-research）**：多 Agent 协作输出深度研究结果
- **RAG 检索增强**：向量检索 + 来源返回（Qdrant）
- **知识库入库**：前端上传文档（PDF/Word/Markdown/TXT）→ 解析/分块/向量化 → 入库

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
  - jieba - 中文分词

### 核心模块
- **代理系统** (`agents/`): 多代理协作框架
- **解析器** (`parsers/`): 多格式文档解析
- **分块器** (`chunking/`): 智能文本分块
- **检索系统** (`retrieval/`): RAG检索实现
- **服务层** (`services/`): 业务逻辑服务
- **路由层** (`routers/`): API路由定义

## 📁 项目结构

```
sensor-api/
├── main.py                 # FastAPI应用入口
├── requirements.txt        # Python依赖
├── Dockerfile              # Docker构建文件
├── docker-compose.yml      # Docker Compose配置
│
├── agents/                 # 代理系统
│   ├── base/              # 基础代理类
│   ├── coordinator/       # 协调器代理
│   ├── experts/           # 专家代理（代码分析、概念解释等）
│   ├── network/           # 网络代理
│   ├── physics_assistant/ # 物理助手代理
│   └── workflow/          # 工作流管理
│
├── routers/               # API路由
│   ├── auth.py           # 认证路由
│   ├── chat.py           # 聊天路由
│   ├── documents.py      # 文档管理路由
│   ├── assistants.py     # 助手管理路由
│   ├── models.py         # 模型管理路由
│   ├── resources.py      # 资源管理路由
│   ├── users.py          # 用户管理路由
│   ├── network.py        # 网络同步路由
│   ├── emails.py         # 邮件路由
│   └── health.py         # 健康检查路由
│
├── services/              # 服务层
│   ├── rag_service.py    # RAG检索服务
│   ├── ollama_service.py # Ollama模型服务
│   ├── ai_tools.py       # AI工具服务
│   ├── cache_service.py # 缓存服务
│   ├── email_service.py  # 邮件服务
│   ├── network_sync_service.py # 网络同步服务
│   └── ...               # 其他服务
│
├── models/                # 数据模型
│   ├── user.py           # 用户模型
│   ├── course_assistant.py # 课程助手模型
│   ├── resource.py       # 资源模型
│   └── email.py          # 邮件模型
│
├── database/              # 数据库客户端
│   ├── mongodb.py        # MongoDB客户端
│   ├── qdrant_client.py  # Qdrant客户端
│   └── neo4j_client.py   # Neo4j客户端
│
├── parsers/               # 文档解析器
│   ├── pdf_parser.py     # PDF解析器
│   ├── word_parser.py    # Word解析器
│   ├── markdown_parser.py # Markdown解析器
│   └── router/           # 解析路由
│
├── chunking/              # 文本分块
│   ├── smart_chunker.py  # 智能分块器
│   ├── langchain/        # LangChain分块器
│   └── router/           # 分块路由
│
├── retrieval/             # 检索模块
│   └── rag_retriever.py  # RAG检索器
│
├── embedding/             # 向量化
│   └── embedding_service.py # 向量化服务
│
├── utils/                 # 工具函数
│   ├── logger.py         # 日志工具
│   ├── lifespan.py       # 应用生命周期
│   ├── code_analyzer.py  # 代码分析工具
│   ├── formula_analyzer.py # 公式分析工具
│   └── ...               # 其他工具
│
├── middleware/            # 中间件
│   ├── auth_middleware.py # 认证中间件
│   └── logging_middleware.py # 日志中间件
│
├── scripts/               # 脚本工具
│   ├── init_neo4j.py     # Neo4j初始化
│   └── migrate_*.py      # 数据迁移脚本
│
└── vendor/                # 第三方依赖（PaddleOCR等）
```

## 🚀 快速开始

### 环境要求
- Python 3.9+
- MongoDB 4.4+
- Qdrant（可通过Docker运行）
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
MONGODB_DB_NAME=sensor_ai

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
LOG_FILE=./logs/sensor-api.log
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
- 健康检查: http://localhost:8000/api/health

## 📚 API接口文档

### 认证接口
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/refresh` - 刷新Token

### 聊天接口
- `POST /api/chat/conversations` - 创建对话
- `GET /api/chat/conversations` - 获取对话列表
- `GET /api/chat/conversations/{id}` - 获取对话详情
- `POST /api/chat/conversations/{id}/messages` - 发送消息
- `POST /api/chat/stream` - 流式聊天
- `DELETE /api/chat/conversations/{id}` - 删除对话

### 助手管理接口
- `GET /api/assistants` - 获取助手列表
- `POST /api/assistants` - 创建助手（仅管理员）
- `PUT /api/assistants/{id}` - 更新助手（仅管理员）
- `DELETE /api/assistants/{id}` - 删除助手（仅管理员）

### 文档管理接口（需要管理员权限）
- `POST /api/documents/upload` - 上传文档
- `GET /api/documents/` - 获取文档列表
- `GET /api/documents/{id}` - 获取文档详情
- `DELETE /api/documents/{id}` - 删除文档
- `POST /api/documents/{id}/reindex` - 重新索引文档

### 资源管理接口
- `POST /api/resources/upload` - 上传资源
- `GET /api/resources/` - 获取资源列表
- `GET /api/resources/{id}` - 获取资源详情
- `DELETE /api/resources/{id}` - 删除资源

### 用户管理接口（需要管理员权限）
- `GET /api/users` - 获取用户列表
- `GET /api/users/{id}` - 获取用户详情
- `PUT /api/users/{id}` - 更新用户信息
- `DELETE /api/users/{id}` - 删除用户

### 网络同步接口
- `POST /api/network/sync` - 同步网络节点
- `GET /api/network/nodes` - 获取网络节点
- `GET /api/network/graph` - 获取知识图谱

### 邮件接口
- `POST /api/emails/send` - 发送邮件
- `GET /api/emails/` - 获取邮件列表

### 健康检查
- `GET /api/health` - 系统健康检查

完整的API文档可在启动服务后访问 `/docs` 查看交互式文档。

## 🐳 Docker 部署

### 构建镜像

**重要：构建前需要先下载GitHub依赖**

为了避免构建时从GitHub拉取依赖（与国内镜像源冲突），需要先下载依赖到本地（见上方"下载第三方依赖"部分）。

下载完成后，进行Docker构建：
```bash
docker build -t sensor-api .
```

### 运行容器
```bash
docker run -d \
  -p 8000:8000 \
  --name sensor-api \
  --env-file .env \
  sensor-api
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

本项目采用 MIT 许可证。

## 🙏 致谢

- FastAPI - 现代、快速的Web框架
- Ollama - 本地AI模型运行
- Qdrant - 向量数据库
- LangChain - LLM应用框架
- PaddleOCR - OCR识别引擎

---

如有问题或建议，请提交 Issue 或 Pull Request。

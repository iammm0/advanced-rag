# 前端应用模块（advanced-rag-web）

`advanced-rag` 的 Next.js 前端应用，提供用户交互界面（**匿名访问**）。仅保留 **聊天（含深度研究）** 与 **知识库上传/列表**。

## 功能特性

- **聊天界面**：实时聊天，支持流式文本显示、对话历史侧边栏
- **深度研究**：多 Agent 协作输出深度研究内容
- **知识库**：上传文档入库、列表/进度展示，聊天中可开启 RAG 检索增强并显示 sources
- **响应式设计**：支持移动端和桌面端

## 技术栈

- Next.js 16
- React 19
- TypeScript
- Tailwind CSS

## 安装依赖

```bash
npm install
```

## 开发

```bash
npm run dev
```

访问 `http://localhost:3000`

## 构建

```bash
npm run build
npm start
```

## 环境配置

创建 `.env.local` 文件：

```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

如果不设置 `NEXT_PUBLIC_API_URL`，前端默认使用 `http://localhost:8000` 作为后端地址。

## 页面说明

### 聊天页面 (`/chat`)

- 所有用户可访问
- 支持选择AI助手
- 支持选择文档进行针对性检索
- 支持流式和非流式回复
- 支持编辑消息和重新生成

### 助手管理页面 (`/assistants`)

- 所有用户可查看助手列表
- 管理员可以创建、编辑、删除助手
- 管理员可以设置默认助手

### 用户统计页面 (`/users`)

- 仅管理员可访问
- 查看所有用户的详细信息
- 查看用户的对话记录

### 知识库页面 (`/documents`)

- 仅管理员可访问
- 上传文档到指定助手的知识库
- 查看文档列表和处理进度
- 管理文档（删除、重命名、重新处理）

## 目录结构

```
sensor-web/
├── app/                # Next.js App Router页面
│   ├── chat/          # 聊天页面（支持助手选择）
│   ├── login/         # 登录页面
│   ├── documents/     # 文档管理页面（管理员）
│   ├── assistants/    # 助手管理页面
│   ├── users/         # 用户统计页面（管理员）
│   └── profile/       # 个人中心页面
├── components/        # React组件
│   ├── ChatMessage.tsx      # 聊天消息组件
│   ├── ChatSidebar.tsx      # 聊天侧边栏
│   ├── StreamingText.tsx    # 流式文本显示
│   ├── DocumentUpload.tsx   # 文档上传组件
│   ├── Navbar.tsx           # 导航栏
│   └── Layout.tsx           # 布局组件
├── lib/               # 工具函数
│   ├── api.ts        # API客户端（包含所有API方法）
│   ├── auth.ts       # 认证工具
│   ├── conversation.ts  # 对话管理工具
│   └── useAuth.ts    # 认证Hook
└── types/             # TypeScript类型定义
    ├── chat.ts       # 聊天相关类型
    ├── conversation.ts  # 对话相关类型
    └── assistant.ts   # 助手相关类型
```

## 主要功能说明

### 聊天功能

- 支持选择不同的AI助手进行对话
- 支持流式和非流式回复
- 支持RAG检索，根据选择的助手检索对应的知识库
- 支持编辑消息和重新生成回答
- 支持文档选择，可以指定在特定文档范围内检索

### 助手管理（所有用户可查看，管理员可管理）

- 查看所有可用的AI助手
- 管理员可以创建、编辑、删除助手
- 管理员可以设置默认助手
- 每个助手显示系统提示词预览和集合名称

### 用户统计（仅管理员）

- 查看所有用户的详细信息
- 查看用户的在线状态和最后活跃时间
- 查看用户的对话数量统计
- 查看用户的完整对话记录（只读）

### 知识库管理（仅管理员）

- 上传文档到指定助手的知识库
- 查看文档列表和处理进度
- 删除文档（会同时清理向量数据）
- 重新处理失败的文档

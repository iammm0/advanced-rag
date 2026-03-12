# Chunking 模块结构说明

## 目录结构

```
chunking/
├── base.py                    # 分块器基类
├── simple_chunker.py          # 简单分块器（基础实现，无外部依赖）
├── smart_chunker.py           # 智能分块器（处理数学公式等）
├── sliding_window_chunker.py  # 滑动窗口分块器
├── router/                    # 分块路由模块
│   ├── __init__.py
│   └── content_analyzer.py    # 内容分析路由器（根据内容特征选择合适的分块器）
└── langchain/                 # LangChain 分块器模块（依赖外部库）
    ├── __init__.py
    ├── recursive_chunker.py   # 递归分块器（用于高度结构化内容）
    └── semantic_chunker.py    # 语义分块器（用于需要保持语义连贯性的内容）
```

## 设计说明

### 1. 基础分块器（根目录）
- **simple_chunker.py**: 简单分块器，按固定大小分割，无外部依赖
- **smart_chunker.py**: 智能分块器，能够识别和保护数学公式
- **sliding_window_chunker.py**: 滑动窗口分块器

### 2. 路由模块（router/）
- **content_analyzer.py**: 内容分析路由器，根据文档内容特征（文件类型、代码块数量、LaTeX公式数量、段落结构等）自动选择合适的分块器

### 3. LangChain 分块器（langchain/）
- **recursive_chunker.py**: 基于 LangChain 的递归分块器，用于高度结构化的内容（代码、论文等）
- **semantic_chunker.py**: 基于 LangChain 的语义分块器，用于需要保持语义连贯性的内容（报告、文章等）

## 使用方式

### 直接使用分块器

```python
from chunking.simple_chunker import SimpleChunker
from chunking.langchain.recursive_chunker import RecursiveChunker
from chunking.langchain.semantic_chunker import SemanticChunker

# 使用简单分块器
chunker = SimpleChunker(chunk_size=500, chunk_overlap=50)
chunks = chunker.chunk(text)

# 使用递归分块器
chunker = RecursiveChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk(text)

# 使用语义分块器
chunker = SemanticChunker(chunk_size=1000, chunk_overlap=200)
chunks = chunker.chunk(text)
```

### 使用内容分析路由器（推荐）

```python
from chunking.router import ContentAnalyzer

# 创建路由器
analyzer = ContentAnalyzer()

# 自动选择合适的分块器
chunker_type, chunker = analyzer.route(text, metadata)

# 使用选中的分块器
chunks = chunker.chunk(text, metadata)
```

## 重构说明

### 重构前的问题
- 分块器实现和路由逻辑混在一起，不够清晰
- `router` 目录下既有路由逻辑又有分块器实现，命名容易引起误解

### 重构后的改进
- **清晰的模块划分**：基础分块器、路由逻辑、LangChain 分块器分别放在不同目录
- **明确的依赖关系**：依赖外部库的分块器独立放在 `langchain` 目录
- **更好的可维护性**：新增分块器时，根据依赖关系选择合适的位置

## 向后兼容性

重构后的代码保持了向后兼容性：
- 通过 `chunking/__init__.py` 导出所有分块器
- 通过 `chunking/router/__init__.py` 导出路由器和 LangChain 分块器
- 现有的导入语句无需修改


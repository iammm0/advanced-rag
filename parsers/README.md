# Parsers 模块结构说明

## 目录结构

```
parsers/
├── base.py                    # 解析器基类
├── pdf_parser.py              # PDF解析器（依赖PyPDF2）
├── word_parser.py             # Word解析器
├── text_parser.py             # 文本解析器
├── markdown_parser.py         # Markdown解析器
├── parser_factory.py          # 解析器工厂
├── router/                    # 解析路由模块
│   ├── __init__.py
│   └── parsing_router.py      # 解析路由器（根据文档特征选择合适解析器）
├── utils/                     # 解析工具模块
│   ├── __init__.py
│   ├── unified_loader.py      # 统一文档加载器
│   └── result_synthesizer.py  # 结果合成器
└── unstructured/              # Unstructured解析器模块（依赖外部库）
    ├── __init__.py
    └── unstructured_parser.py # Unstructured解析器（用于复杂格式文档）
```

## 设计说明

### 1. 基础解析器（根目录）
- **base.py**: 解析器基类，定义了解析器的接口
- **pdf_parser.py**: PDF解析器，支持文本版和扫描版PDF（依赖PyPDF2）
- **word_parser.py**: Word文档解析器
- **text_parser.py**: 纯文本解析器
- **markdown_parser.py**: Markdown解析器
- **parser_factory.py**: 解析器工厂，根据文件扩展名返回合适的解析器

### 2. 路由模块（router/）
- **parsing_router.py**: 解析路由器，根据文档类型和特征（文件大小、是否包含表格等）智能选择合适解析器

### 3. 工具模块（utils/）
- **unified_loader.py**: 统一文档加载器，负责加载和验证文档文件
- **result_synthesizer.py**: 结果合成器，统一不同解析器的输出格式

### 4. Unstructured解析器（unstructured/）
- **unstructured_parser.py**: 基于Unstructured库的解析器，用于复杂格式文档的布局分析（依赖unstructured库）

## 增强功能

### 图片OCR（PDFParser）
- 使用PaddleOCR从PDF中的图片提取文字
- 自动识别扫描版PDF中的图片并进行OCR
- 提取的图片文字会合并到文档文本中

### 表格提取（PDFParser, WordParser, MarkdownParser）
- 自动识别文档中的表格
- 保留表格的HTML和Markdown格式，便于前端渲染
- 提取表格的语义结构信息（行数、列数、数据类型等）

### 公式分析（PDFParser, WordParser, MarkdownParser）
- 提取公式中的变量（包括带下标的变量）
- 提取公式中的关系（等式、不等式）
- 分析公式结构（是否包含分数、根号、积分等）
- 计算公式复杂度

### 代码分析（MarkdownParser）
- 自动检测代码块的编程语言
- 提取函数定义、类定义、导入语句
- 提取变量名和关键字
- 估算代码复杂度

所有增强功能的结果都存储在解析结果的`metadata`字段中，不会影响基本的文本提取功能。

## 使用方式

### 直接使用解析器

```python
from parsers.pdf_parser import PDFParser
from parsers.word_parser import WordParser
from parsers.unstructured.unstructured_parser import UnstructuredParser

# 使用PDF解析器
parser = PDFParser()
result = parser.parse("document.pdf")

# 使用Word解析器
parser = WordParser()
result = parser.parse("document.docx")

# 使用Unstructured解析器
parser = UnstructuredParser()
result = parser.parse("complex_document.pdf")
```

### 使用解析器工厂

```python
from parsers.parser_factory import ParserFactory

# 根据文件路径自动选择解析器
parser = ParserFactory.get_parser("document.pdf")
if parser:
    result = parser.parse("document.pdf")
```

### 使用解析路由器（推荐）

```python
from parsers.router import ParsingRouter
from parsers.utils import ResultSynthesizer

# 创建路由器
router = ParsingRouter()
synthesizer = ResultSynthesizer()

# 自动选择合适解析器
parser_type, parser = router.route("document.pdf")

# 解析文档
result = parser.parse("document.pdf")

# 合成结果
synthesized_result = synthesizer.synthesize(result, parser_type, "document.pdf")
```

## 重构说明

### 重构前的问题
- `enhanced` 目录下混合了路由逻辑、工具类和依赖外部库的解析器，不够清晰
- 命名不够明确，无法直观看出模块的依赖关系

### 重构后的改进
- **清晰的模块划分**：基础解析器、路由逻辑、工具类、Unstructured解析器分别放在不同目录
- **明确的依赖关系**：依赖外部库的解析器独立放在 `unstructured` 目录
- **更好的可维护性**：新增解析器时，根据依赖关系选择合适的位置

## 向后兼容性

重构后的代码保持了向后兼容性：
- 通过 `parsers/__init__.py` 导出所有解析器和工具类
- 通过 `parsers/router/__init__.py` 导出路由器
- 现有的导入语句无需修改（通过 `__init__.py` 的重新导出）


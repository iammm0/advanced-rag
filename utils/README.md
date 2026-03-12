# 工具模块说明

本目录包含文档解析和处理的增强工具模块。

## 模块列表

### 1. image_ocr.py - 图片OCR工具

使用PaddleOCR从图片中提取文字内容。

**功能：**
- 从图片文件中提取文字
- 从PDF文档中提取图片并进行OCR识别
- 支持中英文识别
- 返回文字内容、置信度和位置信息

**使用示例：**
```python
from utils.image_ocr import image_ocr

# 从图片提取文字
result = image_ocr.extract_text_from_image("image.jpg")
print(result["text"])  # 提取的文字内容
print(result["confidence"])  # 平均置信度

# 从PDF提取图片文字
pdf_result = image_ocr.extract_text_from_pdf_images("document.pdf")
print(pdf_result["total_text"])  # 所有图片的文字内容
```

**依赖：**
- PaddleOCR（已在requirements.txt中）

### 2. table_extractor.py - 表格提取工具

从文档中提取表格并转换为多种格式（HTML、Markdown）。

**功能：**
- 识别Markdown格式表格
- 识别管道分隔的表格（| 分隔）
- 转换为HTML格式（便于前端渲染）
- 转换为Markdown格式
- 提取表格的语义结构信息（行数、列数、数据类型等）

**使用示例：**
```python
from utils.table_extractor import TableExtractor

# 从文本中提取表格
text = """
| 列1 | 列2 | 列3 |
|-----|-----|-----|
| 值1 | 值2 | 值3 |
"""
tables = TableExtractor.extract_table_from_text(text)

for table in tables:
    print(table["html"])  # HTML格式
    print(table["markdown"])  # Markdown格式
    print(table["semantic"])  # 语义结构信息
```

### 3. formula_analyzer.py - 公式分析工具

分析数学公式，提取变量、关系和语义信息。

**功能：**
- 提取公式中的变量（包括带下标的变量）
- 提取公式中的关系（等式、不等式）
- 提取公式中的函数
- 分析公式结构（是否包含分数、根号、积分等）
- 计算公式复杂度

**使用示例：**
```python
from utils.formula_analyzer import FormulaAnalyzer

# 分析单个公式
formula = "$$E = mc^2$$"
analysis = FormulaAnalyzer.analyze_formula(formula)
print(analysis["variables"])  # ['E', 'm', 'c']
print(analysis["relations"])  # [{'type': 'equality', 'operator': '=', ...}]
print(analysis["structure"])  # {'is_equation': True, ...}

# 从文本中提取所有公式并分析
text = "根据公式 $F = ma$ 和 $E = mc^2$..."
formulas_info = FormulaAnalyzer.extract_all_formulas_info(text)
```

### 4. code_analyzer.py - 代码分析工具

分析代码块，提取语法树和语义信息。

**功能：**
- 自动检测编程语言（Python、JavaScript、Java、C++等）
- 提取函数定义（函数名、参数）
- 提取类定义
- 提取导入语句
- 提取变量名和关键字
- 估算代码复杂度

**使用示例：**
```python
from utils.code_analyzer import CodeAnalyzer

code = """
def calculate_sum(a, b):
    return a + b

class Calculator:
    def __init__(self):
        self.value = 0
"""

# 分析代码块
analysis = CodeAnalyzer.analyze_code_block(code)
print(analysis["language"])  # 'python'
print(analysis["functions"])  # [{'name': 'calculate_sum', 'parameters': ['a', 'b'], ...}]
print(analysis["classes"])  # [{'name': 'Calculator', ...}]
print(analysis["complexity"])  # 'simple' / 'moderate' / 'complex'
```

## 集成到解析器

这些工具已经集成到以下解析器中：

- **PDFParser**: 支持图片OCR、表格提取、公式分析
- **WordParser**: 支持表格提取、公式分析、图片提取
- **MarkdownParser**: 支持表格提取、代码分析、公式分析

解析结果会在`metadata`字段中包含这些增强信息：

```python
result = parser.parse("document.pdf")
metadata = result["metadata"]

# 图片OCR结果
if "image_ocr" in metadata:
    print(metadata["image_ocr"])

# 表格信息
if "tables" in metadata:
    for table in metadata["tables"]:
        print(table["html"])  # HTML格式表格
        print(table["semantic"])  # 语义结构

# 公式信息
if "formulas" in metadata:
    for formula in metadata["formulas"]:
        print(formula["variables"])  # 变量列表
        print(formula["relations"])  # 关系列表

# 代码块信息（仅Markdown）
if "code_blocks" in metadata:
    for code_block in metadata["code_blocks"]:
        print(code_block["language"])  # 编程语言
        print(code_block["analysis"])  # 代码分析结果
```

## 注意事项

1. **PaddleOCR**: 首次使用时会自动下载模型，可能需要一些时间
2. **性能**: OCR和代码分析可能较慢，建议在后台异步处理
3. **错误处理**: 所有工具都包含错误处理，如果某个功能失败，不会影响基本的文本提取


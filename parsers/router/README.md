# 解析路由器说明

## 功能概述

解析路由器（`ParsingRouter`）根据文档的特征智能选择最合适的解析器。

## 路由策略

### 1. Unstructured解析器（复杂格式）

**适用场景：**
- 扫描版PDF（需要OCR和布局分析）
- 包含大量图片的文档（>5张）
- 包含复杂表格的文档（>3个表格）
- 大型文档（>2MB）
- 包含复杂布局的文档

**检测方法：**
- 扫描版PDF：检查前3页的文本提取量，如果平均每页少于50个字符，判定为扫描版
- Word文档：检查表格数量、图片数量、段落数量
- PDF文档：检查前几页是否有文本，如果没有文本可能是图片PDF
- 文件大小：超过2MB的文件优先使用Unstructured

### 2. 原有解析器（标准格式）

**适用场景：**
- 文本版PDF
- 简单的Word文档（无复杂表格、图片）
- Markdown文档
- 纯文本文件

**检测方法：**
- 简单格式文件（.txt, .md）直接使用原有解析器
- 对于PDF和Word，如果未检测到复杂格式，使用原有解析器

## 使用示例

```python
from parsers.router import ParsingRouter

router = ParsingRouter()
parser_type, parser = router.route("document.pdf")

# parser_type 可能是：
# - ParsingRouter.PARSER_TYPE_UNSTRUCTURED
# - ParsingRouter.PARSER_TYPE_LEGACY

result = parser.parse("document.pdf")
```

## 日志输出

路由器会输出详细的日志信息，帮助理解路由决策：

```
✓ 路由到 Unstructured 解析器: document.pdf (复杂格式)
✓ 路由到原有解析器: document.pdf (标准格式)
```

## 错误处理

- 如果Unstructured解析器初始化失败，会自动回退到原有解析器
- 如果检测过程中出错，会记录警告并继续处理
- 如果找不到合适的解析器，会抛出`ValueError`


"""文档解析器模块"""
# 保持向后兼容，导出原有模块
from .base import BaseParser
from .parser_factory import ParserFactory
from .pdf_parser import PDFParser
from .word_parser import WordParser
from .text_parser import TextParser
from .markdown_parser import MarkdownParser

# 导出路由模块和工具模块
try:
    from .router import ParsingRouter
    from .utils import UnifiedLoader, ResultSynthesizer
    from .unstructured import UnstructuredParser
    
    __all__ = [
        "BaseParser",
        "ParserFactory",
        "PDFParser",
        "WordParser",
        "TextParser",
        "MarkdownParser",
        "UnifiedLoader",
        "ParsingRouter",
        "ResultSynthesizer",
        "UnstructuredParser"
    ]
except ImportError:
    # 如果路由模块或工具模块不可用，只导出原有模块
    __all__ = [
        "BaseParser",
        "ParserFactory",
        "PDFParser",
        "WordParser",
        "TextParser",
        "MarkdownParser"
    ]

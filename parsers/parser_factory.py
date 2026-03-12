"""文档解析器工厂"""
from typing import Optional
from .base import BaseParser
from .pdf_parser import PDFParser
from .text_parser import TextParser
from .markdown_parser import MarkdownParser
from .word_parser import WordParser


class ParserFactory:
    """文档解析器工厂类"""
    
    _parsers: list[BaseParser] = [
        PDFParser(),
        TextParser(),
        MarkdownParser(),
        WordParser()
    ]
    
    @classmethod
    def get_parser(cls, file_path: str) -> Optional[BaseParser]:
        """
        根据文件路径获取合适的解析器
        
        Args:
            file_path: 文件路径
        
        Returns:
            解析器实例，如果找不到则返回None
        """
        for parser in cls._parsers:
            if parser.can_parse(file_path):
                return parser
        return None
    
    @classmethod
    def register_parser(cls, parser: BaseParser):
        """注册新的解析器"""
        cls._parsers.append(parser)


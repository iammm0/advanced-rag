"""文本文件解析器"""
from typing import Dict, Any, List
from .base import BaseParser
import chardet


class TextParser(BaseParser):
    """文本文件解析器（支持TXT等）"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析文本文件"""
        try:
            # 检测文件编码
            with open(file_path, 'rb') as file:
                raw_data = file.read()
                encoding_result = chardet.detect(raw_data)
                encoding = encoding_result.get('encoding', 'utf-8')
            
            # 使用检测到的编码读取文件
            with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
                text = file.read()
            
            return {
                "text": text,
                "metadata": {
                    "encoding": encoding,
                    "lines": len(text.split('\n'))
                }
            }
        except Exception as e:
            raise Exception(f"Failed to parse text file: {e}")
    
    def supported_extensions(self) -> List[str]:
        return ["txt", "text"]


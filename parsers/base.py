"""文档解析器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any


class BaseParser(ABC):
    """文档解析器基类"""
    
    @abstractmethod
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析文档
        
        Args:
            file_path: 文件路径
        
        Returns:
            包含文本内容和元数据的字典
        """
        pass
    
    @abstractmethod
    def supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名列表"""
        pass
    
    def can_parse(self, file_path: str) -> bool:
        """检查是否可以解析该文件"""
        ext = file_path.lower().split('.')[-1]
        return ext in self.supported_extensions()


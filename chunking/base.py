"""文本分块器基类"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class BaseChunker(ABC):
    """文本分块器基类"""
    
    @abstractmethod
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        将文本分割成块
        
        Args:
            text: 要分割的文本
            metadata: 可选的元数据
        
        Returns:
            文本块列表，每个块包含text和metadata
        """
        pass


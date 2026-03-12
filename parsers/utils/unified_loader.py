"""统一加载器 - 负责加载各种格式的文档文件"""
import os
from typing import Dict, Any, Optional
from utils.logger import logger


class UnifiedLoader:
    """统一文档加载器"""
    
    def __init__(self):
        """初始化加载器"""
        pass
    
    def load(self, file_path: str) -> Dict[str, Any]:
        """
        加载文档文件
        
        Args:
            file_path: 文件路径
        
        Returns:
            包含文件信息的字典：
            - file_path: 文件路径
            - file_size: 文件大小（字节）
            - file_ext: 文件扩展名
            - exists: 文件是否存在
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        file_size = os.path.getsize(file_path)
        file_ext = os.path.splitext(file_path)[1].lower()
        
        logger.debug(f"加载文件: {file_path}, 大小: {file_size} 字节, 扩展名: {file_ext}")
        
        return {
            "file_path": file_path,
            "file_size": file_size,
            "file_ext": file_ext,
            "exists": True
        }
    
    def validate_file(self, file_path: str) -> bool:
        """
        验证文件是否有效
        
        Args:
            file_path: 文件路径
        
        Returns:
            文件是否有效
        """
        try:
            file_info = self.load(file_path)
            return file_info["exists"] and file_info["file_size"] > 0
        except Exception as e:
            logger.warning(f"文件验证失败: {file_path}, 错误: {e}")
            return False


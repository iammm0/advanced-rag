"""Unstructured 解析器 - 用于复杂格式文档的布局分析"""
from typing import Dict, Any, List, Optional
from parsers.base import BaseParser
from utils.logger import logger


class UnstructuredParser(BaseParser):
    """Unstructured 解析器 - 支持复杂格式文档的布局分析"""
    
    def __init__(self):
        """初始化 Unstructured 解析器"""
        self._initialized = False
        self._partition_func = None
    
    def _initialize_unstructured(self):
        """延迟初始化 Unstructured 库"""
        if self._initialized:
            return
        
        try:
            from unstructured.partition.auto import partition
            self._partition_func = partition
            self._initialized = True
            logger.info("Unstructured 解析器初始化成功")
        except ImportError:
            logger.error("Unstructured 库未安装，无法使用 Unstructured 解析器")
            raise ImportError("请安装 Unstructured: pip install unstructured[all]")
        except Exception as e:
            logger.error(f"初始化 Unstructured 解析器失败: {e}", exc_info=True)
            raise
    
    def _parse_with_unstructured(self, file_path: str) -> Dict[str, Any]:
        """
        使用 Unstructured 库解析文档
        
        Args:
            file_path: 文件路径
        
        Returns:
            包含文本和元数据的字典
        """
        if not self._initialized:
            self._initialize_unstructured()
        
        try:
            # 使用 Unstructured 的自动分区功能
            elements = self._partition_func(filename=file_path)
            
            # 提取文本内容
            text_parts = []
            metadata_parts = []
            
            for element in elements:
                # 提取文本
                text = getattr(element, 'text', '')
                if text and text.strip():
                    text_parts.append(text)
                
                # 提取元数据
                element_metadata = getattr(element, 'metadata', {})
                if element_metadata:
                    metadata_parts.append(element_metadata)
            
            full_text = "\n\n".join(text_parts)
            
            # 合并元数据
            merged_metadata = {}
            if metadata_parts:
                # 合并所有元素的元数据
                for meta in metadata_parts:
                    if isinstance(meta, dict):
                        merged_metadata.update(meta)
            
            # 添加文件信息
            import os
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            merged_metadata.update({
                "file_name": file_name,
                "file_size": file_size,
                "element_count": len(elements),
                "extraction_method": "unstructured"
            })
            
            logger.info(f"Unstructured 解析完成 - 文件: {file_path}, 元素数: {len(elements)}, 文本长度: {len(full_text)}")
            
            return {
                "text": full_text,
                "metadata": merged_metadata
            }
        
        except Exception as e:
            error_msg = f"Unstructured 解析失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """
        解析文档（使用 Unstructured）
        
        Args:
            file_path: 文件路径
        
        Returns:
            包含文本内容和元数据的字典
        """
        return self._parse_with_unstructured(file_path)
    
    def supported_extensions(self) -> List[str]:
        """返回支持的文件扩展名列表"""
        # Unstructured 支持多种格式
        return ["pdf", "docx", "doc", "pptx", "xlsx", "html", "txt", "md"]


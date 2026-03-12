"""LangChain 递归分块器 - 用于高度结构化的内容（代码、论文等）"""
from typing import List, Dict, Any, Optional
from chunking.base import BaseChunker
from utils.logger import logger


class RecursiveChunker(BaseChunker):
    """LangChain 递归分块器 - 使用 RecursiveCharacterTextSplitter"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        初始化递归分块器
        
        Args:
            chunk_size: 每个块的目标大小（字符数）
            chunk_overlap: 块之间的重叠字符数
            separators: 分隔符列表（按优先级排序）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",  # 段落分隔
            "\n",    # 行分隔
            "。",     # 中文句号
            ". ",    # 英文句号+空格
            "；",     # 中文分号
            "; ",    # 英文分号+空格
            "，",     # 中文逗号
            ", ",    # 英文逗号+空格
            " ",     # 空格
            ""       # 字符级别
        ]
        self._text_splitter = None
    
    def _get_text_splitter(self):
        """延迟初始化 LangChain 文本分割器"""
        if self._text_splitter is None:
            try:
                # 兼容旧版和新版 LangChain
                try:
                    from langchain_text_splitters import RecursiveCharacterTextSplitter
                except ImportError:
                    try:
                        from langchain.text_splitter import RecursiveCharacterTextSplitter
                    except ImportError:
                        from langchain_core.text_splitters import RecursiveCharacterTextSplitter
                
                self._text_splitter = RecursiveCharacterTextSplitter(
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap,
                    separators=self.separators,
                    length_function=len
                )
                logger.info("LangChain RecursiveCharacterTextSplitter 初始化成功")
            except ImportError:
                logger.error("LangChain 未安装，无法使用递归分块器")
                raise ImportError("请安装 LangChain: pip install langchain langchain-text-splitters")
            except Exception as e:
                logger.error(f"初始化递归分块器失败: {e}", exc_info=True)
                raise
        
        return self._text_splitter
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        将文本分割成块
        
        Args:
            text: 要分割的文本
            metadata: 可选的元数据
        
        Returns:
            文本块列表，每个块包含 text 和 metadata
        """
        if not text or not text.strip():
            return []
        
        try:
            text_splitter = self._get_text_splitter()
            # 使用 LangChain 的分割器
            chunks = text_splitter.split_text(text)
            
            # 转换为标准格式
            result = []
            for i, chunk_text in enumerate(chunks):
                if chunk_text.strip():  # 跳过空块
                    result.append({
                        "text": chunk_text,
                        "chunk_index": i,
                        "metadata": metadata or {}
                    })
            
            logger.debug(f"递归分块完成 - 块数量: {len(result)}, 文本长度: {len(text)}")
            return result
        
        except Exception as e:
            logger.error(f"递归分块失败: {e}", exc_info=True)
            # 如果失败，返回单个块
            return [{
                "text": text,
                "chunk_index": 0,
                "metadata": metadata or {}
            }]


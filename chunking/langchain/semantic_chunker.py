"""语义分块器 - 用于需要保持语义连贯性的内容（报告、文章等）"""
from typing import List, Dict, Any, Optional
from chunking.base import BaseChunker
from embedding.embedding_service import embedding_service
from utils.logger import logger


class SemanticChunker(BaseChunker):
    """语义分块器 - 使用 LangChain SemanticChunker 保持语义连贯性"""
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        breakpoint_threshold_amount: float = 0.5
    ):
        """
        初始化语义分块器
        
        Args:
            chunk_size: 每个块的目标大小（字符数）
            chunk_overlap: 块之间的重叠字符数
            breakpoint_threshold_amount: 语义断点阈值（0-1之间）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.breakpoint_threshold_amount = breakpoint_threshold_amount
        self._semantic_chunker = None
        self._embedding_function = None
    
    def _get_embedding_function(self):
        """获取嵌入函数（用于语义分块）"""
        if self._embedding_function is None:
            # 使用现有的 embedding_service
            def embed_func(texts: List[str]) -> List[List[float]]:
                """嵌入函数包装器"""
                try:
                    return embedding_service.encode(texts)
                except Exception as e:
                    logger.error(f"嵌入向量生成失败: {e}", exc_info=True)
                    raise
            
            self._embedding_function = embed_func
            logger.info("语义分块器嵌入函数初始化成功")
        
        return self._embedding_function
    
    def _get_semantic_chunker(self):
        """延迟初始化 LangChain 语义分块器"""
        if self._semantic_chunker is None:
            try:
                from langchain_experimental.text_splitter import SemanticChunker as LangChainSemanticChunker
                
                embedding_function = self._get_embedding_function()
                
                self._semantic_chunker = LangChainSemanticChunker(
                    embeddings=embedding_function,
                    breakpoint_threshold_amount=self.breakpoint_threshold_amount,
                    chunk_size=self.chunk_size,
                    chunk_overlap=self.chunk_overlap
                )
                logger.info("LangChain SemanticChunker 初始化成功")
            except ImportError:
                # 如果 langchain_experimental 不可用，尝试使用 langchain
                try:
                    from langchain.text_splitter import SemanticChunker as LangChainSemanticChunker
                    embedding_function = self._get_embedding_function()
                    
                    self._semantic_chunker = LangChainSemanticChunker(
                        embeddings=embedding_function,
                        breakpoint_threshold_amount=self.breakpoint_threshold_amount,
                        chunk_size=self.chunk_size,
                        chunk_overlap=self.chunk_overlap
                    )
                    logger.info("LangChain SemanticChunker 初始化成功（使用 langchain）")
                except ImportError:
                    logger.error("LangChain SemanticChunker 未安装，无法使用语义分块器")
                    raise ImportError("请安装 LangChain: pip install langchain langchain-experimental")
            except Exception as e:
                logger.error(f"初始化语义分块器失败: {e}", exc_info=True)
                raise
        
        return self._semantic_chunker
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        将文本分割成块（基于语义）
        
        Args:
            text: 要分割的文本
            metadata: 可选的元数据
            
        Returns:
            文本块列表，每个块包含 text 和 metadata
        """
        if not text or not text.strip():
            return []
        
        try:
            semantic_chunker = self._get_semantic_chunker()
            
            # 使用语义分块器
            # SemanticChunker 的 API 可能因版本而异
            try:
                # 尝试使用 create_documents 方法
                documents = semantic_chunker.create_documents([text])
                chunks = [doc.page_content for doc in documents]
            except AttributeError:
                # 如果不存在 create_documents，尝试使用 split_text
                try:
                    chunks = semantic_chunker.split_text(text)
                except AttributeError:
                    # 如果都不存在，使用 split_documents
                    from langchain.schema import Document
                    doc = Document(page_content=text)
                    documents = semantic_chunker.split_documents([doc])
                    chunks = [doc.page_content for doc in documents]
            
            # 转换为标准格式
            result = []
            for i, chunk_text in enumerate(chunks):
                if chunk_text.strip():  # 跳过空块
                    result.append({
                        "text": chunk_text,
                        "chunk_index": i,
                        "metadata": metadata or {}
                    })
            
            logger.debug(f"语义分块完成 - 块数量: {len(result)}, 文本长度: {len(text)}")
            return result
        
        except Exception as e:
            logger.error(f"语义分块失败: {e}", exc_info=True)
            # 如果失败，回退到简单的字符分割
            logger.warning("语义分块失败，使用简单分割作为回退")
            from chunking.simple_chunker import SimpleChunker
            fallback_chunker = SimpleChunker(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
            return fallback_chunker.chunk(text, metadata)


"""滑动窗口文本分块器"""
from typing import List, Dict, Any, Optional
from .base import BaseChunker


class SlidingWindowChunker(BaseChunker):
    """滑动窗口文本分块器（更智能的分块策略）"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 100,
        min_chunk_size: int = 100
    ):
        """
        初始化滑动窗口分块器
        
        Args:
            chunk_size: 每个块的目标字符数
            chunk_overlap: 块之间的重叠字符数
            min_chunk_size: 最小块大小
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """使用滑动窗口策略分割文本"""
        if not text.strip():
            return []
        
        chunks = []
        sentences = self._split_into_sentences(text)
        
        current_chunk = []
        current_length = 0
        
        for sentence in sentences:
            sentence_length = len(sentence)
            
            # 如果当前块加上新句子超过大小，保存当前块
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                if len(chunk_text) >= self.min_chunk_size:
                    chunks.append({
                        "text": chunk_text,
                        "metadata": metadata or {}
                    })
                
                # 保留重叠部分
                overlap_text = []
                overlap_length = 0
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_text.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break
                
                current_chunk = overlap_text
                current_length = overlap_length
            
            current_chunk.append(sentence)
            current_length += sentence_length
        
        # 添加最后一个块
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if len(chunk_text) >= self.min_chunk_size:
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata or {}
                })
        
        return chunks
    
    def _split_into_sentences(self, text: str) -> List[str]:
        """将文本分割成句子"""
        # 简单的句子分割（可以改进）
        import re
        # 按句号、问号、感叹号分割，保留分隔符
        sentences = re.split(r'([。！？.!?])', text)
        
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
            else:
                sentence = sentences[i]
            
            sentence = sentence.strip()
            if sentence:
                result.append(sentence)
        
        return result


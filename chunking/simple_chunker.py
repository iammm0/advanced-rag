"""简单文本分块器"""
from typing import List, Dict, Any, Optional
from .base import BaseChunker
import re


class SimpleChunker(BaseChunker):
    """简单文本分块器（按固定大小分割）"""
    
    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separators: List[str] = None
    ):
        """
        初始化分块器
        
        Args:
            chunk_size: 每个块的最大字符数
            chunk_overlap: 块之间的重叠字符数
            separators: 优先使用的分隔符列表
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or ["\n\n", "\n", "。", ".", " ", ""]
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """将文本分割成块"""
        if not text.strip():
            return []
        
        chunks = []
        current_pos = 0
        text_len = len(text)
        last_pos = -1  # 用于检测是否卡住
        max_iterations = text_len // (self.chunk_size - self.chunk_overlap) + 100  # 防止无限循环
        iteration = 0
        
        while current_pos < text_len:
            iteration += 1
            # 防止无限循环
            if iteration > max_iterations:
                # 如果卡住，强制移动到下一个位置
                if current_pos == last_pos:
                    current_pos += self.chunk_size - self.chunk_overlap
                    if current_pos >= text_len:
                        break
                else:
                    last_pos = current_pos
            
            # 计算当前块的结束位置
            end_pos = min(current_pos + self.chunk_size, text_len)
            
            # 如果还没到文本末尾，尝试向后查找分隔符
            if end_pos < text_len:
                # 限制搜索范围，避免在大文本中搜索过远
                # 只在重叠区域和稍后一点查找，不要搜索太远
                search_start = max(current_pos, end_pos - self.chunk_overlap)
                search_end = min(text_len, end_pos + 50)  # 减少搜索范围从100到50
                
                found_separator = False
                best_sep_pos = -1
                best_sep_len = 0
                
                # 优先查找更长的分隔符（更可能是有意义的断点）
                sorted_separators = sorted([s for s in self.separators if s], key=len, reverse=True)
                
                for separator in sorted_separators:
                    # 向后查找分隔符
                    next_sep_pos = text.find(separator, search_start, search_end)
                    if next_sep_pos != -1:
                        # 选择最接近 end_pos 的分隔符
                        if best_sep_pos == -1 or next_sep_pos < best_sep_pos:
                            best_sep_pos = next_sep_pos
                            best_sep_len = len(separator)
                            found_separator = True
                
                if found_separator:
                    end_pos = best_sep_pos + best_sep_len
                else:
                    # 如果没有找到分隔符，使用默认的块大小
                    end_pos = min(current_pos + self.chunk_size, text_len)
            
            # 提取块文本
            chunk_text = text[current_pos:end_pos].strip()
            
            if chunk_text:
                chunks.append({
                    "text": chunk_text,
                    "start_index": current_pos,
                    "end_index": end_pos,
                    "metadata": metadata or {}
                })
            
            # 移动到下一个块的开始位置（考虑重叠）
            # 确保至少向前移动，避免死循环
            next_pos = end_pos - self.chunk_overlap
            if next_pos <= current_pos:
                # 如果没有向前移动，强制移动至少一个字符
                next_pos = current_pos + 1
            
            current_pos = next_pos
            
            # 如果已经到达文本末尾，退出
            if current_pos >= text_len:
                break
        
        return chunks


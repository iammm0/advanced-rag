
import re
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from chunking.base import BaseChunker
from chunking.langchain.semantic_chunker import SemanticChunker
from utils.logger import logger

class HybridChunker(BaseChunker):
    """
    混合分块器：规则分块 + 语义分块
    
    特性：
    1. 基于规则提取代码块、公式和表格，以保持其完整性。
    2. 对普通文本使用基于 Ollama 嵌入的语义分块。
    3. 分块去重。
    4. 细粒度的元数据（content_type）。
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        semantic_threshold: float = 0.5
    ):
        """
        初始化混合分块器
        
        Args:
            chunk_size: 目标分块大小（字符数）
            chunk_overlap: 分块重叠大小（字符数）
            semantic_threshold: 语义分块的断点阈值（0-1之间）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        # 初始化语义分块器
        self.semantic_chunker = SemanticChunker(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            breakpoint_threshold_amount=semantic_threshold
        )
        
        # 正则表达式模式
        # 匹配代码块 (```...```)
        self.code_block_pattern = re.compile(r'```[\s\S]*?```')
        # 匹配 LaTeX 公式 ($$...$$ 或 \[...\])
        self.formula_pattern = re.compile(r'\$\$[\s\S]*?\$\$|\\\[[\s\S]*?\\\]')
        # 表格检测：连续的以 | 开头的行
        # 使用多行模式匹配以 | 开头的一组行
        self.table_pattern = re.compile(r'(?:^\|.*\|(?:\r?\n|$))+', re.MULTILINE)

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        执行混合分块
        
        Args:
            text: 输入文本
            metadata: 可选元数据
            
        Returns:
            分块结果列表，包含文本和元数据
        """
        if not text or not text.strip():
            return []
            
        metadata = metadata or {}
        
        # 1. 提取特殊块（代码、公式、表格）
        segments = self._extract_special_blocks(text)
        
        # 2. 处理分段
        final_chunks = []
        seen_hashes = set()
        
        for segment in segments:
            seg_type = segment["type"]
            seg_text = segment["text"]
            
            if not seg_text.strip():
                continue
                
            chunks_to_add = []
            
            if seg_type == "text":
                # 对普通文本使用语义分块
                # semantic_chunker.chunk 返回包含 "text" 和 "metadata" 的字典列表
                try:
                    text_chunks = self.semantic_chunker.chunk(seg_text, metadata)
                    for chunk in text_chunks:
                        # 确保元数据被复制并更新
                        chunk_meta = chunk.get("metadata", {}).copy()
                        chunk_meta["content_type"] = "text"
                        chunks_to_add.append({
                            "text": chunk["text"],
                            "metadata": chunk_meta
                        })
                except Exception as e:
                    logger.error(f"语义分块失败: {e}。回退到简单文本分块。", exc_info=True)
                    chunks_to_add.append({
                        "text": seg_text,
                        "metadata": {**metadata, "content_type": "text"}
                    })
            else:
                # 特殊块作为单个块保留（保持完整性）
                chunks_to_add.append({
                    "text": seg_text,
                    "metadata": {**metadata, "content_type": seg_type}
                })
            
            # 3. 去重并添加
            for chunk_data in chunks_to_add:
                chunk_text = chunk_data["text"]
                chunk_hash = self._compute_hash(chunk_text)
                
                if chunk_hash not in seen_hashes:
                    seen_hashes.add(chunk_hash)
                    final_chunks.append(chunk_data)
                else:
                    logger.debug(f"移除重复分块: {chunk_hash[:8]}...")
                    
        return final_chunks

    def _extract_special_blocks(self, text: str) -> List[Dict[str, str]]:
        """
        将文本分割为片段列表：[{"type": "code"|"formula"|"table"|"text", "text": "..."}]
        """
        matches = []
        
        # 辅助函数：检查重叠
        def is_overlapping(start, end, existing_matches):
            for m_start, m_end, _ in existing_matches:
                if max(start, m_start) < min(end, m_end):
                    return True
            return False

        # 查找代码块（最高优先级）
        for m in self.code_block_pattern.finditer(text):
            matches.append((m.start(), m.end(), "code"))
            
        # 查找公式
        for m in self.formula_pattern.finditer(text):
            if not is_overlapping(m.start(), m.end(), matches):
                matches.append((m.start(), m.end(), "formula"))
                
        # 查找表格
        for m in self.table_pattern.finditer(text):
            if not is_overlapping(m.start(), m.end(), matches):
                matches.append((m.start(), m.end(), "table"))
        
        # 按起始位置排序
        matches.sort(key=lambda x: x[0])
        
        # 构建结果列表
        result = []
        last_pos = 0
        
        for start, end, type_ in matches:
            # 添加前面的普通文本
            if start > last_pos:
                text_segment = text[last_pos:start]
                if text_segment.strip():
                    result.append({"type": "text", "text": text_segment})
            
            # 添加特殊块
            result.append({"type": type_, "text": text[start:end]})
            last_pos = end
            
        # 添加剩余文本
        if last_pos < len(text):
            text_segment = text[last_pos:]
            if text_segment.strip():
                result.append({"type": "text", "text": text_segment})
                
        return result

    def _compute_hash(self, text: str) -> str:
        """计算文本的 SHA256 哈希值"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()

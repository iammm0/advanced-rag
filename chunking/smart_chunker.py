"""智能文本分块器 - 支持数学公式和结构化文档"""
from typing import List, Dict, Any, Optional
from .base import BaseChunker
import re


class SmartChunker(BaseChunker):
    """
    智能文本分块器
    
    特性：
    1. 识别段落边界（双换行、标题等）
    2. 保护数学公式完整性（LaTeX格式）
    3. 识别列表和表格结构
    4. 根据内容类型调整分块大小
    5. 保持语义完整性
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,  # 对于数学公式文档，使用更大的块
        chunk_overlap: int = 200,  # 增加重叠以保持上下文
        min_chunk_size: int = 100,
        max_chunk_size: int = 2000
    ):
        """
        初始化智能分块器
        
        Args:
            chunk_size: 目标块大小（字符数）
            chunk_overlap: 块之间的重叠字符数
            min_chunk_size: 最小块大小
            max_chunk_size: 最大块大小（防止单个块过大）
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        
        # 数学公式模式（LaTeX格式）
        self.math_patterns = [
            r'\$\$.*?\$\$',  # 块级公式 $$...$$
            r'\$.*?\$',      # 行内公式 $...$
            r'\\\[.*?\\\]',  # LaTeX块级公式 \[...\]
            r'\\\(.*?\\\)',  # LaTeX行内公式 \(...\)
            r'\\begin\{equation\}.*?\\end\{equation\}',  # 公式环境
            r'\\begin\{align\}.*?\\end\{align\}',        # 对齐环境
            r'\\begin\{matrix\}.*?\\end\{matrix\}',      # 矩阵环境
        ]
        
        # 段落分隔符（按优先级排序）
        self.paragraph_separators = [
            r'\n\n+',           # 双换行或更多
            r'\n(?=[一二三四五六七八九十\d]+[、.])',  # 中文编号段落
            r'\n(?=\d+[\.\)]\s)',  # 数字编号段落
            r'\n(?=[A-Z][a-z]+:)',  # 英文标题格式
            r'\n(?=第[一二三四五六七八九十\d]+[章节])',  # 章节标题
        ]
        
        # 标题模式
        self.title_patterns = [
            r'^#{1,6}\s+.+',  # Markdown标题
            r'^第[一二三四五六七八九十\d]+[章节]\s+',  # 中文章节
            r'^[一二三四五六七八九十\d]+[、.]\s+',  # 中文编号
        ]
    
    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        智能分块文本
        
        Args:
            text: 要分割的文本
            metadata: 可选的元数据
            
        Returns:
            文本块列表
        """
        if not text.strip():
            return []
        
        # 步骤1: 识别和保护数学公式
        text_with_markers, formula_map = self._protect_formulas(text)
        
        # 步骤2: 识别段落边界
        paragraphs = self._split_into_paragraphs(text_with_markers)
        
        # 步骤3: 智能合并段落
        chunks = self._merge_paragraphs_into_chunks(paragraphs)
        
        # 步骤4: 恢复数学公式
        chunks = self._restore_formulas(chunks, formula_map)
        
        # 步骤5: 后处理：确保块大小合理
        chunks = self._post_process_chunks(chunks, metadata)
        
        return chunks
    
    def _protect_formulas(self, text: str) -> tuple:
        """
        识别并保护数学公式，用占位符替换
        
        Returns:
            (处理后的文本, 公式映射字典)
        """
        formula_map = {}
        formula_counter = 0
        protected_text = text
        
        # 收集所有公式匹配（避免重复匹配）
        all_matches = []
        matched_positions = set()
        
        for pattern in self.math_patterns:
            for match in re.finditer(pattern, text, re.DOTALL):
                start, end = match.span()
                # 检查是否已经被其他模式匹配（避免重复）
                is_overlapped = any(
                    start < other_end and end > other_start
                    for other_start, other_end in matched_positions
                )
                if not is_overlapped:
                    all_matches.append((start, end, match.group(0)))
                    matched_positions.add((start, end))
        
        # 按起始位置从后往前排序（避免位置偏移）
        all_matches.sort(key=lambda x: x[0], reverse=True)
        
        for start, end, formula in all_matches:
            placeholder = f"__FORMULA_{formula_counter}__"
            formula_map[placeholder] = formula
            protected_text = protected_text[:start] + placeholder + protected_text[end:]
            formula_counter += 1
        
        return protected_text, formula_map
    
    def _restore_formulas(self, chunks: List[Any], formula_map: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        恢复数学公式
        
        Args:
            chunks: 块列表，可能是字符串列表或字典列表
            formula_map: 公式映射字典
            
        Returns:
            字典列表，每个字典包含text字段
        """
        restored_chunks = []
        for chunk in chunks:
            # 处理字符串类型的chunk
            if isinstance(chunk, str):
                text = chunk
            # 处理字典类型的chunk
            elif isinstance(chunk, dict):
                text = chunk.get("text", "")
            else:
                # 未知类型，跳过
                continue
            
            # 恢复公式占位符
            for placeholder, formula in formula_map.items():
                text = text.replace(placeholder, formula)
            
            # 确保返回字典格式
            if isinstance(chunk, dict):
                restored_chunk = chunk.copy()
                restored_chunk["text"] = text
            else:
                restored_chunk = {"text": text}
            
            restored_chunks.append(restored_chunk)
        
        return restored_chunks
    
    def _split_into_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """
        将文本分割成段落
        
        Returns:
            段落列表，每个段落包含text和metadata
        """
        # 首先按双换行分割
        raw_paragraphs = re.split(r'\n\n+', text)
        
        paragraphs = []
        for para in raw_paragraphs:
            para = para.strip()
            if not para:
                continue
            
            # 检查是否是标题
            is_title = any(re.match(pattern, para, re.MULTILINE) for pattern in self.title_patterns)
            
            # 检查是否包含公式
            has_formula = any(re.search(pattern, para) for pattern in self.math_patterns)
            
            paragraphs.append({
                "text": para,
                "is_title": is_title,
                "has_formula": has_formula,
                "length": len(para)
            })
        
        return paragraphs
    
    def _merge_paragraphs_into_chunks(self, paragraphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        智能合并段落为块
        
        策略：
        1. 标题段落单独成块或与下一段合并
        2. 包含公式的段落尽量保持完整
        3. 普通段落按大小合并
        
        Returns:
            字典列表，每个字典包含text字段
        """
        if not paragraphs:
            return []
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        i = 0
        while i < len(paragraphs):
            para = paragraphs[i]
            para_text = para["text"]
            para_length = para["length"]
            is_title = para.get("is_title", False)
            has_formula = para.get("has_formula", False)
            
            # 如果当前块为空，直接添加
            if not current_chunk:
                current_chunk.append(para_text)
                current_length = para_length
                i += 1
                continue
            
            # 如果段落包含公式，尽量保持完整
            if has_formula:
                # 如果当前块加上这个公式段落不超过最大大小，合并
                if current_length + para_length <= self.max_chunk_size:
                    current_chunk.append(para_text)
                    current_length += para_length
                    i += 1
                else:
                    # 保存当前块
                    chunks.append({"text": "\n\n".join(current_chunk)})
                    current_chunk = [para_text]
                    current_length = para_length
                    i += 1
                continue
            
            # 如果是标题
            if is_title:
                # 如果当前块较小，可以合并标题和内容
                if current_length < self.chunk_size * 0.5:
                    current_chunk.append(para_text)
                    current_length += para_length
                    i += 1
                else:
                    # 保存当前块，标题单独或与下一段合并
                    chunks.append({"text": "\n\n".join(current_chunk)})
                    current_chunk = [para_text]
                    current_length = para_length
                    i += 1
                continue
            
            # 普通段落：检查是否可以合并
            if current_length + para_length <= self.chunk_size:
                # 可以合并
                current_chunk.append(para_text)
                current_length += para_length
                i += 1
            else:
                # 当前块已满，保存并开始新块
                chunks.append({"text": "\n\n".join(current_chunk)})
                
                # 如果单个段落就超过chunk_size，需要分割
                if para_length > self.max_chunk_size:
                    # 分割大段落
                    sub_chunks = self._split_large_paragraph(para_text)
                    if sub_chunks:
                        # 将字符串转换为字典
                        for sub_chunk in sub_chunks[:-1]:
                            chunks.append({"text": sub_chunk})
                        current_chunk = [sub_chunks[-1]]
                        current_length = len(sub_chunks[-1])
                    else:
                        current_chunk = [para_text]
                        current_length = para_length
                else:
                    current_chunk = [para_text]
                    current_length = para_length
                i += 1
        
        # 添加最后一个块
        if current_chunk:
            chunks.append({"text": "\n\n".join(current_chunk)})
        
        return chunks
    
    def _split_large_paragraph(self, text: str) -> List[str]:
        """
        分割过大的段落
        
        优先在句子边界分割
        """
        if len(text) <= self.max_chunk_size:
            return [text]
        
        # 尝试在句子边界分割
        sentence_endings = r'[。！？.!?]\s+'
        sentences = re.split(f'({sentence_endings})', text)
        
        # 重新组合句子
        combined_sentences = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = sentences[i] + sentences[i + 1]
            else:
                sentence = sentences[i]
            if sentence.strip():
                combined_sentences.append(sentence.strip())
        
        # 按chunk_size合并句子
        chunks = []
        current_chunk = []
        current_length = 0
        
        for sentence in combined_sentences:
            sent_length = len(sentence)
            
            if current_length + sent_length <= self.chunk_size:
                current_chunk.append(sentence)
                current_length += sent_length
            else:
                if current_chunk:
                    chunks.append(" ".join(current_chunk))
                current_chunk = [sentence]
                current_length = sent_length
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
        
        return chunks if chunks else [text]
    
    def _post_process_chunks(self, chunks: List[Dict[str, Any]], metadata: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        后处理块：确保大小合理，添加元数据
        
        Args:
            chunks: 块列表，每个块是包含text字段的字典
            metadata: 可选的元数据
            
        Returns:
            处理后的块列表
        """
        processed_chunks = []
        
        for i, chunk in enumerate(chunks):
            # 确保chunk是字典格式
            if isinstance(chunk, dict):
                chunk_text = chunk.get("text", "")
            elif isinstance(chunk, str):
                chunk_text = chunk
            else:
                continue
            
            chunk_text = chunk_text.strip()
            
            # 跳过太小的块
            if len(chunk_text) < self.min_chunk_size:
                # 如果下一个块存在，尝试合并
                if i + 1 < len(chunks):
                    next_chunk = chunks[i + 1]
                    next_text = next_chunk.get("text", "") if isinstance(next_chunk, dict) else next_chunk
                    if isinstance(chunks[i + 1], dict):
                        chunks[i + 1]["text"] = chunk_text + "\n\n" + next_text
                    else:
                        chunks[i + 1] = chunk_text + "\n\n" + next_text
                    continue
                # 如果这是最后一个块且太小，仍然保留（可能是重要内容）
                if len(chunk_text) < 50:  # 非常小的块才跳过
                    continue
            
            # 确保不超过最大大小
            if len(chunk_text) > self.max_chunk_size:
                # 强制分割
                sub_chunks = self._split_large_paragraph(chunk_text)
                for sub_chunk in sub_chunks:
                    sub_chunk_text = sub_chunk.strip()
                    if len(sub_chunk_text) >= self.min_chunk_size:
                        processed_chunks.append({
                            "text": sub_chunk_text,
                            "chunk_index": len(processed_chunks),
                            "metadata": metadata or {}
                        })
            else:
                processed_chunks.append({
                    "text": chunk_text,
                    "chunk_index": len(processed_chunks),
                    "metadata": metadata or {}
                })
        
        return processed_chunks


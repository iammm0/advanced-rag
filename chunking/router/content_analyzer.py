"""内容分析路由器 - 根据文档内容特征分发到不同的分块器"""
from typing import Dict, Any, Optional, Tuple
from chunking.langchain.recursive_chunker import RecursiveChunker
from chunking.langchain.semantic_chunker import SemanticChunker
from chunking.simple_chunker import SimpleChunker
from chunking.smart_chunker import SmartChunker
from chunking.hybrid_chunker import HybridChunker
from chunking.report_chunker import ReportChunker
from utils.logger import logger


class ContentAnalyzer:
    """内容分析路由器 - 智能分发文档到合适的分块器"""
    
    # 分块器类型枚举
    CHUNKER_TYPE_RECURSIVE = "recursive"  # LangChain 递归分块器（高度结构化内容）
    CHUNKER_TYPE_SEMANTIC = "semantic"  # 语义分块器（需要保持语义连贯性）
    CHUNKER_TYPE_SMART = "smart"  # 智能分块器（包含公式、表格等）
    CHUNKER_TYPE_LEGACY = "legacy"  # 简单分块器（通用型）
    CHUNKER_TYPE_HYBRID = "hybrid"  # 混合分块器（规则+语义）
    CHUNKER_TYPE_REPORT = "report"  # 行业报告分块器（结构 + token 预算）
    
    def __init__(self):
        """初始化内容分析器"""
        self.recursive_chunker = None
        self.semantic_chunker = None
        self.smart_chunker = None
        self.legacy_chunker = None
        self.hybrid_chunker = None
        self.report_chunker = None
    
    def _get_recursive_chunker(self) -> RecursiveChunker:
        """获取 LangChain 递归分块器（延迟初始化）"""
        if self.recursive_chunker is None:
            self.recursive_chunker = RecursiveChunker()
        return self.recursive_chunker
    
    def _get_semantic_chunker(self) -> Optional[SemanticChunker]:
        """获取语义分块器（延迟初始化）"""
        if self.semantic_chunker is None:
            try:
                self.semantic_chunker = SemanticChunker()
            except Exception as e:
                logger.warning(f"语义分块器初始化失败: {e}，将使用其他分块器")
                return None
        return self.semantic_chunker
    
    def _get_smart_chunker(self) -> SmartChunker:
        """获取智能分块器（延迟初始化）"""
        if self.smart_chunker is None:
            self.smart_chunker = SmartChunker(
                chunk_size=1000,
                chunk_overlap=200,
                min_chunk_size=100,
                max_chunk_size=2000
            )
        return self.smart_chunker
    
    def _get_legacy_chunker(self) -> SimpleChunker:
        """获取简单分块器（延迟初始化）"""
        if self.legacy_chunker is None:
            self.legacy_chunker = SimpleChunker(chunk_size=500, chunk_overlap=50)
        return self.legacy_chunker

    def _get_hybrid_chunker(self) -> HybridChunker:
        """获取混合分块器（延迟初始化）"""
        if self.hybrid_chunker is None:
            self.hybrid_chunker = HybridChunker(
                chunk_size=1000,
                chunk_overlap=200,
                semantic_threshold=0.5
            )
        return self.hybrid_chunker

    def _get_report_chunker(self) -> ReportChunker:
        """获取行业报告分块器（延迟初始化）"""
        if self.report_chunker is None:
            self.report_chunker = ReportChunker()
        return self.report_chunker
    
    def _detect_highly_structured(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        检测是否为高度结构化的内容（代码、论文等）
        
        适合使用递归分块器的场景：
        1. 代码文件（.py, .js, .java等）
        2. 包含大量代码块的文档
        3. 包含大量LaTeX公式的学术论文
        4. 包含大量结构化标记的文档（Markdown、HTML等）
        
        Args:
            text: 文本内容
            metadata: 可选的元数据
        
        Returns:
            是否为高度结构化内容
        """
        # 1. 检查元数据中的文件类型
        if metadata:
            file_type = metadata.get("file_type", "").lower()
            # 代码文件
            code_extensions = ['.py', '.js', '.java', '.cpp', '.c', '.go', '.rs', '.ts', '.rb', '.php']
            if any(file_type.endswith(ext) for ext in code_extensions):
                logger.info("✓ 检测到代码文件，使用递归分块器")
                return True
            
            # 检查metadata中的代码块信息
            code_blocks = metadata.get("code_blocks", [])
            if isinstance(code_blocks, list) and len(code_blocks) > 3:
                logger.info(f"✓ 检测到 {len(code_blocks)} 个代码块，使用递归分块器")
                return True
        
        # 2. 检查文本特征
        # 检查是否包含大量代码块（``` 或缩进代码）
        code_block_count = text.count('```') // 2  # 每对```算一个代码块
        code_block_count += text.count('    def ') + text.count('    class ')
        code_block_count += text.count('function ') + text.count('class ')
        
        if code_block_count > 5:
            logger.info(f"✓ 检测到大量代码块 ({code_block_count} 个)，使用递归分块器")
            return True
        
        # 3. 检查是否包含大量 LaTeX 公式（论文特征）
        latex_patterns = ['\\begin{', '\\end{', '\\[']
        latex_count = sum(text.count(pattern) for pattern in latex_patterns)
        # 检查metadata中的公式信息
        if metadata:
            formulas = metadata.get("formulas", [])
            if isinstance(formulas, list):
                latex_count += len(formulas)
        
        if latex_count > 10:
            logger.info(f"✓ 检测到大量 LaTeX 公式 ({latex_count} 个)，使用递归分块器")
            return True
        
        # 4. 检查是否包含大量结构化标记（Markdown、HTML等）
        structured_markers = ['# ', '## ', '### ', '<div', '<section', '<table']
        structured_count = sum(text.count(marker) for marker in structured_markers)
        # 检查metadata中的表格信息
        if metadata:
            tables = metadata.get("tables", [])
            if isinstance(tables, list):
                structured_count += len(tables) * 2  # 表格也算结构化内容
        
        if structured_count > 20:
            logger.info(f"✓ 检测到大量结构化标记 ({structured_count} 个)，使用递归分块器")
            return True
        
        return False
    
    def _detect_formulas_or_tables(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        检测是否包含公式或表格（适合使用智能分块器）
        
        Args:
            text: 文本内容
            metadata: 可选的元数据
        
        Returns:
            是否包含公式或表格
        """
        # 1. 检查metadata中的公式和表格信息
        if metadata:
            formulas = metadata.get("formulas", [])
            tables = metadata.get("tables", [])
            
            if isinstance(formulas, list) and len(formulas) > 0:
                logger.info(f"✓ 检测到 {len(formulas)} 个公式，使用智能分块器")
                return True
            
            if isinstance(tables, list) and len(tables) > 0:
                logger.info(f"✓ 检测到 {len(tables)} 个表格，使用智能分块器")
                return True
        
        # 2. 检查文本中的公式模式
        formula_patterns = [r'\$\$.*?\$\$', r'\$[^\$]+\$', r'\\\[.*?\\\]', r'\\begin\{equation\}']
        import re
        formula_count = 0
        for pattern in formula_patterns:
            matches = re.findall(pattern, text)
            formula_count += len(matches)
        
        if formula_count > 3:
            logger.info(f"✓ 检测到 {formula_count} 个公式，使用智能分块器")
            return True
        
        # 3. 检查文本中的表格模式（Markdown表格）
        table_markers = ['|', '---', '|--']
        table_count = text.count('|') // 10  # 粗略估算表格数量
        if table_count > 0 and any(marker in text for marker in table_markers):
            logger.info(f"✓ 检测到表格，使用智能分块器")
            return True
        
        return False
    
    def _detect_semantic_coherence_required(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        检测是否需要保持语义连贯性（报告、文章等）
        
        适合使用语义分块器的场景：
        1. 长文档（报告、论文、文章）
        2. 包含大量段落的文档
        3. 需要保持上下文连贯性的文档
        
        Args:
            text: 文本内容
            metadata: 可选的元数据
        
        Returns:
            是否需要保持语义连贯性
        """
        # 1. 检查文档长度（长文档更适合语义分块）
        text_length = len(text)
        if text_length < 1000:  # 太短的文档不需要语义分块
            return False
        
        # 2. 检查元数据
        if metadata:
            file_type = metadata.get("file_type", "").lower()
            # 文档类型
            document_extensions = ['.docx', '.doc', '.pdf', '.txt', '.md']
            if any(file_type.endswith(ext) for ext in document_extensions):
                # 检查是否包含大量段落（文章特征）
                paragraph_count = text.count('\n\n')
                if paragraph_count > 10 and text_length > 5000:
                    logger.info(f"✓ 检测到长文档 ({text_length} 字符, {paragraph_count} 段落)，使用语义分块器")
                    return True
        
        # 3. 检查文本特征
        # 检查是否包含大量句子（文章特征）
        sentence_endings = ['. ', '。', '! ', '！', '? ', '？']
        sentence_count = sum(text.count(ending) for ending in sentence_endings)
        
        if sentence_count > 50:
            # 检查段落结构
            paragraphs = text.split('\n\n')
            if len(paragraphs) > 5:
                # 检查平均段落长度（文章通常有较长的段落）
                avg_para_length = sum(len(p) for p in paragraphs) / len(paragraphs) if paragraphs else 0
                if avg_para_length > 200 and text_length > 3000:
                    logger.info(f"✓ 检测到文章特征 ({sentence_count} 句子, {len(paragraphs)} 段落)，使用语义分块器")
                    return True
        
        # 4. 检查是否包含章节结构（学术文档特征）
        section_markers = ['第', '章', '节', 'Chapter', 'Section']
        section_count = sum(text.count(marker) for marker in section_markers)
        if section_count > 5 and text_length > 5000:
            logger.info(f"✓ 检测到章节结构 ({section_count} 个标记)，使用语义分块器")
            return True
        
        return False
    
    def route(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> Tuple[str, Any]:
        """
        路由文本到合适的分块器
        
        路由策略（按优先级）：
        1. 高度结构化内容（代码、论文）-> 递归分块器
        2. 包含公式、表格或需要保持语义连贯性的长文档 -> 混合分块器 (升级版)
        3. 其他文档 -> 简单分块器
        
        Args:
            text: 要分块的文本
            metadata: 可选的元数据（可能包含解析器提取的表格、公式、代码块等信息）
        
        Returns:
            (分块器类型, 分块器实例) 元组
        """
        if not text or not text.strip():
            # 空文本使用简单分块器
            logger.info("空文本，使用简单分块器")
            return self.CHUNKER_TYPE_LEGACY, self._get_legacy_chunker()
        
        # 0. 超长报告优先：结构 + token 预算分块
        # 行业报告通常章节明显、文本极长，用 report chunker 能提升语义完整性与可控性
        text_length = len(text)
        if text_length >= 100_000:
            logger.info(f"✓ 检测到超长文档 ({text_length} 字符)，使用行业报告分块器")
            return self.CHUNKER_TYPE_REPORT, self._get_report_chunker()

        # 1. 检测高度结构化内容 -> LangChain 递归分块器
        # （优先级最高，因为代码和论文需要精确的结构化分块）
        if self._detect_highly_structured(text, metadata):
            return self.CHUNKER_TYPE_RECURSIVE, self._get_recursive_chunker()
        
        # 2. 检测包含公式或表格的文档 -> 混合分块器 (替代智能分块器)
        if self._detect_formulas_or_tables(text, metadata):
            logger.info("检测到公式或表格，使用混合分块器")
            return self.CHUNKER_TYPE_HYBRID, self._get_hybrid_chunker()
        
        # 3. 检测需要语义连贯性的内容 -> 混合分块器 (替代语义分块器)
        if self._detect_semantic_coherence_required(text, metadata):
            logger.info("检测到需要语义连贯性的内容，使用混合分块器")
            return self.CHUNKER_TYPE_HYBRID, self._get_hybrid_chunker()
        
        # 4. 默认使用简单分块器（通用型，适合大多数场景）
        logger.info("使用简单分块器（通用型）")
        return self.CHUNKER_TYPE_LEGACY, self._get_legacy_chunker()


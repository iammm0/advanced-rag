"""数学公式提取工具"""
import re
from typing import List, Tuple, Dict, Any


class FormulaExtractor:
    """数学公式提取器"""
    
    # LaTeX公式模式
    MATH_PATTERNS = [
        # 块级公式
        (r'\$\$([\s\S]*?)\$\$', 'block'),
        (r'\\\[([\s\S]*?)\\\]', 'block'),
        (r'\\begin\{equation\}([\s\S]*?)\\end\{equation\}', 'block'),
        (r'\\begin\{align\}([\s\S]*?)\\end\{align\}', 'block'),
        (r'\\begin\{matrix\}([\s\S]*?)\\end\{matrix\}', 'block'),
        # 行内公式
        (r'\$([^\$]+)\$', 'inline'),
        (r'\\\(([^\)]+)\\\)', 'inline'),
    ]
    
    # 物理量模式（如：M = 5, kg 或 M = 5\,\text{kg}）
    PHYSICS_PATTERNS = [
        r'\([A-Za-z_\\]+[^)]*=\s*[^,)]+[,\s]*(?:\\?text\{[^}]+\}|[a-zA-Z/]+)\)',
        r'\$[A-Za-z_\\]+[^$]*=\s*[^$,]+[,\s]*\\?text\{[^}]+\}\$',
    ]
    
    @staticmethod
    def extract_formulas(text: str) -> List[Tuple[str, str, int, int]]:
        """
        提取文本中的数学公式
        
        Args:
            text: 输入文本
            
        Returns:
            公式列表，每个元素为 (公式内容, 类型, 起始位置, 结束位置)
        """
        formulas = []
        matched_positions = set()
        
        for pattern, formula_type in FormulaExtractor.MATH_PATTERNS:
            for match in re.finditer(pattern, text, re.DOTALL):
                start, end = match.span()
                # 检查是否已经被其他模式匹配
                is_overlapped = any(
                    start < other_end and end > other_start
                    for other_start, other_end in matched_positions
                )
                if not is_overlapped:
                    formula_content = match.group(1) if match.groups() else match.group(0)
                    formulas.append((formula_content.strip(), formula_type, start, end))
                    matched_positions.add((start, end))
        
        # 按起始位置排序
        formulas.sort(key=lambda x: x[2])
        return formulas
    
    @staticmethod
    def normalize_formula(formula: str) -> str:
        """
        规范化公式格式，转换为标准LaTeX格式
        
        Args:
            formula: 原始公式文本
            
        Returns:
            规范化后的LaTeX公式
        """
        # 移除多余的空白
        formula = re.sub(r'\s+', ' ', formula.strip())
        
        # 确保常见的数学符号正确
        # 替换常见的错误编码为正确的LaTeX符号
        replacements = {
            '×': r'\times',
            '÷': r'\div',
            '≤': r'\leq',
            '≥': r'\geq',
            '≠': r'\neq',
            '±': r'\pm',
            '∞': r'\infty',
            '∑': r'\sum',
            '∏': r'\prod',
            '∫': r'\int',
            '√': r'\sqrt',
            'α': r'\alpha',
            'β': r'\beta',
            'γ': r'\gamma',
            'δ': r'\delta',
            'ε': r'\epsilon',
            'θ': r'\theta',
            'λ': r'\lambda',
            'μ': r'\mu',
            'π': r'\pi',
            'σ': r'\sigma',
            'φ': r'\phi',
            'ω': r'\omega',
        }
        
        for old, new in replacements.items():
            formula = formula.replace(old, new)
        
        return formula
    
    @staticmethod
    def preserve_formulas_in_text(text: str) -> str:
        """
        在文本中保留公式，确保公式不被清理函数误删
        
        Args:
            text: 输入文本
            
        Returns:
            处理后的文本，公式已标记
        """
        formulas = FormulaExtractor.extract_formulas(text)
        
        # 从后往前替换，避免位置偏移
        for formula_content, formula_type, start, end in reversed(formulas):
            # 规范化公式
            normalized = FormulaExtractor.normalize_formula(formula_content)
            # 用标记包裹公式，确保后续处理不会破坏
            if formula_type == 'block':
                replacement = f'\n\n$${normalized}$$\n\n'
            else:
                replacement = f' ${normalized}$ '
            text = text[:start] + replacement + text[end:]
        
        return text
    
    @staticmethod
    def detect_physics_variables(text: str) -> List[str]:
        """
        检测物理量定义
        
        Args:
            text: 输入文本
            
        Returns:
            物理量定义列表
        """
        physics_vars = []
        for pattern in FormulaExtractor.PHYSICS_PATTERNS:
            matches = re.findall(pattern, text)
            physics_vars.extend(matches)
        return physics_vars


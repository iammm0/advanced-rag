"""公式分析工具 - 提取公式中的变量和关系"""
from typing import Dict, Any, List, Set, Tuple
from utils.formula_extractor import FormulaExtractor
from utils.logger import logger
import re


class FormulaAnalyzer:
    """公式分析器 - 提取公式中的变量、关系和语义信息"""
    
    # 常见数学变量模式（单个字母或带下标）
    VARIABLE_PATTERNS = [
        r'\b([a-zA-Z])\b',  # 单个字母变量：x, y, z
        r'([a-zA-Z])_\{([^}]+)\}',  # 带下标的变量：x_{i}, a_{n}
        r'([a-zA-Z])_([a-zA-Z0-9]+)',  # 简单下标：x_i, a_n
        r'\\mathrm\{([a-zA-Z]+)\}',  # 正体变量：\mathrm{max}
        r'\\text\{([^}]+)\}',  # 文本变量：\text{max}
    ]
    
    # 常见数学关系运算符
    RELATION_OPERATORS = [
        '=', '==', '≠', '!=', '≈', '≈', '≤', '<=', '≥', '>=',
        '<', '>', '∈', '∉', '⊂', '⊃', '⊆', '⊇', '≡', '≅'
    ]
    
    # 常见数学函数
    MATH_FUNCTIONS = [
        'sin', 'cos', 'tan', 'log', 'ln', 'exp', 'sqrt', 'max', 'min',
        'sum', 'prod', 'int', 'lim', 'inf', 'sup'
    ]
    
    @staticmethod
    def analyze_formula(formula: str) -> Dict[str, Any]:
        """
        分析公式，提取变量、关系和语义信息
        
        Args:
            formula: LaTeX格式的公式字符串
        
        Returns:
            包含分析结果的字典：
            - variables: 变量列表
            - relations: 关系列表
            - functions: 函数列表
            - structure: 结构信息
        """
        # 清理公式（移除标记符号）
        clean_formula = formula.strip()
        if clean_formula.startswith('$$'):
            clean_formula = clean_formula[2:]
        if clean_formula.endswith('$$'):
            clean_formula = clean_formula[:-2]
        if clean_formula.startswith('$'):
            clean_formula = clean_formula[1:]
        if clean_formula.endswith('$'):
            clean_formula = clean_formula[:-1]
        clean_formula = clean_formula.strip()
        
        # 提取变量
        variables = FormulaAnalyzer._extract_variables(clean_formula)
        
        # 提取关系
        relations = FormulaAnalyzer._extract_relations(clean_formula)
        
        # 提取函数
        functions = FormulaAnalyzer._extract_functions(clean_formula)
        
        # 分析结构
        structure = FormulaAnalyzer._analyze_structure(clean_formula)
        
        return {
            "variables": list(variables),
            "relations": relations,
            "functions": list(functions),
            "structure": structure,
            "formula": clean_formula
        }
    
    @staticmethod
    def _extract_variables(formula: str) -> Set[str]:
        """提取公式中的变量"""
        variables = set()
        
        # 提取单个字母变量（排除数学函数和常量）
        single_letter_vars = re.findall(r'\b([a-zA-Z])\b', formula)
        for var in single_letter_vars:
            # 排除常见的数学常量
            if var.lower() not in ['e', 'i', 'π', 'pi']:
                variables.add(var)
        
        # 提取带下标的变量
        subscript_vars = re.findall(r'([a-zA-Z])_\{([^}]+)\}', formula)
        for base, sub in subscript_vars:
            variables.add(f"{base}_{{{sub}}}")
        
        # 提取简单下标变量
        simple_subscript = re.findall(r'([a-zA-Z])_([a-zA-Z0-9]+)', formula)
        for base, sub in simple_subscript:
            variables.add(f"{base}_{sub}")
        
        # 提取正体变量
        mathrm_vars = re.findall(r'\\mathrm\{([^}]+)\}', formula)
        variables.update(mathrm_vars)
        
        # 提取文本变量
        text_vars = re.findall(r'\\text\{([^}]+)\}', formula)
        variables.update(text_vars)
        
        return variables
    
    @staticmethod
    def _extract_relations(formula: str) -> List[Dict[str, Any]]:
        """提取公式中的关系"""
        relations = []
        
        # 查找等号关系
        equals = list(re.finditer(r'([^=<>≠≤≥]+)\s*([=≠≈])\s*([^=<>≠≤≥]+)', formula))
        for match in equals:
            left = match.group(1).strip()
            op = match.group(2)
            right = match.group(3).strip()
            relations.append({
                "type": "equality",
                "operator": op,
                "left": left,
                "right": right
            })
        
        # 查找不等式关系
        inequalities = list(re.finditer(r'([^=<>≠≤≥]+)\s*([<>≤≥])\s*([^=<>≠≤≥]+)', formula))
        for match in inequalities:
            left = match.group(1).strip()
            op = match.group(2)
            right = match.group(3).strip()
            relations.append({
                "type": "inequality",
                "operator": op,
                "left": left,
                "right": right
            })
        
        return relations
    
    @staticmethod
    def _extract_functions(formula: str) -> Set[str]:
        """提取公式中的函数"""
        functions = set()
        
        # 查找LaTeX函数命令
        latex_functions = re.findall(r'\\([a-zA-Z]+)\s*\(', formula)
        functions.update(latex_functions)
        
        # 查找普通函数名
        for func_name in FormulaAnalyzer.MATH_FUNCTIONS:
            if re.search(rf'\b{func_name}\s*\(', formula):
                functions.add(func_name)
        
        return functions
    
    @staticmethod
    def _analyze_structure(formula: str) -> Dict[str, Any]:
        """分析公式的结构"""
        # 检查是否是方程
        has_equals = '=' in formula or '=' in formula.replace('\\', '')
        
        # 检查是否包含分数
        has_fraction = '\\frac' in formula or '/' in formula
        
        # 检查是否包含根号
        has_root = '\\sqrt' in formula or '√' in formula
        
        # 检查是否包含积分
        has_integral = '\\int' in formula or '∫' in formula
        
        # 检查是否包含求和/求积
        has_sum = '\\sum' in formula or '∑' in formula
        has_prod = '\\prod' in formula or '∏' in formula
        
        # 检查是否包含矩阵
        has_matrix = '\\begin{matrix}' in formula or '\\begin{pmatrix}' in formula
        
        return {
            "is_equation": has_equals,
            "has_fraction": has_fraction,
            "has_root": has_root,
            "has_integral": has_integral,
            "has_sum": has_sum,
            "has_product": has_prod,
            "has_matrix": has_matrix,
            "complexity": FormulaAnalyzer._calculate_complexity(formula)
        }
    
    @staticmethod
    def _calculate_complexity(formula: str) -> str:
        """计算公式复杂度"""
        # 统计各种元素的数量
        operators = len(re.findall(r'[+\-*/=<>≠≤≥]', formula))
        functions = len(re.findall(r'\\[a-zA-Z]+\s*\(', formula))
        fractions = formula.count('\\frac')
        roots = formula.count('\\sqrt')
        
        total_complexity = operators + functions + fractions * 2 + roots * 2
        
        if total_complexity <= 3:
            return "simple"
        elif total_complexity <= 8:
            return "moderate"
        else:
            return "complex"
    
    @staticmethod
    def extract_all_formulas_info(text: str) -> List[Dict[str, Any]]:
        """
        从文本中提取所有公式并分析
        
        Args:
            text: 输入文本
        
        Returns:
            公式分析结果列表
        """
        formulas = FormulaExtractor.extract_formulas(text)
        analyzed_formulas = []
        
        for formula_content, formula_type, start, end in formulas:
            analysis = FormulaAnalyzer.analyze_formula(formula_content)
            analysis["type"] = formula_type
            analysis["position"] = {"start": start, "end": end}
            analyzed_formulas.append(analysis)
        
        return analyzed_formulas


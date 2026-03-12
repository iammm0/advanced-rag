"""代码分析工具 - 提取代码的语法树和语义信息"""
from typing import Dict, Any, List, Optional, Set
from utils.logger import logger
import re


class CodeAnalyzer:
    """代码分析器 - 提取代码的语法树和语义信息"""
    
    # 常见编程语言的关键字
    LANGUAGE_KEYWORDS = {
        'python': ['def', 'class', 'import', 'from', 'if', 'else', 'elif', 'for', 'while', 'try', 'except', 'return', 'yield', 'async', 'await'],
        'javascript': ['function', 'const', 'let', 'var', 'if', 'else', 'for', 'while', 'try', 'catch', 'async', 'await', 'return'],
        'java': ['public', 'private', 'protected', 'class', 'interface', 'extends', 'implements', 'if', 'else', 'for', 'while', 'try', 'catch', 'return'],
        'cpp': ['class', 'struct', 'namespace', 'public', 'private', 'protected', 'if', 'else', 'for', 'while', 'try', 'catch', 'return'],
    }
    
    @staticmethod
    def detect_language(code: str) -> str:
        """
        检测代码语言
        
        Args:
            code: 代码文本
        
        Returns:
            语言名称（python, javascript, java, cpp等）
        """
        code_lower = code.lower()
        
        # Python特征
        if 'def ' in code or 'import ' in code or 'print(' in code or '__init__' in code:
            return 'python'
        
        # JavaScript特征
        if 'function ' in code or 'const ' in code or 'let ' in code or '=>' in code:
            return 'javascript'
        
        # Java特征
        if 'public class' in code_lower or 'public static void main' in code_lower:
            return 'java'
        
        # C++特征
        if '#include' in code or 'std::' in code or 'namespace ' in code:
            return 'cpp'
        
        return 'unknown'
    
    @staticmethod
    def extract_functions(code: str, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        提取代码中的函数定义
        
        Args:
            code: 代码文本
            language: 编程语言（如果为None则自动检测）
        
        Returns:
            函数定义列表
        """
        if language is None:
            language = CodeAnalyzer.detect_language(code)
        
        functions = []
        
        if language == 'python':
            functions = CodeAnalyzer._extract_python_functions(code)
        elif language == 'javascript':
            functions = CodeAnalyzer._extract_javascript_functions(code)
        elif language == 'java':
            functions = CodeAnalyzer._extract_java_functions(code)
        elif language == 'cpp':
            functions = CodeAnalyzer._extract_cpp_functions(code)
        
        return functions
    
    @staticmethod
    def _extract_python_functions(code: str) -> List[Dict[str, Any]]:
        """提取Python函数"""
        functions = []
        
        # 匹配函数定义：def function_name(params):
        pattern = r'def\s+(\w+)\s*\(([^)]*)\)\s*:'
        matches = re.finditer(pattern, code)
        
        for match in matches:
            func_name = match.group(1)
            params_str = match.group(2)
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            
            functions.append({
                "name": func_name,
                "parameters": params,
                "language": "python"
            })
        
        return functions
    
    @staticmethod
    def _extract_javascript_functions(code: str) -> List[Dict[str, Any]]:
        """提取JavaScript函数"""
        functions = []
        
        # 匹配函数定义：function name(params) 或 const name = (params) =>
        patterns = [
            r'function\s+(\w+)\s*\(([^)]*)\)',
            r'const\s+(\w+)\s*=\s*\(([^)]*)\)\s*=>',
            r'(\w+)\s*:\s*\(([^)]*)\)\s*=>'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                func_name = match.group(1)
                params_str = match.group(2) if len(match.groups()) >= 2 else ""
                params = [p.strip() for p in params_str.split(',') if p.strip()]
                
                functions.append({
                    "name": func_name,
                    "parameters": params,
                    "language": "javascript"
                })
        
        return functions
    
    @staticmethod
    def _extract_java_functions(code: str) -> List[Dict[str, Any]]:
        """提取Java函数"""
        functions = []
        
        # 匹配方法定义：access_modifier return_type methodName(params)
        pattern = r'(?:public|private|protected)?\s*\w+\s+(\w+)\s*\(([^)]*)\)'
        matches = re.finditer(pattern, code)
        
        for match in matches:
            func_name = match.group(1)
            params_str = match.group(2)
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            
            functions.append({
                "name": func_name,
                "parameters": params,
                "language": "java"
            })
        
        return functions
    
    @staticmethod
    def _extract_cpp_functions(code: str) -> List[Dict[str, Any]]:
        """提取C++函数"""
        functions = []
        
        # 匹配函数定义：return_type function_name(params)
        pattern = r'\w+\s+(\w+)\s*\(([^)]*)\)'
        matches = re.finditer(pattern, code)
        
        for match in matches:
            func_name = match.group(1)
            params_str = match.group(2)
            params = [p.strip() for p in params_str.split(',') if p.strip()]
            
            functions.append({
                "name": func_name,
                "parameters": params,
                "language": "cpp"
            })
        
        return functions
    
    @staticmethod
    def extract_classes(code: str, language: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        提取代码中的类定义
        
        Args:
            code: 代码文本
            language: 编程语言
        
        Returns:
            类定义列表
        """
        if language is None:
            language = CodeAnalyzer.detect_language(code)
        
        classes = []
        
        if language == 'python':
            # Python类定义：class ClassName:
            pattern = r'class\s+(\w+)(?:\([^)]+\))?\s*:'
            matches = re.finditer(pattern, code)
            for match in matches:
                class_name = match.group(1)
                classes.append({
                    "name": class_name,
                    "language": "python"
                })
        
        elif language in ['java', 'cpp', 'javascript']:
            # Java/C++/JavaScript类定义：class ClassName
            pattern = r'class\s+(\w+)'
            matches = re.finditer(pattern, code)
            for match in matches:
                class_name = match.group(1)
                classes.append({
                    "name": class_name,
                    "language": language
                })
        
        return classes
    
    @staticmethod
    def extract_imports(code: str, language: Optional[str] = None) -> List[str]:
        """
        提取代码中的导入语句
        
        Args:
            code: 代码文本
            language: 编程语言
        
        Returns:
            导入模块列表
        """
        if language is None:
            language = CodeAnalyzer.detect_language(code)
        
        imports = []
        
        if language == 'python':
            # Python: import module 或 from module import item
            import_pattern = r'(?:import\s+(\w+(?:\.\w+)*)|from\s+(\w+(?:\.\w+)*)\s+import)'
            matches = re.finditer(import_pattern, code)
            for match in matches:
                module = match.group(1) or match.group(2)
                if module:
                    imports.append(module)
        
        elif language == 'javascript':
            # JavaScript: import ... from 'module'
            import_pattern = r"import\s+.*?\s+from\s+['\"]([^'\"]+)['\"]"
            matches = re.finditer(import_pattern, code)
            for match in matches:
                imports.append(match.group(1))
        
        elif language in ['java', 'cpp']:
            # Java/C++: import package.name 或 #include <header>
            if language == 'java':
                import_pattern = r'import\s+([\w.]+)'
            else:
                import_pattern = r'#include\s+[<"]([\w./]+)[>"]'
            
            matches = re.finditer(import_pattern, code)
            for match in matches:
                imports.append(match.group(1))
        
        return imports
    
    @staticmethod
    def analyze_code_block(code: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        分析代码块，提取语法树和语义信息
        
        Args:
            code: 代码文本
            language: 编程语言
        
        Returns:
            包含分析结果的字典
        """
        if language is None:
            language = CodeAnalyzer.detect_language(code)
        
        functions = CodeAnalyzer.extract_functions(code, language)
        classes = CodeAnalyzer.extract_classes(code, language)
        imports = CodeAnalyzer.extract_imports(code, language)
        
        # 提取变量名（简单模式）
        variables = CodeAnalyzer._extract_variables(code, language)
        
        # 提取关键字
        keywords = CodeAnalyzer._extract_keywords(code, language)
        
        return {
            "language": language,
            "functions": functions,
            "classes": classes,
            "imports": imports,
            "variables": variables,
            "keywords": keywords,
            "line_count": len(code.split('\n')),
            "complexity": CodeAnalyzer._estimate_complexity(code, language)
        }
    
    @staticmethod
    def _extract_variables(code: str, language: str) -> Set[str]:
        """提取变量名"""
        variables = set()
        
        if language == 'python':
            # Python变量赋值：variable = value
            pattern = r'(\w+)\s*='
            matches = re.finditer(pattern, code)
            for match in matches:
                var_name = match.group(1)
                if var_name not in ['if', 'for', 'while', 'def', 'class', 'import', 'from']:
                    variables.add(var_name)
        
        elif language == 'javascript':
            # JavaScript: const/let/var variable = value
            pattern = r'(?:const|let|var)\s+(\w+)\s*='
            matches = re.finditer(pattern, code)
            for match in matches:
                variables.add(match.group(1))
        
        return variables
    
    @staticmethod
    def _extract_keywords(code: str, language: str) -> Set[str]:
        """提取关键字"""
        keywords = set()
        
        if language in CodeAnalyzer.LANGUAGE_KEYWORDS:
            lang_keywords = CodeAnalyzer.LANGUAGE_KEYWORDS[language]
            for keyword in lang_keywords:
                if re.search(rf'\b{keyword}\b', code):
                    keywords.add(keyword)
        
        return keywords
    
    @staticmethod
    def _estimate_complexity(code: str, language: str) -> str:
        """估算代码复杂度"""
        lines = code.split('\n')
        line_count = len([l for l in lines if l.strip()])
        
        # 统计控制结构
        control_structures = len(re.findall(r'\b(if|else|elif|for|while|try|except|catch)\b', code))
        
        # 统计函数/方法数量
        functions = len(CodeAnalyzer.extract_functions(code, language))
        
        complexity_score = line_count + control_structures * 2 + functions * 3
        
        if complexity_score <= 20:
            return "simple"
        elif complexity_score <= 50:
            return "moderate"
        else:
            return "complex"


"""Markdown文档解析器"""
from typing import Dict, Any, List
from .base import BaseParser
import markdown
import logging
from markdown.extensions import codehilite, tables, fenced_code

logger = logging.getLogger(__name__)


class MarkdownParser(BaseParser):
    """Markdown文档解析器"""
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """解析Markdown文件（增强版：支持表格提取、代码分析、公式分析）"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                md_content = file.read()
            
            # 运行时开关（同步解析路径）
            try:
                from services.runtime_config import get_runtime_config_sync

                _cfg = get_runtime_config_sync()
                _modules = _cfg.get("modules") or {}
                table_enabled = bool(_modules.get("table_parse_enabled", True))
            except Exception:
                table_enabled = True
            
            # 提取纯文本（去除Markdown标记）
            md = markdown.Markdown(
                extensions=['codehilite', 'tables', 'fenced_code']
            )
            html_content = md.convert(md_content)
            
            # 简单的HTML标签去除（保留文本内容）
            import re
            text = re.sub(r'<[^>]+>', '', html_content)
            text = re.sub(r'\n\s*\n', '\n\n', text)  # 清理多余空行
            
            metadata = {
                "format": "markdown",
                "sections": len(re.findall(r'^#+\s', md_content, re.MULTILINE))
            }
            
            # 增强功能：提取表格
            tables_info = []
            if table_enabled:
                try:
                    from utils.table_extractor import TableExtractor
                    tables = TableExtractor.extract_table_from_text(md_content)
                    for table in tables:
                        tables_info.append({
                            "type": table.get("type"),
                            "html": table.get("html"),
                            "markdown": table.get("markdown"),
                            "semantic": TableExtractor.extract_semantic_structure(table.get("data", []))
                        })
                    if tables_info:
                        metadata["tables"] = tables_info
                except Exception as e:
                    logger.warning(f"表格提取失败: {e}")
            
            # 增强功能：分析代码块
            code_blocks_info = []
            try:
                from utils.code_analyzer import CodeAnalyzer
                # 提取Markdown代码块
                code_block_pattern = r'```(\w+)?\n(.*?)```'
                code_blocks = re.finditer(code_block_pattern, md_content, re.DOTALL)
                
                for match in code_blocks:
                    language = match.group(1) or "unknown"
                    code_content = match.group(2)
                    
                    analysis = CodeAnalyzer.analyze_code_block(code_content, language)
                    code_blocks_info.append({
                        "language": language,
                        "content": code_content,
                        "analysis": analysis
                    })
                
                if code_blocks_info:
                    metadata["code_blocks"] = code_blocks_info
            except Exception as e:
                logger.warning(f"代码分析失败: {e}")
            
            # 增强功能：分析公式
            formulas_info = []
            try:
                from utils.formula_analyzer import FormulaAnalyzer
                formulas_info = FormulaAnalyzer.extract_all_formulas_info(md_content)
                if formulas_info:
                    metadata["formulas"] = formulas_info
            except Exception as e:
                logger.warning(f"公式分析失败: {e}")
            
            return {
                "text": text,
                "raw_markdown": md_content,
                "metadata": metadata
            }
        except Exception as e:
            raise Exception(f"Failed to parse Markdown file: {e}")
    
    def supported_extensions(self) -> List[str]:
        return ["md", "markdown"]


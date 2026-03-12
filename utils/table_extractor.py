"""表格提取工具 - 提取表格并转换为多种格式"""
from typing import Dict, Any, List, Optional
from utils.logger import logger
import re


class TableExtractor:
    """表格提取和格式化工具"""
    
    @staticmethod
    def extract_table_from_text(text: str) -> List[Dict[str, Any]]:
        """
        从文本中识别表格结构
        
        Args:
            text: 输入文本
        
        Returns:
            表格列表，每个表格包含格式化的文本和结构信息
        """
        tables = []
        
        # 识别Markdown表格格式
        markdown_tables = TableExtractor._extract_markdown_tables(text)
        tables.extend(markdown_tables)
        
        # 识别管道分隔的表格（| 分隔）
        pipe_tables = TableExtractor._extract_pipe_tables(text)
        tables.extend(pipe_tables)
        
        return tables
    
    @staticmethod
    def _extract_markdown_tables(text: str) -> List[Dict[str, Any]]:
        """提取Markdown格式的表格"""
        tables = []
        lines = text.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            # 检查是否是表格行（包含 | 分隔符）
            if '|' in line and line.count('|') >= 2:
                # 检查下一行是否是分隔行（包含 --- 或 ===）
                if i + 1 < len(lines):
                    next_line = lines[i + 1].strip()
                    if re.match(r'^\|[\s\-:|=]+\|', next_line):
                        # 找到表格开始
                        table_lines = [line]
                        i += 1
                        table_lines.append(next_line)  # 分隔行
                        i += 1
                        
                        # 收集表格数据行
                        while i < len(lines):
                            current_line = lines[i].strip()
                            if '|' in current_line:
                                table_lines.append(current_line)
                                i += 1
                            else:
                                break
                        
                        # 解析表格
                        table_data = TableExtractor._parse_markdown_table(table_lines)
                        if table_data:
                            tables.append({
                                "type": "markdown",
                                "raw": "\n".join(table_lines),
                                "data": table_data,
                                "html": TableExtractor._to_html(table_data),
                                "markdown": "\n".join(table_lines)
                            })
                        continue
            i += 1
        
        return tables
    
    @staticmethod
    def _extract_pipe_tables(text: str) -> List[Dict[str, Any]]:
        """提取管道分隔的表格（| 分隔）"""
        tables = []
        lines = text.split('\n')
        
        current_table = []
        for line in lines:
            line = line.strip()
            # 检查是否是表格行（包含 | 分隔符，且至少2个）
            if '|' in line and line.count('|') >= 2:
                # 移除首尾的 |
                parts = [p.strip() for p in line.split('|') if p.strip()]
                if len(parts) >= 2:  # 至少2列
                    current_table.append(parts)
                else:
                    # 如果当前有表格数据，保存它
                    if current_table:
                        table_data = TableExtractor._parse_pipe_table(current_table)
                        if table_data:
                            tables.append({
                                "type": "pipe",
                                "raw": "\n".join([" | ".join(row) for row in current_table]),
                                "data": table_data,
                                "html": TableExtractor._to_html(table_data),
                                "markdown": TableExtractor._to_markdown(table_data)
                            })
                        current_table = []
            else:
                # 如果当前有表格数据，保存它
                if current_table:
                    table_data = TableExtractor._parse_pipe_table(current_table)
                    if table_data:
                        tables.append({
                            "type": "pipe",
                            "raw": "\n".join([" | ".join(row) for row in current_table]),
                            "data": table_data,
                            "html": TableExtractor._to_html(table_data),
                            "markdown": TableExtractor._to_markdown(table_data)
                        })
                    current_table = []
        
        # 处理最后一个表格
        if current_table:
            table_data = TableExtractor._parse_pipe_table(current_table)
            if table_data:
                tables.append({
                    "type": "pipe",
                    "raw": "\n".join([" | ".join(row) for row in current_table]),
                    "data": table_data,
                    "html": TableExtractor._to_html(table_data),
                    "markdown": TableExtractor._to_markdown(table_data)
                })
        
        return tables
    
    @staticmethod
    def _parse_markdown_table(lines: List[str]) -> Optional[List[List[str]]]:
        """解析Markdown表格"""
        if len(lines) < 2:
            return None
        
        # 跳过分隔行（第二行）
        data_lines = [lines[0]] + lines[2:]
        
        table_data = []
        for line in data_lines:
            # 移除首尾的 |
            parts = [p.strip() for p in line.split('|')]
            # 移除空的首尾元素
            if parts and not parts[0]:
                parts = parts[1:]
            if parts and not parts[-1]:
                parts = parts[:-1]
            
            if parts:
                table_data.append(parts)
        
        return table_data if table_data else None
    
    @staticmethod
    def _parse_pipe_table(rows: List[List[str]]) -> Optional[List[List[str]]]:
        """解析管道分隔的表格"""
        if not rows:
            return None
        
        # 确保所有行的列数一致（以第一行为准）
        max_cols = max(len(row) for row in rows) if rows else 0
        normalized_rows = []
        
        for row in rows:
            normalized_row = row + [''] * (max_cols - len(row))
            normalized_rows.append(normalized_row[:max_cols])
        
        return normalized_rows if normalized_rows else None
    
    @staticmethod
    def _to_html(table_data: List[List[str]]) -> str:
        """将表格数据转换为HTML格式"""
        if not table_data:
            return ""
        
        html_parts = ['<table class="document-table">']
        
        # 第一行作为表头
        if len(table_data) > 0:
            html_parts.append('  <thead>')
            html_parts.append('    <tr>')
            for cell in table_data[0]:
                html_parts.append(f'      <th>{TableExtractor._escape_html(cell)}</th>')
            html_parts.append('    </tr>')
            html_parts.append('  </thead>')
        
        # 数据行
        if len(table_data) > 1:
            html_parts.append('  <tbody>')
            for row in table_data[1:]:
                html_parts.append('    <tr>')
                for cell in row:
                    html_parts.append(f'      <td>{TableExtractor._escape_html(cell)}</td>')
                html_parts.append('    </tr>')
            html_parts.append('  </tbody>')
        
        html_parts.append('</table>')
        return '\n'.join(html_parts)
    
    @staticmethod
    def _to_markdown(table_data: List[List[str]]) -> str:
        """将表格数据转换为Markdown格式"""
        if not table_data:
            return ""
        
        markdown_parts = []
        
        # 表头
        if len(table_data) > 0:
            header = table_data[0]
            markdown_parts.append('| ' + ' | '.join(header) + ' |')
            markdown_parts.append('| ' + ' | '.join(['---'] * len(header)) + ' |')
        
        # 数据行
        for row in table_data[1:]:
            markdown_parts.append('| ' + ' | '.join(row) + ' |')
        
        return '\n'.join(markdown_parts)
    
    @staticmethod
    def _escape_html(text: str) -> str:
        """转义HTML特殊字符"""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#39;'))
    
    @staticmethod
    def extract_semantic_structure(table_data: List[List[str]]) -> Dict[str, Any]:
        """
        提取表格的语义结构信息
        
        Args:
            table_data: 表格数据（二维列表）
        
        Returns:
            包含语义信息的字典：
            - row_count: 行数
            - col_count: 列数
            - headers: 表头列表
            - data_types: 每列的数据类型推测
            - has_numeric: 是否包含数值列
        """
        if not table_data:
            return {}
        
        row_count = len(table_data)
        col_count = len(table_data[0]) if table_data else 0
        
        # 提取表头（第一行）
        headers = table_data[0] if table_data else []
        
        # 推测每列的数据类型
        data_types = []
        has_numeric = False
        
        if len(table_data) > 1:
            for col_idx in range(col_count):
                col_values = [row[col_idx] if col_idx < len(row) else '' for row in table_data[1:]]
                col_values = [v.strip() for v in col_values if v.strip()]
                
                # 检查是否全是数字
                numeric_count = sum(1 for v in col_values if re.match(r'^-?\d+\.?\d*$', v))
                if numeric_count == len(col_values) and col_values:
                    data_types.append("numeric")
                    has_numeric = True
                # 检查是否包含数字
                elif numeric_count > 0:
                    data_types.append("mixed")
                    has_numeric = True
                else:
                    data_types.append("text")
        else:
            data_types = ["text"] * col_count
        
        return {
            "row_count": row_count,
            "col_count": col_count,
            "headers": headers,
            "data_types": data_types,
            "has_numeric": has_numeric
        }


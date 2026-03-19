"""结果合成器 - 统一不同解析器的输出格式"""
from typing import Dict, Any, List, Optional
from utils.logger import logger


def _table_to_text(table: Dict[str, Any]) -> str:
    """从表格信息中取 Markdown 或 HTML 或 semantic 的文本表示。"""
    if table.get("markdown"):
        return table["markdown"].strip()
    if table.get("html"):
        return table["html"].strip()
    semantic = table.get("semantic")
    if isinstance(semantic, str):
        return semantic.strip()
    if isinstance(semantic, dict):
        return str(semantic).strip()
    return ""


class ResultSynthesizer:
    """结果合成器 - 将不同解析器的输出统一为 Document 对象格式，支持将表格/代码块写回正文以降低语义损失。"""

    def __init__(
        self,
        merge_tables_into_text: bool = True,
        merge_code_blocks_into_text: bool = True,
        use_raw_markdown_if_present: bool = True,
    ):
        """
        初始化合成器

        Args:
            merge_tables_into_text: 是否将 metadata["tables"] 的 Markdown 拼接到 text
            merge_code_blocks_into_text: 是否将 metadata["code_blocks"] 的代码内容拼接到 text
            use_raw_markdown_if_present: 若解析结果含 raw_markdown，是否优先作为正文（保留标题等结构）
        """
        self.merge_tables_into_text = merge_tables_into_text
        self.merge_code_blocks_into_text = merge_code_blocks_into_text
        self.use_raw_markdown_if_present = use_raw_markdown_if_present

    def synthesize(
        self,
        parse_result: Dict[str, Any],
        parser_type: str,
        file_path: str,
        *,
        merge_tables_into_text: Optional[bool] = None,
        merge_code_blocks_into_text: Optional[bool] = None,
        use_raw_markdown_if_present: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        合成解析结果为标准格式，可选将表格/代码块/raw_markdown 写回正文。

        Args:
            parse_result: 解析器返回的原始结果
            parser_type: 解析器类型（用于记录）
            file_path: 文件路径
            merge_tables_into_text: 覆盖实例默认值
            merge_code_blocks_into_text: 覆盖实例默认值
            use_raw_markdown_if_present: 覆盖实例默认值

        Returns:
            统一格式：text, metadata
        """
        merge_tables = merge_tables_into_text if merge_tables_into_text is not None else self.merge_tables_into_text
        merge_code = merge_code_blocks_into_text if merge_code_blocks_into_text is not None else self.merge_code_blocks_into_text
        use_raw_md = use_raw_markdown_if_present if use_raw_markdown_if_present is not None else self.use_raw_markdown_if_present

        metadata = dict(parse_result.get("metadata", {}))

        # 基准正文：优先 raw_markdown 以保留 Markdown 标题等结构
        if use_raw_md and parse_result.get("raw_markdown"):
            text = parse_result["raw_markdown"]
        else:
            text = parse_result.get("text", "") or ""

        # 将表格写回正文
        if merge_tables and metadata.get("tables"):
            for table in metadata["tables"]:
                part = _table_to_text(table)
                if part:
                    text += "\n\n[表格]\n" + part

        # 将代码块写回正文
        if merge_code and metadata.get("code_blocks"):
            for block in metadata["code_blocks"]:
                lang = block.get("language", "text")
                content = block.get("content", "")
                if content is None:
                    content = ""
                text += "\n\n```" + str(lang) + "\n" + str(content) + "\n```\n"

        metadata["parser_type"] = parser_type
        metadata["file_path"] = file_path

        if not text or not text.strip():
            logger.warning(f"解析结果文本为空: {file_path}, 解析器类型: {parser_type}")

        synthesized_result = {"text": text, "metadata": metadata}
        logger.debug(f"结果合成完成: {file_path}, 文本长度: {len(text)}, 解析器类型: {parser_type}")
        return synthesized_result
    
    def merge_multiple_results(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        合并多个解析结果（如果需要）
        
        Args:
            results: 解析结果列表
        
        Returns:
            合并后的结果
        """
        if not results:
            return {"text": "", "metadata": {}}
        
        if len(results) == 1:
            return results[0]
        
        # 合并文本
        texts = [r.get("text", "") for r in results]
        merged_text = "\n\n".join(texts)
        
        # 合并元数据
        merged_metadata = {}
        for r in results:
            metadata = r.get("metadata", {})
            merged_metadata.update(metadata)
        
        return {
            "text": merged_text,
            "metadata": merged_metadata
        }


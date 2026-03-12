"""结果合成器 - 统一不同解析器的输出格式"""
from typing import Dict, Any, List, Optional
from utils.logger import logger


class ResultSynthesizer:
    """结果合成器 - 将不同解析器的输出统一为 Document 对象格式"""
    
    def __init__(self):
        """初始化合成器"""
        pass
    
    def synthesize(self, parse_result: Dict[str, Any], parser_type: str, file_path: str) -> Dict[str, Any]:
        """
        合成解析结果为标准格式
        
        Args:
            parse_result: 解析器返回的原始结果
            parser_type: 解析器类型（用于记录）
            file_path: 文件路径
        
        Returns:
            统一格式的文档对象：
            - text: 文本内容
            - metadata: 元数据（包含解析器类型等信息）
        """
        # 确保结果包含必要的字段
        text = parse_result.get("text", "")
        metadata = parse_result.get("metadata", {})
        
        # 添加解析器类型信息
        metadata["parser_type"] = parser_type
        metadata["file_path"] = file_path
        
        # 确保文本不为空
        if not text or not text.strip():
            logger.warning(f"解析结果文本为空: {file_path}, 解析器类型: {parser_type}")
        
        # 统一元数据格式
        synthesized_result = {
            "text": text,
            "metadata": metadata
        }
        
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


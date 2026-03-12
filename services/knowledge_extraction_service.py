
import json
import re
import asyncio
from typing import List, Dict, Any
from services.ollama_service import OllamaService
from database.neo4j_client import neo4j_client
from utils.logger import logger

class KnowledgeExtractionService:
    """知识抽取与图谱构建服务"""
    
    def __init__(self):
        """初始化知识抽取服务"""
        self.ollama_service = OllamaService()
        self.extraction_prompt_template = """
你是一个知识图谱专家。请从以下文本中提取“实体-关系-实体”三元组。
请严格按照 JSON 格式返回结果，不要包含任何其他解释性文字。
返回格式示例：
[
  {{ "head": "实体1", "head_type": "类型1", "relation": "关系", "tail": "实体2", "tail_type": "类型2" }},
  ...
]

实体类型可以是：Concept(概念), Technology(技术), Person(人物), Organization(组织), Location(地点), Event(事件), Other(其他)。
关系应当简洁明了。

文本内容：
{text}
"""

    async def extract_triplets(self, text: str) -> List[Dict[str, Any]]:
        """
        使用 Ollama 提取三元组
        
        Args:
            text: 输入文本
            
        Returns:
            三元组列表，每个三元组是一个字典
        """
        prompt = self.extraction_prompt_template.format(text=text)
        
        try:
            # 使用 Ollama 生成
            # 我们直接调用 API 以避免 OllamaService 的 prompt 包装
            response = self.ollama_service.session.post(
                f"{self.ollama_service.base_url}/api/generate",
                json={
                    "model": self.ollama_service.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"  # 强制 JSON 输出
                },
                timeout=120
            )
            response.raise_for_status()
            result = response.json()
            content = result.get("response", "")
            
            # 解析 JSON
            triplets = self._parse_json(content)
            return triplets
        except Exception as e:
            logger.error(f"知识抽取失败: {e}")
            return []

    def _parse_json(self, content: str) -> List[Dict[str, Any]]:
        """解析 LLM 返回的 JSON 字符串"""
        parsed = None
        try:
            # 尝试直接解析
            parsed = json.loads(content)
        except json.JSONDecodeError:
            # 尝试从 markdown 代码块中提取
            match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if match:
                try:
                    parsed = json.loads(match.group(1))
                except:
                    pass
            
        if parsed is None:
            # 尝试修复常见的 JSON 错误 (简单的)
            try:
                # 有时候模型返回的不是 list 而是单个 object
                if content.strip().startswith("{"):
                    parsed = json.loads(content)
            except:
                pass
        
        if parsed is None:
            logger.warning(f"无法解析 JSON: {content[:100]}...")
            return []
            
        if isinstance(parsed, dict):
            return [parsed]
        elif isinstance(parsed, list):
            return parsed
        else:
            logger.warning(f"JSON 解析结果不是列表或字典: {type(parsed)}")
            return []

    async def extract_entities(self, query: str) -> List[str]:
        """
        从查询中提取实体
        
        Args:
            query: 用户查询字符串
            
        Returns:
            实体名称列表
        """
        prompt = f"""
请从以下查询中提取关键实体（人名、地名、组织、概念、技术术语等）。
只返回实体列表，JSON 格式：["实体1", "实体2"]。
不要包含任何解释。

查询：{query}
"""
        try:
            response = self.ollama_service.session.post(
                f"{self.ollama_service.base_url}/api/generate",
                json={
                    "model": self.ollama_service.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json"
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            content = result.get("response", "")
            
            entities = self._parse_json(content)
            if isinstance(entities, list):
                return [str(e) for e in entities if isinstance(e, (str, int, float))]
            return []
        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return []

    async def build_graph(self, text: str, metadata: Dict[str, Any] = None):
        """
        构建知识图谱：抽取并存入 Neo4j
        
        Args:
            text: 输入文本
            metadata: 元数据（包含文档ID等）
        """
        if not neo4j_client.driver:
            neo4j_client.connect()
            if not neo4j_client.driver:
                logger.warning("Neo4j 未连接，跳过图谱构建")
                return

        triplets = await self.extract_triplets(text)
        if not triplets:
            return

        doc_id = metadata.get("document_id") if metadata else None
        chunk_id = metadata.get("chunk_id") if metadata else None

        for triplet in triplets:
            try:
                head = triplet.get("head")
                head_type = triplet.get("head_type", "Concept")
                tail = triplet.get("tail")
                tail_type = triplet.get("tail_type", "Concept")
                relation = triplet.get("relation")

                if not head or not tail or not relation:
                    continue

                # 创建节点
                neo4j_client.create_entity(head_type, {"name": head})
                neo4j_client.create_entity(tail_type, {"name": tail})

                # 创建关系
                rel_props = {}
                if doc_id:
                    rel_props["source_doc"] = doc_id
                if chunk_id:
                    rel_props["source_chunk"] = chunk_id
                
                neo4j_client.create_relationship(
                    head, head_type,
                    tail, tail_type,
                    self._normalize_relation(relation),
                    rel_props
                )
            except Exception as e:
                logger.error(f"图谱构建错误 (triplet: {triplet}): {e}")

    def _normalize_relation(self, relation: str) -> str:
        """
        规范化关系名称 (Neo4j 关系类型通常是大写，无空格)
        
        Args:
            relation: 原始关系名称
            
        Returns:
            规范化后的关系名称
        """
        # 简单处理：转大写，空格转下划线，去除非法字符
        clean = re.sub(r'[^\w]', '_', relation)
        return clean.upper()

knowledge_extraction_service = KnowledgeExtractionService()

"""资源推荐服务"""
from typing import List, Dict, Any, Optional
from database.mongodb import mongodb, ResourceRepository, mongodb_client
from database.qdrant_client import get_qdrant_client
from embedding.embedding_service import embedding_service
from utils.logger import logger
import jieba
import jieba.analyse


class RecommendationService:
    """资源推荐服务"""

    def __init__(self):
        self.resource_repo = None

    def _get_resource_repo(self) -> ResourceRepository:
        """获取资源仓库（延迟初始化）"""
        if self.resource_repo is None:
            mongodb_client.connect()
            self.resource_repo = ResourceRepository(mongodb_client)
        return self.resource_repo

    async def get_user_recent_queries(self, user_id: str, limit: int = 10) -> List[str]:
        """
        获取用户最近的查询内容

        Args:
            user_id: 用户ID
            limit: 返回的查询数量

        Returns:
            查询内容列表
        """
        try:
            collection = mongodb.get_collection("conversations")

            # 获取用户最近的对话
            cursor = collection.find({"user_id": user_id}).sort("updated_at", -1).limit(5)

            queries = []
            async for conv in cursor:
                messages = conv.get("messages", [])
                # 提取用户消息（最近的消息优先）
                for msg in reversed(messages):
                    if msg.get("role") == "user":
                        content = msg.get("content", "").strip()
                        if content and len(content) > 5:  # 过滤太短的消息
                            queries.append(content)
                            if len(queries) >= limit:
                                break
                    if len(queries) >= limit:
                        break
                if len(queries) >= limit:
                    break

            logger.info(f"获取用户查询历史 - 用户ID: {user_id}, 查询数量: {len(queries)}")
            return queries
        except Exception as e:
            logger.error(f"获取用户查询历史失败: {str(e)}", exc_info=True)
            return []

    def extract_keywords(self, text: str, top_k: int = 10) -> List[str]:
        """
        提取文本关键词

        Args:
            text: 文本内容
            top_k: 返回的关键词数量

        Returns:
            关键词列表
        """
        try:
            # 使用jieba提取关键词
            keywords = jieba.analyse.extract_tags(text, topK=top_k, withWeight=False)
            return keywords
        except Exception as e:
            logger.error(f"提取关键词失败: {str(e)}", exc_info=True)
            return []

    def calculate_keyword_score(self, resource_description: str, keywords: List[str]) -> float:
        """
        计算资源描述与关键词的匹配分数

        Args:
            resource_description: 资源描述
            keywords: 关键词列表

        Returns:
            匹配分数（0-1）
        """
        if not keywords or not resource_description:
            return 0.0

        description_lower = resource_description.lower()
        matched_count = 0

        for keyword in keywords:
            if keyword.lower() in description_lower:
                matched_count += 1

        # 计算匹配率
        score = matched_count / len(keywords)
        return min(score, 1.0)

    def calculate_tag_score(self, resource_tags: List[str], keywords: List[str]) -> float:
        """
        计算资源标签与关键词的匹配分数

        Args:
            resource_tags: 资源标签列表
            keywords: 关键词列表

        Returns:
            匹配分数（0-1）
        """
        if not keywords or not resource_tags:
            return 0.0

        tags_lower = [tag.lower() for tag in resource_tags]
        keywords_lower = [keyword.lower() for keyword in keywords]

        matched_count = 0
        for keyword in keywords_lower:
            # 检查关键词是否在标签中（完全匹配或包含）
            for tag in tags_lower:
                if keyword in tag or tag in keyword:
                    matched_count += 1
                    break  # 每个关键词只匹配一次

        # 计算匹配率
        score = matched_count / len(keywords)
        return min(score, 1.0)

    async def search_similar_resources(
        self,
        query_text: str,
        assistant_id: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, float]:
        """
        使用向量相似度搜索资源

        Args:
            query_text: 查询文本
            assistant_id: 助手ID（可选）
            limit: 返回数量

        Returns:
            资源ID到相似度分数的字典
        """
        try:
            # 获取助手对应的集合名称
            collection_name = "sensor_knowledge"  # 默认集合
            if assistant_id:
                try:
                    assistant_collection = mongodb.get_collection("course_assistants")
                    assistant_doc = await assistant_collection.find_one({"_id": assistant_id})
                    if assistant_doc:
                        collection_name = assistant_doc.get("collection_name", "sensor_knowledge")
                except Exception as e:
                    logger.warning(f"获取助手集合名称失败: {str(e)}")

            resource_collection_name = f"{collection_name}_resources"

            # 向量化查询文本
            query_vector = embedding_service.encode([query_text])[0]

            # 在Qdrant中搜索
            qdrant_client_instance = get_qdrant_client(resource_collection_name)

            # 检查Qdrant服务是否可用
            if not qdrant_client_instance.check_health():
                logger.warning(f"Qdrant服务不可用，跳过向量搜索")
                return []

            # 搜索相似向量
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            search_filter = None
            if assistant_id:
                # 如果需要按助手筛选，需要在payload中存储assistant_id
                # 这里先不做筛选，后续可以优化
                pass

            search_results = qdrant_client_instance.client.search(
                collection_name=resource_collection_name,
                query_vector=query_vector,
                limit=limit * 2,  # 多搜索一些，后续会过滤
                score_threshold=0.3  # 相似度阈值
            )

            # 提取资源ID和分数
            resource_scores = {}
            for result in search_results:
                resource_id = result.payload.get("resource_id")
                score = result.score
                if resource_id:
                    # 如果同一个资源有多个向量，取最高分
                    if resource_id not in resource_scores or score > resource_scores[resource_id]:
                        resource_scores[resource_id] = score

            logger.info(f"向量搜索完成 - 找到 {len(resource_scores)} 个相似资源")
            return resource_scores
        except Exception as e:
            logger.error(f"向量搜索失败: {str(e)}", exc_info=True)
            return {}

    async def recommend_resources(
        self,
        user_id: str,
        assistant_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        推荐资源（混合算法：关键词匹配 + 向量相似度）

        Args:
            user_id: 用户ID
            assistant_id: 助手ID（可选）
            limit: 返回数量

        Returns:
            推荐资源列表（包含推荐分数）
        """
        try:
            # 1. 获取用户最近的查询
            queries = await self.get_user_recent_queries(user_id, limit=5)

            if not queries:
                # 如果没有查询历史，返回热门资源（按创建时间排序）
                logger.info(f"用户无查询历史，返回热门资源 - 用户ID: {user_id}")
                repo = self._get_resource_repo()
                resources = repo.list_resources(
                    skip=0,
                    limit=limit,
                    assistant_id=assistant_id,
                    status="active",
                    is_public=True
                )

                result = []
                for resource in resources:
                    result.append({
                        "resource_id": resource["_id"],
                        "title": resource.get("title", ""),
                        "description": resource.get("description", ""),
                        "file_type": resource.get("file_type", ""),
                        "file_size": resource.get("file_size", 0),
                        "score": 0.5  # 默认分数
                    })
                return result

            # 2. 合并所有查询文本
            combined_query = " ".join(queries)

            # 3. 提取关键词
            keywords = self.extract_keywords(combined_query, top_k=10)
            logger.info(f"提取关键词: {keywords}")

            # 4. 向量相似度搜索
            vector_scores = await self.search_similar_resources(
                combined_query,
                assistant_id=assistant_id,
                limit=limit * 2
            )

            # 5. 获取资源详情并计算综合分数
            repo = self._get_resource_repo()
            resource_scores = {}

            # 处理向量搜索结果
            for resource_id, vector_score in vector_scores.items():
                resource = repo.get_resource(resource_id)
                if not resource:
                    continue

                # 检查资源状态
                if resource.get("status") != "active" or not resource.get("is_public", True):
                    continue

                # 如果指定了助手，检查是否匹配
                if assistant_id and resource.get("assistant_id") != assistant_id:
                    continue

                # 计算关键词匹配分数
                description = resource.get("description", "")
                keyword_score = self.calculate_keyword_score(description, keywords)

                # 计算标签匹配分数
                resource_tags = resource.get("tags", [])
                tag_score = self.calculate_tag_score(resource_tags, keywords)

                # 综合分数：向量相似度 * 0.5 + 关键词匹配 * 0.3 + 标签匹配 * 0.2
                combined_score = vector_score * 0.5 + keyword_score * 0.3 + tag_score * 0.2

                resource_scores[resource_id] = {
                    "resource": resource,
                    "vector_score": vector_score,
                    "keyword_score": keyword_score,
                    "tag_score": tag_score,
                    "combined_score": combined_score
                }

            # 6. 如果没有向量搜索结果，使用关键词匹配所有资源
            if not resource_scores:
                logger.info("无向量搜索结果，使用关键词匹配所有资源")
                all_resources = repo.list_resources(
                    skip=0,
                    limit=limit * 3,
                    assistant_id=assistant_id,
                    status="active",
                    is_public=True
                )

                for resource in all_resources:
                    description = resource.get("description", "")
                    keyword_score = self.calculate_keyword_score(description, keywords)

                    # 计算标签匹配分数
                    resource_tags = resource.get("tags", [])
                    tag_score = self.calculate_tag_score(resource_tags, keywords)

                    # 综合分数：关键词匹配 * 0.7 + 标签匹配 * 0.3
                    combined_score = keyword_score * 0.7 + tag_score * 0.3

                    if combined_score > 0.1:  # 至少要有10%的综合匹配
                        resource_scores[resource["_id"]] = {
                            "resource": resource,
                            "vector_score": 0.0,
                            "keyword_score": keyword_score,
                            "tag_score": tag_score,
                            "combined_score": combined_score
                        }

            # 7. 按综合分数排序
            sorted_resources = sorted(
                resource_scores.items(),
                key=lambda x: x[1]["combined_score"],
                reverse=True
            )

            # 8. 构建返回结果
            result = []
            for resource_id, scores in sorted_resources[:limit]:
                resource = scores["resource"]
                result.append({
                    "resource_id": resource_id,
                    "title": resource.get("title", ""),
                    "description": resource.get("description", ""),
                    "file_type": resource.get("file_type", ""),
                    "file_size": resource.get("file_size", 0),
                    "score": scores["combined_score"]
                })

            logger.info(f"推荐资源完成 - 用户ID: {user_id}, 返回 {len(result)} 个资源")
            return result
        except Exception as e:
            logger.error(f"推荐资源失败: {str(e)}", exc_info=True)
            return []

    async def recommend_similar_resources(
        self,
        resource_id: str,
        assistant_id: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        根据资源ID推荐相似资源（基于关键词、标题、标签、描述）

        Args:
            resource_id: 资源ID
            assistant_id: 助手ID（可选）
            limit: 返回数量

        Returns:
            推荐资源列表（包含推荐分数）
        """
        try:
            repo = self._get_resource_repo()
            resource = repo.get_resource(resource_id)

            if not resource:
                logger.warning(f"资源不存在 - 资源ID: {resource_id}")
                return []

            # 构建查询文本：标题 + 描述 + 标签
            title = resource.get("title", "")
            description = resource.get("description", "")
            tags = resource.get("tags", [])

            # 组合查询文本
            query_parts = []
            if title:
                query_parts.append(title)
            if description:
                query_parts.append(description)
            if tags:
                query_parts.extend(tags)

            query_text = " ".join(query_parts)

            if not query_text.strip():
                logger.warning(f"资源没有可用的查询文本 - 资源ID: {resource_id}")
                return []

            logger.info(f"开始推荐相似资源 - 资源ID: {resource_id}, 查询文本: {query_text[:100]}...")

            # 使用向量搜索找到相似资源
            resource_scores = await self.search_similar_resources(
                query_text=query_text,
                assistant_id=assistant_id,
                limit=limit * 2  # 多搜索一些，因为要排除当前资源
            )

            # 从数据库获取资源详细信息
            repo = self._get_resource_repo()
            result = []

            for similar_resource_id, score in resource_scores.items():
                # 排除当前资源
                if similar_resource_id == resource_id:
                    continue

                # 获取资源详细信息
                similar_resource = repo.get_resource(similar_resource_id)
                if not similar_resource:
                    continue

                # 只返回active状态的公开资源
                if similar_resource.get("status") != "active" or not similar_resource.get("is_public", False):
                    continue

                # 计算关键词匹配分数
                similar_title = similar_resource.get("title", "")
                similar_description = similar_resource.get("description", "")
                similar_tags = similar_resource.get("tags", [])

                # 提取关键词
                keywords = self.extract_keywords(query_text, top_k=10)

                # 计算标题匹配分数
                title_score = self.calculate_keyword_score(similar_title, keywords)

                # 计算描述匹配分数
                desc_score = self.calculate_keyword_score(similar_description, keywords)

                # 计算标签匹配分数
                tag_score = self.calculate_tag_score(similar_tags, keywords)

                # 综合分数：向量相似度 * 0.6 + 关键词匹配 * 0.4
                keyword_score = (title_score * 0.4 + desc_score * 0.3 + tag_score * 0.3)
                combined_score = score * 0.6 + keyword_score * 0.4

                result.append({
                    "resource_id": similar_resource_id,
                    "title": similar_title,
                    "description": similar_description,
                    "file_type": similar_resource.get("file_type", ""),
                    "file_size": similar_resource.get("file_size", 0),
                    "url": similar_resource.get("url"),  # 外部链接URL
                    "thumbnail_url": similar_resource.get("thumbnail_url"),  # 视频封面URL
                    "score": combined_score
                })

                if len(result) >= limit:
                    break

            # 按分数排序
            result.sort(key=lambda x: x["score"], reverse=True)

            logger.info(f"推荐相似资源完成 - 资源ID: {resource_id}, 返回 {len(result)} 个资源")
            return result
        except Exception as e:
            logger.error(f"推荐相似资源失败: {str(e)}", exc_info=True)
            return []


# 全局推荐服务实例
recommendation_service = RecommendationService()

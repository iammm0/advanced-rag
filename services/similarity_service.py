"""相似度计算服务 - 计算用户之间的相似度"""
from typing import Dict, Any, List, Optional
from utils.logger import logger
import re
from collections import Counter


class SimilarityService:
    """相似度计算服务"""
    
    def __init__(self):
        """初始化相似度服务"""
        pass
    
    def calculate_text_similarity(self, user1: Dict[str, Any], user2: Dict[str, Any]) -> float:
        """
        计算文本相似度（基于TF-IDF或简单词汇重叠）
        
        Args:
            user1: 用户1的文档
            user2: 用户2的文档
            
        Returns:
            相似度分数（0-1之间）
        """
        try:
            # 提取文本字段
            text1_fields = []
            text2_fields = []
            
            # 从用户1提取文本
            if user1.get("bio"):
                text1_fields.append(user1["bio"])
            if user1.get("personality"):
                text1_fields.append(user1["personality"])
            if user1.get("full_name"):
                text1_fields.append(user1["full_name"])
            
            # 从用户2提取文本
            if user2.get("bio"):
                text2_fields.append(user2["bio"])
            if user2.get("personality"):
                text2_fields.append(user2["personality"])
            if user2.get("full_name"):
                text2_fields.append(user2["full_name"])
            
            text1 = " ".join(text1_fields)
            text2 = " ".join(text2_fields)
            
            if not text1 or not text2:
                return 0.0
            
            # 简单的词汇重叠相似度（Jaccard相似度）
            words1 = set(re.findall(r'\w+', text1.lower()))
            words2 = set(re.findall(r'\w+', text2.lower()))
            
            if not words1 or not words2:
                return 0.0
            
            intersection = len(words1 & words2)
            union = len(words1 | words2)
            
            if union == 0:
                return 0.0
            
            return intersection / union
            
        except Exception as e:
            logger.error(f"计算文本相似度失败: {str(e)}", exc_info=True)
            return 0.0
    
    def calculate_field_similarity(self, user1: Dict[str, Any], user2: Dict[str, Any], weights: Optional[Dict[str, float]] = None) -> float:
        """
        计算字段匹配度
        
        Args:
            user1: 用户1的文档
            user2: 用户2的文档
            weights: 字段权重字典
            
        Returns:
            相似度分数（0-1之间）
        """
        try:
            # 默认权重
            default_weights = {
                "research_fields": 0.3,
                "skills": 0.2,
                "college": 0.15,
                "major": 0.15,
                "user_type": 0.1,
                "interests": 0.1
            }
            
            if weights is None:
                weights = default_weights
            else:
                # 合并权重
                weights = {**default_weights, **weights}
            
            total_score = 0.0
            total_weight = 0.0
            
            # 研究领域匹配度
            if "research_fields" in weights:
                user1_fields = set(user1.get("research_fields", []))
                user2_fields = set(user2.get("research_fields", []))
                if user1_fields and user2_fields:
                    common_fields = user1_fields & user2_fields
                    if common_fields:
                        match_ratio = len(common_fields) / max(len(user1_fields), len(user2_fields))
                        weight = weights["research_fields"]
                        total_score += match_ratio * weight
                        total_weight += weight
            
            # 技能匹配度
            if "skills" in weights:
                user1_skills = set(user1.get("skills", []))
                user2_skills = set(user2.get("skills", []))
                if user1_skills and user2_skills:
                    common_skills = user1_skills & user2_skills
                    if common_skills:
                        match_ratio = len(common_skills) / max(len(user1_skills), len(user2_skills))
                        weight = weights["skills"]
                        total_score += match_ratio * weight
                        total_weight += weight
            
            # 学院匹配度
            if "college" in weights:
                user1_college = user1.get("college", "")
                user2_college = user2.get("college", "")
                if user1_college and user2_college and user1_college == user2_college:
                    weight = weights["college"]
                    total_score += weight
                    total_weight += weight
            
            # 专业匹配度
            if "major" in weights:
                user1_major = user1.get("major", "")
                user2_major = user2.get("major", "")
                if user1_major and user2_major and user1_major == user2_major:
                    weight = weights["major"]
                    total_score += weight
                    total_weight += weight
            
            # 用户类型匹配度
            if "user_type" in weights:
                user1_type = user1.get("user_type", "")
                user2_type = user2.get("user_type", "")
                if user1_type and user2_type and user1_type == user2_type:
                    weight = weights["user_type"]
                    total_score += weight
                    total_weight += weight
            
            # 兴趣爱好匹配度
            if "interests" in weights:
                user1_interests = set(user1.get("interests", []))
                user2_interests = set(user2.get("interests", []))
                if user1_interests and user2_interests:
                    common_interests = user1_interests & user2_interests
                    if common_interests:
                        match_ratio = len(common_interests) / max(len(user1_interests), len(user2_interests))
                        weight = weights["interests"]
                        total_score += match_ratio * weight
                        total_weight += weight
            
            # 归一化分数
            if total_weight > 0:
                return total_score / total_weight
            else:
                return 0.0
                
        except Exception as e:
            logger.error(f"计算字段相似度失败: {str(e)}", exc_info=True)
            return 0.0
    
    def calculate_relationship_similarity(self, user1_id: str, user2_id: str, relationships: List[Dict[str, Any]]) -> float:
        """
        计算关系相似度（基于共同连接）
        
        Args:
            user1_id: 用户1的ID
            user2_id: 用户2的ID
            relationships: 关系列表
            
        Returns:
            相似度分数（0-1之间）
        """
        try:
            # 获取用户1的连接
            user1_connections = set()
            user2_connections = set()
            
            for rel in relationships:
                if rel.get("from_user_id") == user1_id:
                    user1_connections.add(rel.get("to_user_id"))
                elif rel.get("to_user_id") == user1_id:
                    user1_connections.add(rel.get("from_user_id"))
                
                if rel.get("from_user_id") == user2_id:
                    user2_connections.add(rel.get("to_user_id"))
                elif rel.get("to_user_id") == user2_id:
                    user2_connections.add(rel.get("from_user_id"))
            
            # 计算Jaccard相似度
            common_connections = user1_connections & user2_connections
            union_connections = user1_connections | user2_connections
            
            if not union_connections:
                return 0.0
            
            return len(common_connections) / len(union_connections)
            
        except Exception as e:
            logger.error(f"计算关系相似度失败: {str(e)}", exc_info=True)
            return 0.0
    
    def calculate_combined_similarity(
        self,
        user1: Dict[str, Any],
        user2: Dict[str, Any],
        relationships: Optional[List[Dict[str, Any]]] = None,
        weights: Optional[Dict[str, float]] = None
    ) -> float:
        """
        计算综合相似度
        
        Args:
            user1: 用户1的文档
            user2: 用户2的文档
            relationships: 关系列表（可选）
            weights: 各相似度类型的权重
            
        Returns:
            综合相似度分数（0-1之间）
        """
        try:
            # 默认权重
            default_weights = {
                "text": 0.2,
                "field": 0.5,
                "relationship": 0.3
            }
            
            if weights is None:
                weights = default_weights
            else:
                weights = {**default_weights, **weights}
            
            # 计算各种相似度
            text_sim = self.calculate_text_similarity(user1, user2)
            field_sim = self.calculate_field_similarity(user1, user2)
            
            relationship_sim = 0.0
            if relationships and user1.get("user_id") and user2.get("user_id"):
                relationship_sim = self.calculate_relationship_similarity(
                    user1["user_id"],
                    user2["user_id"],
                    relationships
                )
            
            # 加权平均
            total_weight = weights.get("text", 0.2) + weights.get("field", 0.5) + weights.get("relationship", 0.3)
            combined_score = (
                text_sim * weights.get("text", 0.2) +
                field_sim * weights.get("field", 0.5) +
                relationship_sim * weights.get("relationship", 0.3)
            ) / total_weight if total_weight > 0 else 0.0
            
            return combined_score
            
        except Exception as e:
            logger.error(f"计算综合相似度失败: {str(e)}", exc_info=True)
            return 0.0


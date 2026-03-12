"""查询理解服务 - 使用LLM理解用户查询意图并提取结构化搜索条件"""
from typing import Dict, Any, Optional, List
from services.ollama_service import OllamaService
from utils.logger import logger
import json
import re


class QueryUnderstandingService:
    """查询理解服务"""
    
    def __init__(self, model_name: Optional[str] = None, base_url: Optional[str] = None):
        """
        初始化查询理解服务
        
        Args:
            model_name: 使用的模型名称，如果为None则使用默认模型
            base_url: Ollama服务地址
        """
        self.ollama_service = OllamaService(model_name=model_name, base_url=base_url)
        self.prompt_template = """你是一个专业的查询理解助手，负责将用户的自然语言查询转换为结构化的搜索条件。

## 任务
分析用户的查询，提取以下信息：
1. research_fields: 研究领域列表（如：["量子物理", "光学"]）
2. user_type: 用户类型（"student", "teacher", "other" 或 null）
3. skills: 技能列表（如：["Python", "数据分析"]）
4. college: 学院名称（字符串或 null）
5. major: 专业名称（字符串或 null）
6. interests: 兴趣爱好列表（如：["阅读", "运动"]）
7. intent: 查询意图的简短描述（如："找研究量子物理的教师"）

## 重要原则
- 只提取用户明确提到的信息，不要推测或编造
- 如果用户没有提到某个字段，设置为 null 或空列表
- research_fields 和 skills 应该是列表，即使只有一个值
- user_type 必须是 "student", "teacher", "other" 之一，或者 null
- 如果用户提到"教师"、"老师"、"教授"等，user_type 应该是 "teacher"
- 如果用户提到"学生"、"同学"等，user_type 应该是 "student"
- intent 应该简洁地描述用户的查询意图

## 输出格式
必须返回有效的JSON格式，不要包含任何其他文字说明。

## 示例
用户查询："找研究量子物理的教师"
输出：
{{
  "research_fields": ["量子物理"],
  "user_type": "teacher",
  "skills": [],
  "college": null,
  "major": null,
  "interests": [],
  "intent": "找研究量子物理的教师"
}}

用户查询："找会Python的同学"
输出：
{{
  "research_fields": [],
  "user_type": "student",
  "skills": ["Python"],
  "college": null,
  "major": null,
  "interests": [],
  "intent": "找会Python的同学"
}}

用户查询："物理学院的学生"
输出：
{{
  "research_fields": [],
  "user_type": "student",
  "skills": [],
  "college": "物理学院",
  "major": null,
  "interests": [],
  "intent": "找物理学院的学生"
}}

现在分析以下查询：
用户查询："{query}"

请返回JSON格式的结构化条件："""
    
    async def understand_query(self, query: str) -> Dict[str, Any]:
        """
        理解用户查询，提取结构化搜索条件
        
        Args:
            query: 用户的自然语言查询
            
        Returns:
            结构化条件字典，包含：
            - research_fields: List[str] - 研究领域列表
            - user_type: Optional[str] - 用户类型
            - skills: List[str] - 技能列表
            - college: Optional[str] - 学院名称
            - major: Optional[str] - 专业名称
            - interests: List[str] - 兴趣爱好列表
            - intent: str - 查询意图描述
        """
        try:
            # 构建提示词
            prompt = self.prompt_template.format(query=query)
            
            # 调用LLM生成回复
            response_text = ""
            async for chunk in self.ollama_service.generate(
                prompt=prompt,
                stream=False
            ):
                response_text += chunk
            
            # 尝试从回复中提取JSON
            json_match = re.search(r'\{[^{}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                try:
                    result = json.loads(json_str)
                    # 验证和规范化结果
                    return self._normalize_result(result)
                except json.JSONDecodeError as e:
                    logger.warning(f"JSON解析失败: {str(e)}, 原始回复: {response_text[:200]}")
            
            # 如果JSON解析失败，使用简单关键词提取作为fallback
            logger.warning(f"查询理解失败，使用简单关键词提取 - 查询: {query[:50]}")
            return self._simple_keyword_extraction(query)
            
        except Exception as e:
            logger.error(f"查询理解失败: {str(e)}", exc_info=True)
            # 使用简单关键词提取作为fallback
            return self._simple_keyword_extraction(query)
    
    def _normalize_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        规范化查询理解结果
        
        Args:
            result: LLM返回的原始结果
            
        Returns:
            规范化后的结果
        """
        normalized = {
            "research_fields": [],
            "user_type": None,
            "skills": [],
            "college": None,
            "major": None,
            "interests": [],
            "intent": ""
        }
        
        # 处理研究领域
        if "research_fields" in result:
            fields = result["research_fields"]
            if isinstance(fields, list):
                normalized["research_fields"] = [str(f) for f in fields if f]
            elif isinstance(fields, str) and fields:
                normalized["research_fields"] = [fields]
        
        # 处理用户类型
        if "user_type" in result:
            user_type = result["user_type"]
            if user_type in ["student", "teacher", "other"]:
                normalized["user_type"] = user_type
        
        # 处理技能
        if "skills" in result:
            skills = result["skills"]
            if isinstance(skills, list):
                normalized["skills"] = [str(s) for s in skills if s]
            elif isinstance(skills, str) and skills:
                normalized["skills"] = [skills]
        
        # 处理学院
        if "college" in result:
            college = result["college"]
            if college and isinstance(college, str):
                normalized["college"] = college.strip()
        
        # 处理专业
        if "major" in result:
            major = result["major"]
            if major and isinstance(major, str):
                normalized["major"] = major.strip()
        
        # 处理兴趣爱好
        if "interests" in result:
            interests = result["interests"]
            if isinstance(interests, list):
                normalized["interests"] = [str(i) for i in interests if i]
            elif isinstance(interests, str) and interests:
                normalized["interests"] = [interests]
        
        # 处理意图
        if "intent" in result:
            intent = result["intent"]
            if intent and isinstance(intent, str):
                normalized["intent"] = intent.strip()
        
        return normalized
    
    def _simple_keyword_extraction(self, query: str) -> Dict[str, Any]:
        """
        简单的关键词提取（fallback方法）
        
        Args:
            query: 用户查询
            
        Returns:
            简单的结构化条件
        """
        result = {
            "research_fields": [],
            "user_type": None,
            "skills": [],
            "college": None,
            "major": None,
            "interests": [],
            "intent": query[:100]
        }
        
        # 检测用户类型关键词
        teacher_keywords = ["教师", "老师", "教授", "导师", "teacher"]
        student_keywords = ["学生", "同学", "学弟", "学姐", "学长", "student"]
        
        query_lower = query.lower()
        if any(kw in query for kw in teacher_keywords) or "teacher" in query_lower:
            result["user_type"] = "teacher"
        elif any(kw in query for kw in student_keywords) or "student" in query_lower:
            result["user_type"] = "student"
        
        # 检测学院关键词
        college_match = re.search(r'([\u4e00-\u9fa5]+学院)', query)
        if college_match:
            result["college"] = college_match.group(1)
        
        # 检测专业关键词
        major_match = re.search(r'([\u4e00-\u9fa5]+专业)', query)
        if major_match:
            result["major"] = major_match.group(1)
        
        return result


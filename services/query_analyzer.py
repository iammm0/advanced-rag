"""查询分析服务 - 判断是否需要检索上下文"""
from typing import Dict, Any, Optional
from utils.logger import logger
import requests
import os
import json


class QueryAnalyzer:
    """查询分析器 - 判断用户问题是否需要检索知识库"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        # 使用 127.0.0.1 代替 localhost（避免 DNS 解析问题）
        if "host.docker.internal" not in self.ollama_base_url and "localhost" in self.ollama_base_url:
            self.ollama_base_url = self.ollama_base_url.replace("localhost", "127.0.0.1")
        self.session = requests.Session()
        self.session.verify = False
        # 使用小模型进行快速判断
        self.analysis_model = os.getenv("OLLAMA_ANALYSIS_MODEL", "qwen2.5:3b")  # 使用小模型快速判断
    
    def _build_analysis_prompt(self, query: str) -> str:
        """构建分析提示词"""
        return f"""你是一个查询分析助手。请分析以下用户问题，判断是否需要从知识库中检索相关信息来回答。

判断标准：
1. **需要检索**：问题涉及具体的传感器知识、技术细节、文档内容、课程内容等需要从知识库获取的信息
2. **不需要检索**：问题是一般性对话、问候、系统操作询问、数学计算、编程问题等不需要知识库信息的问题

用户问题：{query}

请只回答 JSON 格式：
{{
  "need_retrieval": true/false,
  "reason": "简要说明判断理由"
}}"""
    
    def analyze(self, query: str) -> Dict[str, Any]:
        """
        分析查询，判断是否需要检索上下文
        
        Args:
            query: 用户查询
            
        Returns:
            包含 need_retrieval 和 reason 的字典
        """
        try:
            # 使用小模型快速判断
            prompt = self._build_analysis_prompt(query)
            
            url = f"{self.ollama_base_url}/api/generate"
            request_data = {
                "model": self.analysis_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 低温度，更确定性的判断
                    "num_predict": 100  # 限制输出长度，快速响应
                }
            }
            
            logger.debug(f"查询分析请求 - 查询: {query[:50]}...")
            
            response = self.session.post(
                url,
                json=request_data,
                timeout=10.0  # 10秒超时，快速判断
            )
            response.raise_for_status()
            result = response.json()
            response_text = result.get("response", "").strip()
            
            # 尝试解析 JSON 响应
            try:
                # 提取 JSON 部分（可能包含其他文本）
                import re
                json_match = re.search(r'\{[^{}]*"need_retrieval"[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    analysis_result = json.loads(json_match.group())
                else:
                    # 如果没有找到 JSON，尝试直接解析
                    analysis_result = json.loads(response_text)
                
                need_retrieval = analysis_result.get("need_retrieval", True)  # 默认需要检索（安全策略）
                reason = analysis_result.get("reason", "未提供理由")
                
                logger.info(f"查询分析结果 - 查询: {query[:50]}..., 需要检索: {need_retrieval}, 理由: {reason}")
                
                return {
                    "need_retrieval": bool(need_retrieval),
                    "reason": reason,
                    "confidence": "high"  # 可以后续添加置信度评估
                }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"解析分析结果失败: {response_text}, 错误: {str(e)}")
                # 如果解析失败，使用关键词匹配作为后备方案
                return self._fallback_analysis(query)
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"查询分析请求失败: {str(e)}，使用后备方案")
            return self._fallback_analysis(query)
        except Exception as e:
            logger.error(f"查询分析失败: {str(e)}", exc_info=True)
            return self._fallback_analysis(query)
    
    def _fallback_analysis(self, query: str) -> Dict[str, Any]:
        """
        后备分析方案：基于关键词匹配
        
        如果模型分析失败，使用简单的关键词匹配
        """
        query_lower = query.lower()
        
        # 不需要检索的关键词（问候、系统操作等）
        no_retrieval_keywords = [
            "你好", "hello", "hi", "谢谢", "thanks", "再见", "bye",
            "帮助", "help", "怎么用", "如何使用", "功能", "操作",
            "计算", "算", "等于", "等于多少",
            "代码", "编程", "写程序", "写代码",
            "时间", "现在几点", "日期",
            "天气", "今天天气"
        ]
        
        # 需要检索的关键词（传感器相关）
        need_retrieval_keywords = [
            "传感器", "sensor", "原理", "工作原理", "应用", "分类",
            "电阻", "电容", "电感", "热电", "光电", "磁电",
            "温度", "压力", "位移", "速度", "加速度",
            "文档", "资料", "教材", "课本", "课程",
            "什么是", "如何选择", "如何安装", "如何调试",
            "特点", "特性", "参数", "规格", "选型"
        ]
        
        # 检查是否需要检索
        has_retrieval_keyword = any(keyword in query_lower for keyword in need_retrieval_keywords)
        has_no_retrieval_keyword = any(keyword in query_lower for keyword in no_retrieval_keywords)
        
        # 如果同时包含两种关键词，优先考虑需要检索的关键词
        if has_retrieval_keyword:
            need_retrieval = True
            reason = "问题包含传感器相关知识关键词"
        elif has_no_retrieval_keyword:
            need_retrieval = False
            reason = "问题属于一般性对话或系统操作"
        else:
            # 默认需要检索（安全策略：不确定时倾向于检索）
            need_retrieval = True
            reason = "未匹配到明确关键词，默认需要检索"
        
        logger.info(f"后备分析结果 - 查询: {query[:50]}..., 需要检索: {need_retrieval}, 理由: {reason}")
        
        return {
            "need_retrieval": need_retrieval,
            "reason": reason,
            "confidence": "medium"  # 后备方案的置信度较低
        }


# 全局查询分析器实例
query_analyzer = QueryAnalyzer()


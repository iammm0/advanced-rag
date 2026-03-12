"""模型选择服务 - 根据问题类型智能选择模型"""
from typing import Dict, Any, Optional
from utils.logger import logger
import requests
import os
import json
import re


class ModelSelector:
    """模型选择器 - 判断问题是否需要公式生成"""
    
    def __init__(self):
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://ollama:11434")
        # 使用 127.0.0.1 代替 localhost（避免 DNS 解析问题）
        if "host.docker.internal" not in self.ollama_base_url and "localhost" in self.ollama_base_url:
            self.ollama_base_url = self.ollama_base_url.replace("localhost", "127.0.0.1")
        self.session = requests.Session()
        self.session.verify = False
        # 使用小模型进行快速判断
        self.analysis_model = os.getenv("OLLAMA_ANALYSIS_MODEL", "qwen2.5:3b")
        # 模型配置
        self.formula_model = os.getenv("FORMULA_MODEL", "gemma3:27b")  # 公式相关模型
        self.knowledge_model = os.getenv("KNOWLEDGE_MODEL", "gemma3:1b")  # 知识型模型
    
    def _build_model_selection_prompt(self, query: str) -> str:
        """构建模型选择提示词"""
        return f"""你是一个模型选择助手。请分析以下用户问题，判断回答这个问题时是否需要生成或推导数学/物理公式。

判断标准：
1. **需要公式模型（gemma3）**：问题涉及公式推导、数学计算、物理公式应用、习题解答、公式解释等需要生成或使用公式的内容
2. **需要知识模型（gpt）**：问题涉及概念解释、原理说明、知识问答、应用介绍、分类说明等知识型内容

示例：
- "什么是传感器？" -> 知识模型（概念解释）
- "电阻传感器的公式是什么？" -> 公式模型（需要公式）
- "请推导欧姆定律" -> 公式模型（公式推导）
- "传感器有哪些类型？" -> 知识模型（分类说明）
- "如何计算电阻值？" -> 公式模型（需要计算和公式）
- "传感器的工作原理是什么？" -> 知识模型（原理说明）

用户问题：{query}

请只回答 JSON 格式：
{{
  "need_formula": true/false,
  "model": "gemma3:27b" 或 "gpt-oss:20b",
  "reason": "简要说明判断理由"
}}"""
    
    def select_model(self, query: str) -> Dict[str, Any]:
        """
        根据问题选择模型
        
        Args:
            query: 用户查询
            
        Returns:
            包含 model 和 reason 的字典
        """
        try:
            # 先使用快速关键词匹配
            quick_result = self._quick_keyword_match(query)
            if quick_result.get("confidence") == "high":
                logger.info(f"模型选择（关键词匹配） - 查询: {query[:50]}..., 模型: {quick_result.get('model')}, 理由: {quick_result.get('reason')}")
                return quick_result
            
            # 如果关键词匹配不确定，使用模型判断
            prompt = self._build_model_selection_prompt(query)
            
            url = f"{self.ollama_base_url}/api/generate"
            request_data = {
                "model": self.analysis_model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # 低温度，更确定性的判断
                    "num_predict": 150  # 限制输出长度，快速响应
                }
            }
            
            logger.debug(f"模型选择请求 - 查询: {query[:50]}...")
            
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
                json_match = re.search(r'\{[^{}]*"need_formula"[^{}]*\}', response_text, re.DOTALL)
                if json_match:
                    selection_result = json.loads(json_match.group())
                else:
                    # 如果没有找到 JSON，尝试直接解析
                    selection_result = json.loads(response_text)
                
                need_formula = selection_result.get("need_formula", False)
                model = selection_result.get("model", self.knowledge_model)
                reason = selection_result.get("reason", "未提供理由")
                
                # 验证模型名称
                if "gemma" in model.lower() or need_formula:
                    selected_model = self.formula_model
                else:
                    selected_model = self.knowledge_model
                
                logger.info(f"模型选择结果 - 查询: {query[:50]}..., 模型: {selected_model}, 理由: {reason}")
                
                return {
                    "model": selected_model,
                    "need_formula": need_formula,
                    "reason": reason,
                    "confidence": "high"
                }
            except (json.JSONDecodeError, KeyError) as e:
                logger.warning(f"解析模型选择结果失败: {response_text}, 错误: {str(e)}")
                # 如果解析失败，使用关键词匹配作为后备方案
                return self._quick_keyword_match(query)
                
        except requests.exceptions.RequestException as e:
            logger.warning(f"模型选择请求失败: {str(e)}，使用关键词匹配")
            return self._quick_keyword_match(query)
        except Exception as e:
            logger.error(f"模型选择失败: {str(e)}", exc_info=True)
            return self._quick_keyword_match(query)
    
    def _quick_keyword_match(self, query: str) -> Dict[str, Any]:
        """
        快速关键词匹配（后备方案）
        
        如果模型分析失败，使用简单的关键词匹配
        """
        query_lower = query.lower()
        
        # 需要公式模型的关键词
        formula_keywords = [
            "公式", "推导", "计算", "求解", "证明", "验证",
            "等于", "等于多少", "怎么算", "如何计算",
            "习题", "题目", "解答", "解题", "步骤",
            "数学", "物理公式", "定律公式", "表达式",
            "积分", "微分", "导数", "极限", "级数",
            "方程", "方程组", "不等式", "函数",
            "电阻", "电容", "电感", "电压", "电流", "功率",
            "f=", "v=", "a=", "e=", "p=",  # 常见物理量符号
        ]
        
        # 知识型关键词（如果明确是知识型问题，优先使用知识模型）
        knowledge_keywords = [
            "什么是", "定义", "概念", "原理", "工作原理",
            "类型", "分类", "种类", "有哪些",
            "应用", "用途", "作用", "功能",
            "特点", "特性", "优势", "缺点",
            "介绍", "说明", "解释", "阐述",
            "如何选择", "如何安装", "如何调试", "如何使用",
            "区别", "对比", "比较", "差异",
        ]
        
        # 检查关键词
        has_formula_keyword = any(keyword in query_lower for keyword in formula_keywords)
        has_knowledge_keyword = any(keyword in query_lower for keyword in knowledge_keywords)
        
        # 判断逻辑
        if has_formula_keyword and not has_knowledge_keyword:
            # 明确需要公式
            return {
                "model": self.formula_model,
                "need_formula": True,
                "reason": "问题包含公式相关关键词",
                "confidence": "high"
            }
        elif has_knowledge_keyword and not has_formula_keyword:
            # 明确是知识型问题
            return {
                "model": self.knowledge_model,
                "need_formula": False,
                "reason": "问题属于知识型问答",
                "confidence": "high"
            }
        elif has_formula_keyword and has_knowledge_keyword:
            # 同时包含两种关键词，优先考虑公式（因为公式问题通常也需要知识背景）
            return {
                "model": self.formula_model,
                "need_formula": True,
                "reason": "问题同时包含公式和知识关键词，优先使用公式模型",
                "confidence": "medium"
            }
        else:
            # 默认使用知识模型（安全策略：不确定时倾向于知识型回答）
            return {
                "model": self.knowledge_model,
                "need_formula": False,
                "reason": "未匹配到明确关键词，默认使用知识模型",
                "confidence": "low"
            }


# 全局模型选择器实例
model_selector = ModelSelector()


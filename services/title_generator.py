"""对话标题和快捷提示词生成服务"""
import requests
import os
import json
from typing import Optional, List
from utils.logger import logger


class TitleGenerator:
    """使用小模型生成对话标题和快捷提示词"""
    
    def __init__(self, base_url: Optional[str] = None, model_name: str = "qwen2.5:3b"):
        """
        初始化标题生成器
        
        Args:
            base_url: Ollama服务地址，默认 http://localhost:11434
            model_name: 模型名称，默认 qwen2.5:3b
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # 使用 127.0.0.1 代替 localhost（避免 DNS 解析问题）
        if "host.docker.internal" not in self.base_url and "localhost" in self.base_url:
            self.base_url = self.base_url.replace("localhost", "127.0.0.1")
        self.model_name = model_name
        self.session = requests.Session()
        self.session.verify = False
        self.timeout = 30.0  # 30秒超时，小模型应该很快
        logger.info(f"标题生成器初始化 - 地址: {self.base_url}, 模型: {self.model_name}")
    
    def generate_conversation_title(self, messages: List[dict]) -> str:
        """
        根据对话消息生成对话标题
        
        Args:
            messages: 对话消息列表，每个消息包含 role 和 content
        
        Returns:
            生成的标题，如果失败则返回默认标题
        """
        try:
            # 提取前几条消息作为上下文（最多3轮对话）
            context_messages = []
            user_count = 0
            for msg in messages:
                role = msg.get("role", "")
                content = msg.get("content", "").strip()
                if role in ["user", "assistant"] and content:
                    context_messages.append(f"{'用户' if role == 'user' else '助手'}: {content}")
                    if role == "user":
                        user_count += 1
                        if user_count >= 3:  # 最多取前3个用户消息
                            break
            
            if not context_messages:
                return "新对话"
            
            # 构建提示词
            context_text = "\n".join(context_messages)
            prompt = f"""请根据以下对话内容，生成一个简洁的标题（不超过20个字，不要包含标点符号）：

{context_text}

请只返回标题，不要包含其他内容。"""
            
            # 调用Ollama生成标题
            url = f"{self.base_url}/api/generate"
            request_data = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # 较低温度，更确定性的输出
                    "num_predict": 30  # 限制输出长度
                }
            }
            
            response = self.session.post(url, json=request_data, timeout=self.timeout)
            response.raise_for_status()
            result = response.json()
            title = result.get("response", "").strip()
            
            # 清理标题：移除可能的引号、标点符号等
            title = title.strip('"').strip("'").strip("。").strip(".").strip()
            
            # 限制长度
            if len(title) > 30:
                title = title[:30]
            
            # 如果生成失败或为空，使用默认标题
            if not title or len(title) < 2:
                # 尝试从第一个用户消息提取标题
                first_user_msg = None
                for msg in messages:
                    if msg.get("role") == "user":
                        first_user_msg = msg.get("content", "").strip()
                        break
                
                if first_user_msg:
                    title = first_user_msg[:30] + ("..." if len(first_user_msg) > 30 else "")
                else:
                    title = "新对话"
            
            logger.info(f"生成对话标题成功: {title}")
            return title
            
        except Exception as e:
            logger.warning(f"生成对话标题失败: {str(e)}，使用默认标题")
            # 如果生成失败，尝试从第一个用户消息提取
            try:
                for msg in messages:
                    if msg.get("role") == "user":
                        first_msg = msg.get("content", "").strip()
                        if first_msg:
                            return first_msg[:30] + ("..." if len(first_msg) > 30 else "")
            except:
                pass
            return "新对话"
    

# 全局实例
title_generator = TitleGenerator()


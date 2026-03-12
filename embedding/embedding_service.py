"""向量化服务"""
from typing import List, Optional, Dict, Any
import os
import requests
from utils.logger import logger


class EmbeddingService:
    """文本向量化服务 - 使用 Ollama"""
    
    def __init__(
        self,
        model_name: Optional[str] = None
    ):
        """
        初始化向量化服务
        
        Args:
            model_name: Ollama 模型名称
        """
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
        # 使用 127.0.0.1 代替 localhost（避免 DNS 解析问题）
        # 保留容器名称（如 ollama）和 host.docker.internal（用于从容器访问宿主机服务）
        if "host.docker.internal" not in self.ollama_base_url and "localhost" in self.ollama_base_url:
            self.ollama_base_url = self.ollama_base_url.replace("localhost", "127.0.0.1")
        self.session = requests.Session()
        self.session.verify = False
        
        # 使用 Ollama 模型
        self.ollama_model = model_name or os.getenv("OLLAMA_EMBEDDING_MODEL", None)
        
        if self.ollama_model:
            # 如果配置了 Ollama 模型，尝试匹配实际模型名称（处理标签问题）
            self.ollama_model = self._normalize_model_name(self.ollama_model)
        else:
            # 尝试自动检测可用的 Ollama embedding 模型
            self.ollama_model = self._detect_ollama_embedding_model()
        
        if not self.ollama_model:
            raise Exception("未找到可用的 Ollama embedding 模型，请设置 OLLAMA_EMBEDDING_MODEL 环境变量或安装 embedding 模型")
        
        self.model_name = self.ollama_model
        self.vector_size = None  # 将在首次调用时获取
        logger.info(f"使用 Ollama 嵌入服务 - 地址: {self.ollama_base_url}, 模型: {self.ollama_model}")
    
    def _normalize_model_name(self, model_name: str) -> str:
        """
        规范化模型名称，处理标签问题
        
        如果环境变量是 nomic-embed-text，但实际模型是 nomic-embed-text:latest，
        需要匹配到实际的模型名称
        
        Args:
            model_name: 模型名称（可能不带标签）
        
        Returns:
            规范化后的模型名称（匹配实际存在的模型）
        """
        if not model_name:
            return model_name
        
        try:
            # 获取 Ollama 模型列表
            response = self.session.get(
                f"{self.ollama_base_url}/api/tags",
                timeout=5.0
            )
            response.raise_for_status()
            result = response.json()
            models = result.get("models", [])
            
            # 如果模型名称已经包含标签，直接返回
            if ":" in model_name:
                # 检查是否存在完全匹配的模型
                for model_info in models:
                    if model_info.get("name") == model_name:
                        return model_name
                # 如果不存在，返回原名称（让 Ollama 处理）
                return model_name
            
            # 如果模型名称不包含标签，尝试匹配
            # 1. 先尝试精确匹配（不带标签）
            for model_info in models:
                actual_name = model_info.get("name", "")
                # 移除标签进行比较
                base_name = actual_name.split(":")[0]
                if base_name == model_name:
                    # 返回完整的模型名称（包括标签）
                    logger.info(f"模型名称规范化: {model_name} -> {actual_name}")
                    return actual_name
            
            # 2. 如果没找到，尝试添加 :latest 标签
            model_with_latest = f"{model_name}:latest"
            for model_info in models:
                if model_info.get("name") == model_with_latest:
                    logger.info(f"模型名称规范化: {model_name} -> {model_with_latest}")
                    return model_with_latest
            
            # 3. 如果还是没找到，返回原名称（让 Ollama 处理，可能会自动添加 :latest）
            logger.warning(f"未找到匹配的模型: {model_name}，将使用原名称")
            return model_name
            
        except Exception as e:
            logger.debug(f"规范化模型名称时出错: {e}，使用原名称: {model_name}")
            return model_name
    
    def _detect_ollama_embedding_model(self) -> Optional[str]:
        """
        自动检测可用的 Ollama embedding 模型
        
        Returns:
            模型名称，如果未找到则返回 None
        """
        try:
            # 获取 Ollama 模型列表
            response = self.session.get(
                f"{self.ollama_base_url}/api/tags",
                timeout=5.0
            )
            response.raise_for_status()
            result = response.json()
            models = result.get("models", [])
            
            # 常见的 embedding 模型名称（按优先级排序）
            embedding_model_keywords = [
                "embedding",
                "nomic-embed",
                "all-minilm",
                "bge",
                "multilingual",
                "embed"
            ]
            
            # 查找 embedding 模型
            for model_info in models:
                model_name = model_info.get("name", "")
                # 检查模型名称是否包含 embedding 关键词
                for keyword in embedding_model_keywords:
                    if keyword.lower() in model_name.lower():
                        logger.info(f"自动检测到 Ollama embedding 模型: {model_name}")
                        return model_name
            
            # 如果没有找到专门的 embedding 模型，尝试使用第一个可用模型
            if models:
                first_model = models[0].get("name", "")
                logger.warning(f"未找到专门的 embedding 模型，尝试使用: {first_model}")
                return first_model
            
            logger.info("未找到可用的 Ollama embedding 模型")
            return None
            
        except Exception as e:
            logger.debug(f"无法连接到 Ollama 服务进行模型检测: {e}")
            return None
    
    def list_available_ollama_models(self) -> List[Dict[str, Any]]:
        """
        列出所有可用的 Ollama 模型
        
        Returns:
            模型列表
        """
        try:
            response = self.session.get(
                f"{self.ollama_base_url}/api/tags",
                timeout=5.0
            )
            response.raise_for_status()
            result = response.json()
            return result.get("models", [])
        except Exception as e:
            logger.error(f"获取 Ollama 模型列表失败: {e}")
            return []
    
    def _get_ollama_embedding(self, text: str, retry_count: int = 3) -> List[float]:
        """使用 Ollama API 获取单个文本的嵌入向量"""
        import time
        last_exception = None
        
        for attempt in range(retry_count):
            try:
                response = self.session.post(
                    f"{self.ollama_base_url}/api/embeddings",
                    json={
                        "model": self.ollama_model,
                        "prompt": text
                    },
                    timeout=120.0  # 增加超时时间到120秒
                )
                response.raise_for_status()
                result = response.json()
                embedding = result.get("embedding", [])
                
                if not embedding:
                    raise Exception(f"Ollama 返回的嵌入向量为空，模型可能不支持 embedding: {self.ollama_model}")
                
                # 首次调用时设置向量维度
                if self.vector_size is None:
                    self.vector_size = len(embedding)
                    logger.info(f"Ollama 嵌入向量维度: {self.vector_size}")
                
                return embedding
            except requests.exceptions.Timeout as e:
                last_exception = e
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 2  # 递增等待时间：2秒、4秒、6秒
                    logger.warning(f"Ollama 嵌入请求超时（尝试 {attempt + 1}/{retry_count}），{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Ollama 嵌入请求超时，已重试 {retry_count} 次")
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                if attempt < retry_count - 1:
                    wait_time = (attempt + 1) * 2
                    logger.warning(f"Ollama 嵌入请求连接错误（尝试 {attempt + 1}/{retry_count}），{wait_time}秒后重试...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Ollama 嵌入请求连接错误，已重试 {retry_count} 次")
            except requests.exceptions.RequestException as e:
                error_msg = str(e)
                if "model not found" in error_msg.lower():
                    logger.error(f"Ollama 模型未找到: {self.ollama_model}，请使用 'ollama pull {self.ollama_model}' 下载模型")
                raise Exception(f"Ollama 嵌入请求失败: {e}")
        
        # 所有重试都失败
        raise Exception(f"Ollama 嵌入请求失败（已重试 {retry_count} 次）: {last_exception}")
    
    def encode(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """
        将文本列表编码为向量
        
        Args:
            texts: 文本列表
            batch_size: 批处理大小（保留参数以保持兼容性，但 Ollama 不使用）
        
        Returns:
            向量列表
        """
        if not texts:
            return []
        
        # 使用 Ollama API
        embeddings = []
        for text in texts:
            embedding = self._get_ollama_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def encode_single(self, text: str) -> List[float]:
        """编码单个文本"""
        return self.encode([text])[0]
    
    @property
    def dimension(self) -> int:
        """获取向量维度"""
        # 如果还没有获取过维度，先调用一次获取
        if self.vector_size is None:
            test_embedding = self._get_ollama_embedding("test")
            self.vector_size = len(test_embedding)
        return self.vector_size


# 全局向量化服务实例
embedding_service = EmbeddingService()


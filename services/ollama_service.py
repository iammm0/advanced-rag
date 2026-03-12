"""Ollama模型调用服务"""
import requests
import os
import json
from typing import AsyncGenerator, Optional, Dict, Any, List
from utils.logger import logger


class OllamaService:
    """Ollama服务封装"""
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        model_name: Optional[str] = None
    ):
        """
        初始化Ollama服务
        
        Args:
            base_url: Ollama服务地址，默认 http://localhost:11434
            model_name: 模型名称，默认从环境变量获取
        """
        self.base_url = base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        # 使用 127.0.0.1 代替 localhost（避免 DNS 解析问题）
        # 保留容器名称（如 ollama）和 host.docker.internal（用于从容器访问宿主机服务）
        if "host.docker.internal" not in self.base_url and "localhost" in self.base_url:
            self.base_url = self.base_url.replace("localhost", "127.0.0.1")
        self.model_name = model_name or os.getenv("OLLAMA_MODEL", "gemma3:1b")
        self.session = requests.Session()
        self.session.verify = False
        # 增加超时时间到600秒（10分钟），大模型生成回复可能需要较长时间
        self.timeout = float(os.getenv("OLLAMA_TIMEOUT", "600.0"))
        logger.info(f"Ollama服务初始化 - 地址: {self.base_url}, 模型: {self.model_name}, 超时: {self.timeout}秒")
    
    async def generate(
        self,
        prompt: str,
        context: Optional[str] = None,
        stream: bool = False,
        document_id: Optional[str] = None,
        document_info: Optional[Dict[str, Any]] = None,
        knowledge_base_status: Optional[Dict[str, Any]] = None,
        assistant_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> AsyncGenerator[str, None]:
        """
        生成回复（流式或非流式）
        
        Args:
            prompt: 用户提示
            context: 上下文信息（RAG检索到的内容）
            stream: 是否流式输出
            document_id: 文档ID（可选）
            document_info: 文档详细信息（可选）
            knowledge_base_status: 知识库状态信息（可选）
            assistant_id: 助手ID（可选，用于获取系统提示词）
        
        Yields:
            生成的文本片段
        """
        # 构建完整的提示
        full_prompt = await self._build_prompt(
            prompt, 
            context,
            document_id=document_id,
            document_info=document_info,
            knowledge_base_status=knowledge_base_status,
            assistant_id=assistant_id,
            conversation_history=conversation_history
        )
        
        if stream:
            async for chunk in self._generate_stream(full_prompt):
                yield chunk
        else:
            response = await self._generate_once(full_prompt)
            yield response
    
    async def _build_prompt(
        self, 
        prompt: str, 
        context: Optional[str] = None,
        document_id: Optional[str] = None,
        document_info: Optional[Dict[str, Any]] = None,
        knowledge_base_status: Optional[Dict[str, Any]] = None,
        assistant_id: Optional[str] = None,
        conversation_history: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """构建完整的提示（使用提示词链机制）"""
        # 从数据库获取助手特定提示词（如果提供了assistant_id）
        assistant_prompt = None
        if assistant_id:
            try:
                from database.mongodb import mongodb
                collection = mongodb.get_collection("course_assistants")
                assistant_doc = await collection.find_one({"_id": assistant_id})
                if assistant_doc:
                    assistant_prompt = assistant_doc.get("system_prompt")
            except Exception as e:
                logger.warning(f"获取助手系统提示词失败: {str(e)}")
        
        # 使用提示词链服务构建完整的系统提示词
        # 基础提示词（通用物理课程AI助手）+ 助手特定提示词（扩展和细化）
        from services.prompt_chain import prompt_chain
        system_instruction = await prompt_chain.build_prompt_chain(
            base_prompt=None,  # 从数据库或默认值获取基础提示词
            assistant_prompt=assistant_prompt  # 助手特定的提示词
        )
        
        # 如果提示词链构建失败，使用基础提示词（向后兼容）
        if not system_instruction:
            # 直接使用基础提示词
            from services.prompt_chain import prompt_chain
            system_instruction = await prompt_chain.get_base_prompt()

        # 构建知识库状态信息
        kb_status_text = ""
        if knowledge_base_status:
            total_docs = knowledge_base_status.get("total", 0)
            completed_docs = knowledge_base_status.get("completed", 0)
            processing_docs = knowledge_base_status.get("processing", 0)
            failed_docs = knowledge_base_status.get("failed", 0)
            
            kb_status_text = f"""
知识库当前状态：
- 文档总数：{total_docs}
- 已处理完成：{completed_docs}
- 处理中：{processing_docs}
- 处理失败：{failed_docs}"""
            
            # 添加模型信息
            import os
            from embedding.embedding_service import embedding_service
            generation_model = os.getenv("OLLAMA_MODEL", "gemma3:1b")
            embedding_model = embedding_service.model_name if hasattr(embedding_service, 'model_name') else "未知"
            kb_status_text += f"""
- 生成模型：{generation_model}
- 向量化模型：{embedding_model}"""
            
            # 如果有文档列表，添加文档名称（按创建时间排序，最新的在前）
            doc_list = knowledge_base_status.get("documents", [])
            if doc_list:
                # 按创建时间排序（最新的在前）
                sorted_docs = sorted(doc_list, key=lambda x: x.get("created_at", ""), reverse=True)
                kb_status_text += "\n- 文档列表（按时间排序，最新的在前）："
                for doc in sorted_docs[:10]:  # 最多显示10个文档
                    doc_title = doc.get("title", "未命名文档")
                    doc_status = doc.get("status", "unknown")
                    created_at = doc.get("created_at", "")
                    kb_status_text += f"\n  • {doc_title} ({doc_status})"
                    if created_at:
                        kb_status_text += f" - {created_at}"
                if len(sorted_docs) > 10:
                    kb_status_text += f"\n  ... 还有 {len(sorted_docs) - 10} 个文档"

        # 构建文档信息
        doc_info_text = ""
        if document_info:
            doc_title = document_info.get("title") or f"文档_{document_info.get('document_id', 'unknown')[:8]}"
            doc_status = document_info.get("status", "unknown")
            doc_type = document_info.get("file_type", "unknown")
            total_chunks = document_info.get("total_chunks", 0)
            total_vectors = document_info.get("total_vectors", 0)
            created_at = document_info.get("created_at", "")
            metadata = document_info.get("metadata", {})
            author = metadata.get("author", "") if metadata else ""
            
            doc_info_text = f"""
当前查询的文档信息：
- 文档标题：{doc_title}
- 文档类型：{doc_type}
- 处理状态：{doc_status}
- 文本块数量：{total_chunks}
- 向量数量：{total_vectors}"""
            
            if author:
                doc_info_text += f"\n- 作者：{author}"
            if created_at:
                doc_info_text += f"\n- 创建时间：{created_at}"
        
        # 构建完整提示
        prompt_parts = [system_instruction]
        
        if kb_status_text:
            prompt_parts.append(kb_status_text)
        
        if doc_info_text:
            prompt_parts.append(doc_info_text)
        
        if context:
            prompt_parts.append(f"""
上下文信息（来自RAG检索）：
{context}""")
        
        # 添加对话历史上下文（保留最近10轮对话，避免提示词过长）
        if conversation_history and len(conversation_history) > 0:
            # 只保留最近的对话历史（最近20条消息，即10轮对话）
            recent_history = conversation_history[-20:] if len(conversation_history) > 20 else conversation_history
            
            history_text = "\n\n## 对话历史\n\n"
            history_text += "以下是本次对话的历史记录，请参考这些信息来理解用户的意图和上下文：\n\n"
            
            for i, msg in enumerate(recent_history):
                role = msg.get("role", "unknown")
                content = msg.get("content", "").strip()
                if not content:
                    continue
                    
                if role == "user":
                    history_text += f"**用户**：{content}\n\n"
                elif role == "assistant":
                    history_text += f"**助手**：{content}\n\n"
            
            history_text += "---\n\n"
            history_text += "**重要提示**：请根据上述对话历史理解用户的意图和上下文，确保你的回答与之前的对话内容连贯一致。如果用户的问题与之前的对话相关，请结合对话历史来回答。\n\n"
            
            prompt_parts.append(history_text)
        
        # 处理引用内容
        quoted_content = None
        user_question = prompt
        if "[引用内容]" in prompt and "[/引用内容]" in prompt:
            import re
            match = re.search(r'\[引用内容\](.*?)\[/引用内容\]', prompt, re.DOTALL)
            if match:
                quoted_content = match.group(1).strip()
                # 提取用户问题（引用内容之后的部分）
                user_question = prompt.split("[/引用内容]")[-1].strip()
                if not user_question:
                    user_question = "请针对引用的内容进行回答或解释。"
        
        if quoted_content:
            prompt_parts.append(f"""
用户引用的内容：
{quoted_content}

用户问题：{user_question}

请特别注意：用户引用了上述内容，请基于引用的内容来回答用户的问题。如果引用的内容与上下文信息或知识库内容相关，请结合这些信息进行回答。""")
        else:
            prompt_parts.append(f"""
用户问题：{user_question}

请根据上述限制、上下文信息、对话历史和知识库状态回答：""")
        
        full_prompt = "\n".join(prompt_parts)
        
        # 检查并执行工具函数调用（传递assistant_id以便工具函数使用）
        full_prompt = await self._process_tool_calls(full_prompt, assistant_id=assistant_id)
        
        return full_prompt
    
    def _format_tools_description(self, tools_schema: List[Dict[str, Any]]) -> str:
        """
        格式化工具函数描述，用于添加到系统提示词中
        
        Args:
            tools_schema: 工具函数列表
        
        Returns:
            格式化的工具描述文本
        """
        if not tools_schema:
            return "当前没有可用的工具函数。"
        
        description = """你可以调用以下工具函数来获取系统信息：

**重要提示**：当用户询问以下问题时，你必须调用相应的工具函数来获取实时信息，而不是使用记忆中的信息：
- 知识库现在有什么文档、知识库情况、知识库状态、知识库信息
- 用了什么模型、当前使用的模型、推理模型、向量化模型
- 系统配置、系统信息、当前配置

工具函数列表：

"""
        
        for tool in tools_schema:
            name = tool.get("name", "")
            desc = tool.get("description", "")
            params = tool.get("parameters", {}).get("properties", {})
            
            description += f"**{name}**: {desc}\n"
            
            if params:
                description += "  参数：\n"
                for param_name, param_info in params.items():
                    param_type = param_info.get("type", "string")
                    param_desc = param_info.get("description", "")
                    default = param_info.get("default", "")
                    if default:
                        description += f"    - {param_name} ({param_type}): {param_desc} [默认: {default}]\n"
                    else:
                        description += f"    - {param_name} ({param_type}): {param_desc}\n"
            description += "\n"
        
        # 获取第一个工具函数名称作为示例
        example_tool_name = tools_schema[0].get("name", "get_system_info") if tools_schema else "get_system_info"
        
        description += f"""
**调用格式**：
使用以下XML格式调用工具函数（注意：name属性必须是实际的工具函数名称，如 {example_tool_name}）：

示例1：调用无参数的工具函数
<function_calls>
<invoke name="{example_tool_name}">
</invoke>
</function_calls>

示例2：调用带参数的工具函数
<function_calls>
<invoke name="get_knowledge_base_documents">
<parameter name="limit">10</parameter>
</invoke>
</function_calls>

**重要**：name属性的值必须是上面列出的实际工具函数名称之一，不能使用占位符或示例文本。

调用后，工具函数的结果会自动添加到你的上下文中，请基于这些实时数据回答用户的问题。
"""
        
        return description
    
    async def _process_tool_calls(self, prompt: str, assistant_id: Optional[str] = None) -> str:
        """
        处理提示词中的工具函数调用
        
        Args:
            prompt: 原始提示词
            assistant_id: 助手ID（可选），会自动传递给支持该参数的工具函数
        
        Returns:
            处理后的提示词（包含工具函数调用结果）
        """
        import re
        from services.ai_tools import ai_tools
        
        # 查找所有工具函数调用
        pattern = r'<function_calls>\s*<invoke\s+name="([^"]+)">\s*(.*?)\s*</invoke>\s*</function_calls>'
        matches = re.finditer(pattern, prompt, re.DOTALL)
        
        tool_results = []
        
        for match in matches:
            tool_name = match.group(1).strip()
            params_text = match.group(2)
            
            # 验证工具函数名称（防止AI使用占位符）
            if not tool_name or tool_name in ["工具函数名称", "function_name", "tool_name", "函数名称"]:
                logger.warning(f"检测到占位符工具函数名称: '{tool_name}'，跳过调用")
                tool_results.append({
                    "tool": tool_name,
                    "result": {
                        "success": False,
                        "error": f"工具函数名称不能是占位符，请使用实际的工具函数名称（如 get_system_info、get_knowledge_base_documents 等）"
                    }
                })
                continue
            
            # 检查工具函数是否存在
            if tool_name not in ai_tools.functions:
                available_tools = ", ".join(list(ai_tools.functions.keys())[:5])
                logger.warning(f"未知的工具函数: '{tool_name}'，可用工具: {available_tools}...")
                tool_results.append({
                    "tool": tool_name,
                    "result": {
                        "success": False,
                        "error": f"未知的工具函数 '{tool_name}'。可用的工具函数包括: {available_tools} 等。请检查工具函数名称是否正确。"
                    }
                })
                continue
            
            # 解析参数
            params = {}
            param_pattern = r'<parameter\s+name="([^"]+)">([^<]+)</parameter>'
            param_matches = re.finditer(param_pattern, params_text)
            
            for param_match in param_matches:
                param_name = param_match.group(1)
                param_value = param_match.group(2).strip()
                
                # 尝试转换参数类型
                try:
                    # 尝试转换为整数
                    if param_value.isdigit():
                        params[param_name] = int(param_value)
                    # 尝试转换为浮点数
                    elif '.' in param_value and param_value.replace('.', '').isdigit():
                        params[param_name] = float(param_value)
                    # 尝试转换为布尔值
                    elif param_value.lower() in ['true', 'false']:
                        params[param_name] = param_value.lower() == 'true'
                    else:
                        params[param_name] = param_value
                except:
                    params[param_name] = param_value
            
            # 如果工具函数支持assistant_id参数且用户没有提供，自动注入
            tool_schema = ai_tools.tools.get(tool_name, {})
            tool_params = tool_schema.get("parameters", {}).get("properties", {})
            if "assistant_id" in tool_params and "assistant_id" not in params and assistant_id:
                params["assistant_id"] = assistant_id
                logger.debug(f"自动注入assistant_id到工具函数 {tool_name}: {assistant_id}")
            
            # 调用工具函数
            try:
                result = ai_tools.call_tool(tool_name, params if params else None)
                tool_results.append({
                    "tool": tool_name,
                    "result": result
                })
                logger.info(f"成功调用工具函数: {tool_name}, 参数: {params}")
            except Exception as e:
                logger.error(f"调用工具函数 {tool_name} 失败: {str(e)}", exc_info=True)
                tool_results.append({
                    "tool": tool_name,
                    "result": {"success": False, "error": str(e)}
                })
        
        # 如果有工具函数调用结果，添加到提示词末尾
        if tool_results:
            results_text = "\n\n工具函数调用结果：\n"
            for tool_result in tool_results:
                tool_name = tool_result["tool"]
                result = tool_result["result"]
                results_text += f"\n调用 {tool_name} 的结果：\n{json.dumps(result, ensure_ascii=False, indent=2)}\n"
            
            prompt += results_text
        
        return prompt
    
    async def _generate_stream(self, prompt: str) -> AsyncGenerator[str, None]:
        """流式生成"""
        try:
            logger.debug(f"开始流式生成 - 模型: {self.model_name}, 提示长度: {len(prompt)}")
            # 使用队列在线程和异步代码之间传递数据
            import asyncio
            from queue import Queue, Empty
            import threading
            
            queue = Queue()
            exception_holder = [None]
            finished_event = threading.Event()
            
            def _sync_stream():
                """在线程中执行同步流式请求"""
                import time
                response = None
                try:
                    url = f"{self.base_url}/api/generate"
                    request_data = {
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": True
                    }
                    logger.info(f"发送流式请求到 Ollama - URL: {url}, 模型: {self.model_name}, 提示长度: {len(prompt)}")
                    logger.debug(f"请求数据: {request_data}")
                    
                    response = self.session.post(
                        url,
                        json=request_data,
                        timeout=self.timeout,
                        stream=True
                    )
                    
                    logger.debug(f"Ollama 响应状态码: {response.status_code}")
                    response.raise_for_status()
                    logger.info("✓ Ollama 流式请求成功，开始接收数据")
                    
                    line_count = 0
                    last_data_time = time.time()
                    request_start_time = time.time()
                    max_idle_time = 120.0  # 最大空闲时间120秒（大模型可能需要更长时间生成）
                    max_total_time = self.timeout  # 总超时时间
                    
                    # 同步迭代流式响应
                    # 使用 decode_unicode=True 直接获取字符串，避免编码问题
                    for line in response.iter_lines(decode_unicode=True, chunk_size=8192):
                        current_time = time.time()
                        total_elapsed = current_time - request_start_time
                        
                        # 检查总超时时间
                        if total_elapsed > max_total_time:
                            logger.warning(f"流式请求总时间超时（{total_elapsed:.1f}秒 > {max_total_time}秒）")
                            break
                        
                        if line:  # 跳过空行
                            line_count += 1
                            last_data_time = current_time
                            queue.put(line)
                            if line_count <= 3:  # 记录前3行的内容
                                logger.debug(f"收到数据行 {line_count}: {line[:100]}...")
                            elif line_count % 50 == 0:  # 每50行记录一次（减少日志）
                                logger.debug(f"已收到 {line_count} 行数据，耗时 {total_elapsed:.1f}秒...")
                        else:
                            # 空行，检查是否空闲超时
                            idle_time = current_time - last_data_time
                            if idle_time > max_idle_time:
                                logger.warning(f"流式响应空闲超时（{idle_time:.1f}秒 > {max_idle_time}秒），可能连接已断开")
                                break
                    
                    logger.info(f"Ollama 流式响应完成 - 共收到 {line_count} 行数据")
                    finished_event.set()
                    queue.put(None)  # 结束标记
                except requests.exceptions.Timeout as e:
                    logger.error(f"Ollama 流式请求超时: {str(e)}")
                    exception_holder[0] = Exception(f"流式请求超时: {str(e)}")
                    finished_event.set()
                    queue.put(None)
                except requests.exceptions.ConnectionError as e:
                    logger.error(f"Ollama 流式请求连接错误: {str(e)}")
                    exception_holder[0] = Exception(f"流式请求连接错误: {str(e)}")
                    finished_event.set()
                    queue.put(None)
                except Exception as e:
                    logger.error(f"Ollama 流式请求失败: {str(e)}", exc_info=True)
                    exception_holder[0] = e
                    finished_event.set()
                    queue.put(None)  # 确保结束
                finally:
                    # 确保响应对象被关闭
                    if response is not None:
                        try:
                            response.close()
                        except:
                            pass
            
            # 在线程池中启动流式请求
            loop = asyncio.get_event_loop()
            logger.debug("在线程池中启动流式请求...")
            executor_task = loop.run_in_executor(None, _sync_stream)
            
            # 异步消费队列中的数据
            chunk_count = 0
            empty_count = 0
            max_empty_count = 10000  # 最多等待10000次（约1秒）
            
            while True:
                # 检查是否有异常
                if exception_holder[0]:
                    logger.error(f"流式生成过程中发生异常: {exception_holder[0]}")
                    raise exception_holder[0]
                
                # 尝试从队列获取数据（非阻塞）
                try:
                    line = queue.get_nowait()
                    empty_count = 0  # 重置空计数
                    
                    if line is None:  # 结束标记
                        logger.info(f"流式生成完成 - 共生成 {chunk_count} 个文本块")
                        break
                    
                    try:
                        data = json.loads(line)
                        logger.debug(f"解析JSON成功: {list(data.keys())}")
                        
                        if "response" in data:
                            chunk_count += 1
                            response_text = data["response"]
                            logger.debug(f"生成文本块 {chunk_count}: {response_text[:50]}...")
                            yield response_text
                        
                        if data.get("done", False):
                            logger.info(f"Ollama 标记完成 - 共生成 {chunk_count} 个文本块")
                            break
                    except json.JSONDecodeError as e:
                        logger.warning(f"解析JSON失败: {line[:100]}..., 错误: {str(e)}")
                        continue
                except Empty:
                    empty_count += 1
                    # 队列为空，检查是否已完成
                    if finished_event.is_set():
                        # 再尝试一次获取，可能还有数据
                        try:
                            line = queue.get_nowait()
                            if line is None:
                                break
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    chunk_count += 1
                                    yield data["response"]
                                if data.get("done", False):
                                    break
                            except json.JSONDecodeError:
                                pass
                        except Empty:
                            logger.debug("队列已空且已完成，退出循环")
                            break
                    else:
                        # 等待一小段时间后重试
                        if empty_count % 1000 == 0:  # 每1000次记录一次
                            logger.debug(f"等待数据中... (已等待 {empty_count} 次)")
                        # 使用更短的等待时间，让流式输出更及时
                        await asyncio.sleep(0.001)  # 等待1ms（增加等待时间，减少CPU占用）
                        
                        # 防止无限等待（增加到120秒，给大模型更多时间生成）
                        if empty_count > 120000:  # 120000 * 1ms = 120秒
                            logger.warning(f"等待超时（{empty_count}次，约120秒），可能没有数据返回")
                            # 检查线程是否还在运行
                            if not finished_event.is_set():
                                logger.error("流式请求线程可能已卡住，尝试取消任务")
                                # 尝试取消 executor 任务（如果可能）
                                try:
                                    executor_task.cancel()
                                except:
                                    pass
                            # 抛出超时异常
                            raise TimeoutError(f"流式生成超时：等待120秒未收到数据，模型: {self.model_name}。可能是模型响应较慢或网络连接问题。")
                        
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama流式生成HTTP错误: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Ollama流式生成错误: {str(e)}", exc_info=True)
            raise
    
    async def _generate_once(self, prompt: str) -> str:
        """非流式生成"""
        try:
            logger.debug(f"开始非流式生成 - 模型: {self.model_name}, 提示长度: {len(prompt)}")
            # 在线程池中执行同步请求，避免阻塞事件循环
            import asyncio
            loop = asyncio.get_event_loop()
            
            def _sync_generate():
                response = self.session.post(
                    f"{self.base_url}/api/generate",
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=self.timeout
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
            
            response_text = await loop.run_in_executor(None, _sync_generate)
            logger.debug(f"非流式生成完成 - 回复长度: {len(response_text)}")
            return response_text
        except requests.exceptions.RequestException as e:
            logger.error(f"Ollama非流式生成HTTP错误: {str(e)}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Ollama非流式生成错误: {str(e)}", exc_info=True)
            raise


# 全局Ollama服务实例
ollama_service = OllamaService()

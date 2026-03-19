"""应用生命周期管理"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database.mongodb import mongodb
from utils.logger import logger


async def _connect_mongodb_with_retry(max_retries: int = 3, delay_seconds: float = 2.0):
    """带重试的 MongoDB 连接，启动时使用。失败不抛异常，返回是否连接成功。"""
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"正在连接 MongoDB... (尝试 {attempt}/{max_retries})")
            await mongodb.connect()
            return True
        except Exception as e:
            logger.warning(f"MongoDB 连接失败 (尝试 {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                import asyncio
                await asyncio.sleep(delay_seconds)
    logger.error(
        "MongoDB 启动时连接失败，服务将先启动，依赖 MongoDB 的接口可能不可用。"
        "请确认：1) MongoDB 已启动；2) .env 中 MONGODB_URI 或 MONGODB_HOST/PORT 正确；"
        "3) 若在 Docker 内访问宿主机请使用 host.docker.internal 或 127.0.0.1。"
    )
    return False


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理。MongoDB 连接失败时仍允许服务启动，便于本地调试。"""
    mongodb_ready = False
    try:
        mongodb_ready = await _connect_mongodb_with_retry()
        app.state.mongodb_ready = mongodb_ready

        if mongodb_ready:
            # 启动时数据修复/初始化：
            # 1) 仅保留一个默认“通用助手”（course_assistants）——对话用
            # 2) 初始化至少一个默认知识空间（knowledge_spaces）——入库/检索用
            try:
                from utils.timezone import beijing_now

                assistants = mongodb.get_collection("course_assistants")
                # 确保至少有一个默认助手
                default_assistant = await assistants.find_one({"is_default": True})
                if not default_assistant:
                    now = beijing_now()
                    await assistants.insert_one(
                        {
                            "name": "默认助手",
                            "description": "系统默认对话助手（GeneralAssistantAgent）",
                            "system_prompt": "",
                            "collection_name": "default_knowledge",
                            "is_default": True,
                            "created_at": now,
                            "updated_at": now,
                        }
                    )
                    default_assistant = await assistants.find_one({"is_default": True})

                # 删除非默认的“通用助手”（保留一个默认即可）
                await assistants.delete_many({"is_default": {"$ne": True}})

                # 初始化默认知识空间
                spaces = mongodb.get_collection("knowledge_spaces")
                default_space = await spaces.find_one({"is_default": True})
                if not default_space:
                    now = beijing_now()
                    await spaces.insert_one(
                        {
                            "name": "默认知识空间",
                            "description": "系统默认知识库空间",
                            "collection_name": "default_knowledge",
                            "is_default": True,
                            "created_at": now,
                            "updated_at": now,
                        }
                    )
            except Exception as e:
                logger.warning(f"启动初始化（助手/知识空间）失败: {e}")
    except Exception as e:
        logger.error(f"lifespan 异常: {str(e)}", exc_info=True)
        app.state.mongodb_ready = False

    yield

    # 关闭时执行
    try:
        await mongodb.disconnect()
    except Exception as e:
        logger.error(f"关闭数据库连接时出错: {str(e)}", exc_info=True)


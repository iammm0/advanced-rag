"""
资源迁移脚本
用于将旧版本服务器上的资源文件迁移到新的挂载点统一管理
"""
import os
import shutil
import asyncio
from pathlib import Path
from typing import List, Dict, Any
from database.mongodb import mongodb
from utils.logger import logger
from utils.timezone import beijing_now


# 新的资源目录（从环境变量获取）
NEW_RESOURCE_DIR = os.getenv("RESOURCE_DIR", "/app/resources")

# 可能的旧资源目录位置（根据实际情况调整）
OLD_RESOURCE_DIRS = [
    "/app/./resources",  # 相对路径 ./resources 在容器内的实际位置
    "/app/resources",  # 如果相对路径解析为 /app/resources
    "./resources",  # 旧版本可能使用的相对路径（相对于工作目录）
    "/app/uploads/resources",  # 可能存储在uploads下的resources目录
    "/app/data/resources",  # 可能存储在data目录下
    "/var/www/resources",  # 可能的其他位置
]


def find_old_resource_dirs() -> List[str]:
    """查找可能存在的旧资源目录"""
    found_dirs = []
    for old_dir in OLD_RESOURCE_DIRS:
        if os.path.exists(old_dir) and os.path.isdir(old_dir):
            # 检查目录中是否有文件
            try:
                files = [f for f in os.listdir(old_dir) if os.path.isfile(os.path.join(old_dir, f))]
                if files:
                    found_dirs.append(old_dir)
                    logger.info(f"找到旧资源目录: {old_dir}, 包含 {len(files)} 个文件")
            except Exception as e:
                logger.warning(f"检查目录 {old_dir} 失败: {str(e)}")
    return found_dirs


def migrate_resource_file(old_path: str, new_path: str) -> bool:
    """
    迁移单个资源文件

    Args:
        old_path: 旧文件路径
        new_path: 新文件路径

    Returns:
        是否迁移成功
    """
    try:
        # 如果新文件已存在，跳过
        if os.path.exists(new_path):
            logger.debug(f"文件已存在，跳过: {new_path}")
            return True

        # 确保新目录存在
        new_dir = os.path.dirname(new_path)
        os.makedirs(new_dir, exist_ok=True)

        # 复制文件
        shutil.copy2(old_path, new_path)

        # 验证文件大小
        old_size = os.path.getsize(old_path)
        new_size = os.path.getsize(new_path)
        if old_size != new_size:
            logger.error(f"文件大小不匹配: {old_path} ({old_size}) -> {new_path} ({new_size})")
            if os.path.exists(new_path):
                os.remove(new_path)
            return False

        logger.info(f"成功迁移文件: {old_path} -> {new_path}")
        return True
    except Exception as e:
        logger.error(f"迁移文件失败: {old_path} -> {new_path}, 错误: {str(e)}")
        return False


def normalize_path(file_path: str) -> str:
    """
    规范化文件路径，将相对路径转换为绝对路径

    Args:
        file_path: 原始文件路径（可能是相对路径）

    Returns:
        规范化后的绝对路径
    """
    if not file_path:
        return file_path

    # 如果已经是绝对路径且在新目录下，直接返回
    if file_path.startswith(NEW_RESOURCE_DIR):
        return file_path

    # 处理相对路径 ./resources/文件名
    if file_path.startswith("./resources/"):
        # 转换为绝对路径：/app/./resources/文件名 或 /app/resources/文件名
        filename = os.path.basename(file_path)
        # 先尝试 /app/./resources（相对路径的实际位置）
        potential_path = os.path.join("/app/./resources", filename)
        if os.path.exists(potential_path):
            return os.path.abspath(potential_path)
        # 再尝试 /app/resources
        potential_path = os.path.join("/app/resources", filename)
        if os.path.exists(potential_path):
            return potential_path
        # 如果都不存在，返回新目录路径
        return os.path.join(NEW_RESOURCE_DIR, filename)

    # 处理其他相对路径
    if not os.path.isabs(file_path):
        # 相对路径，尝试解析
        abs_path = os.path.abspath(file_path)
        if os.path.exists(abs_path):
            return abs_path
        # 如果解析后不存在，尝试从工作目录查找
        work_dir = os.getcwd()
        potential_path = os.path.join(work_dir, file_path)
        if os.path.exists(potential_path):
            return os.path.abspath(potential_path)

    return file_path


async def migrate_resources_from_db():
    """
    从数据库读取资源记录，迁移文件并更新路径
    """
    try:
        collection = mongodb.get_collection("resources")

        # 查找所有有file_path的资源
        cursor = collection.find({"file_path": {"$exists": True, "$ne": None}})
        resources = await cursor.to_list(length=None)

        logger.info(f"找到 {len(resources)} 个需要检查的资源记录")

        migrated_count = 0
        updated_count = 0
        failed_count = 0
        skipped_count = 0

        for resource in resources:
            resource_id = str(resource["_id"])
            old_file_path = resource.get("file_path")

            if not old_file_path:
                continue

            # 如果文件路径已经是新目录下的绝对路径，检查文件是否存在
            if old_file_path.startswith(NEW_RESOURCE_DIR):
                if os.path.exists(old_file_path):
                    skipped_count += 1
                    logger.debug(f"资源已在正确位置: {resource_id}, 路径: {old_file_path}")
                    continue
                else:
                    # 路径指向新目录但文件不存在，尝试从旧目录查找
                    filename = os.path.basename(old_file_path)
                    old_file_path = None  # 标记需要查找
            else:
                # 规范化路径（处理相对路径）
                normalized_path = normalize_path(old_file_path)
                filename = os.path.basename(normalized_path)

                # 如果规范化后的路径已经是新目录，直接使用
                if normalized_path.startswith(NEW_RESOURCE_DIR):
                    if os.path.exists(normalized_path):
                        # 文件已在新目录，只需更新数据库路径
                        try:
                            await collection.update_one(
                                {"_id": resource["_id"]},
                                {"$set": {"file_path": normalized_path, "updated_at": beijing_now()}}
                            )
                            updated_count += 1
                            logger.info(f"更新资源路径: {resource_id}, 新路径: {normalized_path}")
                            continue
                        except Exception as e:
                            logger.error(f"更新资源记录失败: {resource_id}, 错误: {str(e)}")
                            failed_count += 1
                            continue
                    else:
                        # 规范化后路径指向新目录但文件不存在，需要查找
                        old_file_path = None

            # 需要查找文件的实际位置
            new_file_path = os.path.join(NEW_RESOURCE_DIR, filename)
            found_path = None

            # 如果 old_file_path 存在，先尝试直接使用
            if old_file_path and os.path.exists(old_file_path):
                found_path = old_file_path
            elif old_file_path:
                # 尝试规范化后的路径
                normalized_path = normalize_path(old_file_path)
                if os.path.exists(normalized_path):
                    found_path = normalized_path

            # 如果还没找到，尝试从旧目录列表查找
            if not found_path:
                for old_dir in OLD_RESOURCE_DIRS:
                    potential_path = os.path.join(old_dir, filename)
                    # 处理相对路径的情况
                    if not os.path.isabs(potential_path):
                        potential_path = os.path.abspath(potential_path)
                    if os.path.exists(potential_path):
                        found_path = potential_path
                        break

            # 如果找到了文件，进行迁移
            if found_path:
                # 如果文件已在新目录，只需更新数据库
                if os.path.exists(new_file_path):
                    try:
                        await collection.update_one(
                            {"_id": resource["_id"]},
                            {"$set": {"file_path": new_file_path, "updated_at": beijing_now()}}
                        )
                        updated_count += 1
                        logger.info(f"更新资源路径（文件已存在）: {resource_id}, 新路径: {new_file_path}")
                    except Exception as e:
                        logger.error(f"更新资源记录失败: {resource_id}, 错误: {str(e)}")
                        failed_count += 1
                else:
                    # 迁移文件
                    if migrate_resource_file(found_path, new_file_path):
                        # 更新数据库
                        try:
                            await collection.update_one(
                                {"_id": resource["_id"]},
                                {"$set": {"file_path": new_file_path, "updated_at": beijing_now()}}
                            )
                            updated_count += 1
                            migrated_count += 1
                            logger.info(f"迁移并更新资源: {resource_id}, {found_path} -> {new_file_path}")
                        except Exception as e:
                            logger.error(f"更新资源记录失败: {resource_id}, 错误: {str(e)}")
                            failed_count += 1
                    else:
                        failed_count += 1
            else:
                logger.warning(f"资源文件不存在且未找到: {resource_id}, 原始路径: {resource.get('file_path')}, 文件名: {filename}")
                failed_count += 1

        logger.info(f"资源迁移完成 - 迁移: {migrated_count}, 更新: {updated_count}, 跳过: {skipped_count}, 失败: {failed_count}")
        return {
            "migrated": migrated_count,
            "updated": updated_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total": len(resources)
        }
    except Exception as e:
        logger.error(f"资源迁移失败: {str(e)}", exc_info=True)
        raise


async def migrate_resources_from_old_dirs():
    """
    从旧资源目录迁移所有文件到新目录
    """
    old_dirs = find_old_resource_dirs()

    if not old_dirs:
        logger.info("未找到旧资源目录")
        return {
            "migrated": 0,
            "skipped": 0,
            "failed": 0
        }

    migrated_count = 0
    skipped_count = 0
    failed_count = 0

    for old_dir in old_dirs:
        logger.info(f"开始迁移目录: {old_dir}")
        try:
            files = [f for f in os.listdir(old_dir) if os.path.isfile(os.path.join(old_dir, f))]

            for filename in files:
                old_path = os.path.join(old_dir, filename)
                new_path = os.path.join(NEW_RESOURCE_DIR, filename)

                if os.path.exists(new_path):
                    skipped_count += 1
                    logger.debug(f"文件已存在，跳过: {filename}")
                else:
                    if migrate_resource_file(old_path, new_path):
                        migrated_count += 1
                    else:
                        failed_count += 1
        except Exception as e:
            logger.error(f"迁移目录失败: {old_dir}, 错误: {str(e)}")

    logger.info(f"目录迁移完成 - 迁移: {migrated_count}, 跳过: {skipped_count}, 失败: {failed_count}")
    return {
        "migrated": migrated_count,
        "skipped": skipped_count,
        "failed": failed_count
    }


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始资源迁移任务")
    logger.info(f"新资源目录: {NEW_RESOURCE_DIR}")
    logger.info("=" * 60)

    # 确保新目录存在
    os.makedirs(NEW_RESOURCE_DIR, exist_ok=True)

    # 步骤1: 从旧目录迁移所有文件
    logger.info("\n步骤1: 从旧资源目录迁移文件...")
    dir_result = await migrate_resources_from_old_dirs()

    # 步骤2: 从数据库更新资源路径
    logger.info("\n步骤2: 更新数据库中的资源路径...")
    db_result = await migrate_resources_from_db()

    logger.info("\n" + "=" * 60)
    logger.info("资源迁移任务完成")
    logger.info(f"目录迁移: {dir_result}")
    logger.info(f"数据库更新: {db_result}")
    logger.info("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

"""
数据迁移脚本：将通知系统数据迁移到邮件系统
"""
import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.mongodb import mongodb
from utils.logger import logger
from utils.timezone import beijing_now
from bson import ObjectId


async def migrate_notifications_to_emails():
    """
    将 notifications 集合的数据迁移到 emails 集合
    将 notification_read_status 集合的数据迁移到 email_read_status 集合
    """
    try:
        notifications_collection = mongodb.get_collection("notifications")
        read_status_collection = mongodb.get_collection("notification_read_status")
        emails_collection = mongodb.get_collection("emails")
        email_read_status_collection = mongodb.get_collection("email_read_status")
        
        logger.info("开始迁移通知数据到邮件系统...")
        
        # 获取所有通知
        notifications = await notifications_collection.find({"is_active": True}).to_list(length=None)
        logger.info(f"找到 {len(notifications)} 条通知记录")
        
        migrated_count = 0
        skipped_count = 0
        
        for notification in notifications:
            try:
                # 检查是否已经迁移过（通过 created_by 和 created_at 匹配）
                existing_email = await emails_collection.find_one({
                    "from_user_id": notification.get("created_by"),
                    "subject": notification.get("title"),
                    "created_at": notification.get("created_at")
                })
                
                if existing_email:
                    logger.debug(f"通知 {notification['_id']} 已迁移，跳过")
                    skipped_count += 1
                    continue
                
                # 确定收件人
                target_audience = notification.get("target_audience", "all")
                
                # 获取所有符合条件的用户ID
                user_collection = mongodb.get_collection("users")
                query = {"is_active": True}
                
                if target_audience == "students":
                    query["user_type"] = "student"
                elif target_audience == "teachers":
                    query["user_type"] = "teacher"
                # all 不需要额外过滤
                
                cursor = user_collection.find(query)
                recipient_ids = []
                async for user_doc in cursor:
                    recipient_ids.append(str(user_doc["_id"]))
                
                if not recipient_ids:
                    logger.warning(f"通知 {notification['_id']} 没有符合条件的收件人，跳过")
                    skipped_count += 1
                    continue
                
                # 创建邮件记录
                email_doc = {
                    "from_user_id": notification.get("created_by", ""),
                    "from_username": notification.get("created_by_username", "系统"),
                    "to_user_ids": recipient_ids,
                    "to_user_type": target_audience if target_audience != "all" else None,
                    "subject": notification.get("title", ""),
                    "content": notification.get("content", ""),
                    "markdown_content": notification.get("markdown_content"),
                    "attachments": [],
                    "priority": notification.get("priority", "normal"),
                    "status": "sent",
                    "is_relationship_required": False,  # 通知不需要建立关系
                    "created_at": notification.get("created_at"),
                    "sent_at": notification.get("created_at"),
                    "updated_at": notification.get("created_at")
                }
                
                result = await emails_collection.insert_one(email_doc)
                email_id = result.inserted_id
                
                # 迁移阅读状态
                read_statuses = await read_status_collection.find({
                    "notification_id": notification["_id"]
                }).to_list(length=None)
                
                if read_statuses:
                    email_read_status_operations = []
                    for read_status in read_statuses:
                        email_read_status_operations.append({
                            "email_id": email_id,
                            "user_id": read_status["user_id"],
                            "is_read": True,  # 通知已读状态迁移为邮件已读
                            "read_at": read_status.get("read_at"),
                            "is_deleted": False,
                            "deleted_at": None,
                            "folder": "inbox",
                            "created_at": read_status.get("created_at") or notification.get("created_at")
                        })
                    
                    if email_read_status_operations:
                        await email_read_status_collection.insert_many(email_read_status_operations)
                else:
                    # 如果没有阅读状态记录，为所有收件人创建未读状态
                    email_read_status_operations = []
                    for recipient_id in recipient_ids:
                        email_read_status_operations.append({
                            "email_id": email_id,
                            "user_id": recipient_id,
                            "is_read": False,
                            "read_at": None,
                            "is_deleted": False,
                            "deleted_at": None,
                            "folder": "inbox",
                            "created_at": notification.get("created_at")
                        })
                    
                    if email_read_status_operations:
                        await email_read_status_collection.insert_many(email_read_status_operations)
                
                migrated_count += 1
                logger.info(f"已迁移通知 {notification['_id']} -> 邮件 {email_id}")
                
            except Exception as e:
                logger.error(f"迁移通知 {notification.get('_id')} 失败: {str(e)}", exc_info=True)
                skipped_count += 1
        
        logger.info(f"迁移完成！成功迁移: {migrated_count} 条，跳过: {skipped_count} 条")
        
    except Exception as e:
        logger.error(f"迁移过程出错: {str(e)}", exc_info=True)
        raise


async def main():
    """主函数"""
    try:
        # 初始化 MongoDB 连接
        await mongodb.connect()
        logger.info("MongoDB 连接成功")
        
        # 执行迁移
        await migrate_notifications_to_emails()
        
        logger.info("迁移脚本执行完成")
    except Exception as e:
        logger.error(f"迁移脚本执行失败: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        # 关闭连接
        await mongodb.disconnect()


if __name__ == "__main__":
    asyncio.run(main())


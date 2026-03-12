"""时区工具模块 - 统一使用北京时间（UTC+8）"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 北京时间时区（UTC+8）
BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now() -> datetime:
    """
    获取当前北京时间
    
    Returns:
        当前北京时间的datetime对象
    """
    return datetime.now(BEIJING_TZ)


def to_beijing_time(dt: Optional[datetime]) -> Optional[datetime]:
    """
    将datetime转换为北京时间
    
    Args:
        dt: 要转换的datetime对象（如果为None则返回None）
    
    Returns:
        转换后的北京时间datetime对象
    """
    if dt is None:
        return None
    
    # 如果datetime没有时区信息，假设为UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    # 转换为北京时间
    return dt.astimezone(BEIJING_TZ)


def beijing_from_iso(iso_string: str) -> datetime:
    """
    从ISO格式字符串创建北京时间datetime
    
    Args:
        iso_string: ISO格式的时间字符串
    
    Returns:
        北京时间datetime对象
    """
    dt = datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
    return to_beijing_time(dt)


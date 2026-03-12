"""
视频封面生成工具
使用ffmpeg提取视频的第一帧作为封面
"""
import os
import subprocess
import hashlib
from typing import Optional
from utils.logger import logger


def generate_video_thumbnail(
    video_path: str,
    thumbnail_dir: str,
    timestamp: float = 1.0,
    width: int = 320,
    height: int = 180
) -> Optional[str]:
    """
    生成视频封面（缩略图）
    
    Args:
        video_path: 视频文件路径
        thumbnail_dir: 封面保存目录
        timestamp: 提取的时间点（秒），默认1秒
        width: 封面宽度，默认320
        height: 封面高度，默认180
    
    Returns:
        封面文件路径，如果生成失败返回None
    """
    if not os.path.exists(video_path):
        logger.error(f"视频文件不存在: {video_path}")
        return None
    
    # 确保封面目录存在
    os.makedirs(thumbnail_dir, exist_ok=True)
    
    # 生成唯一的封面文件名（基于视频文件路径的哈希值）
    video_hash = hashlib.md5(video_path.encode()).hexdigest()[:8]
    video_basename = os.path.basename(video_path)
    video_name_without_ext = os.path.splitext(video_basename)[0]
    thumbnail_filename = f"{video_name_without_ext}_{video_hash}_{int(timestamp)}s.jpg"
    thumbnail_path = os.path.join(thumbnail_dir, thumbnail_filename)
    
    # 如果封面已存在，直接返回
    if os.path.exists(thumbnail_path):
        logger.info(f"封面已存在，跳过生成: {thumbnail_path}")
        return thumbnail_path
    
    try:
        # 使用ffmpeg提取视频帧（简化命令，更可靠）
        # -ss: 指定时间点（放在-i之前可以更快定位）
        # -i: 输入文件
        # -vframes 1: 只提取1帧
        # -vf scale: 缩放尺寸（保持宽高比）
        # -q:v 2: 高质量JPEG
        # -y: 覆盖已存在的文件
        cmd = [
            "ffmpeg",
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-vf", f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            "-q:v", "2",
            "-y",
            thumbnail_path
        ]
        
        logger.info(f"开始生成视频封面 - 视频: {video_path}, 封面: {thumbnail_path}, 时间点: {timestamp}秒")
        
        # 执行ffmpeg命令（增加超时时间到60秒，支持大视频文件）
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60  # 60秒超时（支持大视频文件）
        )
        
        if result.returncode == 0 and os.path.exists(thumbnail_path):
            # 验证文件大小（确保不是空文件）
            file_size = os.path.getsize(thumbnail_path)
            if file_size > 0:
                logger.info(f"视频封面生成成功: {thumbnail_path}, 文件大小: {file_size} 字节")
                return thumbnail_path
            else:
                logger.error(f"生成的封面文件为空: {thumbnail_path}")
                # 删除空文件
                try:
                    os.remove(thumbnail_path)
                except:
                    pass
                return None
        else:
            error_msg = result.stderr.decode('utf-8', errors='ignore')
            logger.error(f"生成视频封面失败 - 返回码: {result.returncode}, 错误: {error_msg[:500]}")  # 限制错误信息长度
            return None
            
    except subprocess.TimeoutExpired:
        logger.error(f"生成视频封面超时: {video_path}")
        return None
    except FileNotFoundError:
        logger.error("ffmpeg未安装或不在PATH中，无法生成视频封面")
        return None
    except Exception as e:
        logger.error(f"生成视频封面时发生异常: {str(e)}", exc_info=True)
        return None


def check_ffmpeg_available() -> bool:
    """检查ffmpeg是否可用"""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


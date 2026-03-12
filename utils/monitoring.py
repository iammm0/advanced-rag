"""性能监控工具"""
import time
import asyncio
from typing import Dict, Any, Optional
from functools import wraps
from contextlib import asynccontextmanager
from fastapi import Request, Response
from utils.logger import logger
import psutil
import os


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.request_times: Dict[str, list] = {}
        self.request_counts: Dict[str, int] = {}
        self.error_counts: Dict[str, int] = {}
        self._lock = asyncio.Lock()
    
    async def record_request(
        self,
        path: str,
        method: str,
        duration: float,
        status_code: int
    ):
        """记录请求性能"""
        key = f"{method} {path}"
        
        async with self._lock:
            if key not in self.request_times:
                self.request_times[key] = []
                self.request_counts[key] = 0
                self.error_counts[key] = 0
            
            self.request_times[key].append(duration)
            self.request_counts[key] += 1
            
            # 只保留最近1000次请求的时间记录
            if len(self.request_times[key]) > 1000:
                self.request_times[key] = self.request_times[key][-1000:]
            
            # 记录错误
            if status_code >= 400:
                self.error_counts[key] = self.error_counts.get(key, 0) + 1
    
    async def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        stats = {}
        
        async with self._lock:
            for key in self.request_times:
                times = self.request_times[key]
                if times:
                    stats[key] = {
                        "count": self.request_counts[key],
                        "error_count": self.error_counts.get(key, 0),
                        "avg_time": sum(times) / len(times),
                        "min_time": min(times),
                        "max_time": max(times),
                        "p50": self._percentile(times, 50),
                        "p95": self._percentile(times, 95),
                        "p99": self._percentile(times, 99),
                    }
        
        return stats
    
    def _percentile(self, data: list, percentile: int) -> float:
        """计算百分位数"""
        if not data:
            return 0.0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    async def get_system_metrics(self) -> Dict[str, Any]:
        """获取系统指标"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # 获取进程信息
            process = psutil.Process(os.getpid())
            process_memory = process.memory_info()
            process_cpu = process.cpu_percent(interval=0.1)
            
            return {
                "cpu": {
                    "percent": round(cpu_percent, 2),
                    "process_percent": round(process_cpu, 2),
                },
                "memory": {
                    "total_mb": round(memory.total / 1024 / 1024, 2),
                    "available_mb": round(memory.available / 1024 / 1024, 2),
                    "used_mb": round(memory.used / 1024 / 1024, 2),
                    "percent": round(memory.percent, 2),
                    "process_mb": round(process_memory.rss / 1024 / 1024, 2),
                },
                "disk": {
                    "total_gb": round(disk.total / 1024 / 1024 / 1024, 2),
                    "used_gb": round(disk.used / 1024 / 1024 / 1024, 2),
                    "free_gb": round(disk.free / 1024 / 1024 / 1024, 2),
                    "percent": round(disk.percent, 2),
                }
            }
        except Exception as e:
            logger.warning(f"获取系统指标失败: {str(e)}")
            return {"error": str(e)}


# 全局监控实例
performance_monitor = PerformanceMonitor()


def monitor_performance(func):
    """性能监控装饰器"""
    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            duration = time.time() - start_time
            
            # 尝试从kwargs中获取request和response
            request = kwargs.get('request') or (args[0] if args and hasattr(args[0], 'method') else None)
            response = kwargs.get('response') or result if hasattr(result, 'status_code') else None
            
            if request:
                path = getattr(request, 'url', {}).path if hasattr(request, 'url') else str(request)
                method = getattr(request, 'method', 'UNKNOWN')
                status_code = getattr(response, 'status_code', 200) if response else 200
                
                await performance_monitor.record_request(path, method, duration, status_code)
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"请求处理失败: {str(e)}, 耗时: {duration:.3f}s")
            raise
    
    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            duration = time.time() - start_time
            logger.debug(f"函数 {func.__name__} 执行耗时: {duration:.3f}s")
            return result
        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"函数 {func.__name__} 执行失败: {str(e)}, 耗时: {duration:.3f}s")
            raise
    
    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    else:
        return sync_wrapper


@asynccontextmanager
async def monitor_request(request: Request, response: Response):
    """请求监控上下文管理器"""
    start_time = time.time()
    path = str(request.url.path)
    method = request.method
    
    try:
        yield
    finally:
        duration = time.time() - start_time
        status_code = response.status_code
        
        await performance_monitor.record_request(path, method, duration, status_code)
        
        # 记录慢请求（超过1秒）
        if duration > 1.0:
            logger.warning(
                f"慢请求检测 - {method} {path}, 耗时: {duration:.3f}s, "
                f"状态码: {status_code}"
            )


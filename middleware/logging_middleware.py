"""请求日志中间件"""
import time
from fastapi import Request
from utils.logger import logger
from utils.monitoring import performance_monitor


async def log_requests(request: Request, call_next):
    """记录所有HTTP请求并监控性能"""
    start_time = time.time()
    
    # 记录请求信息
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    query_params = str(request.query_params) if request.query_params else ""
    
    # 只记录非健康检查的请求，减少日志量
    if not path.startswith("/health") and not path.startswith("/api/health"):
        logger.info(f"→ {method} {path}{'?' + query_params if query_params else ''} [IP: {client_ip}]")
    
    # 处理请求
    try:
        response = await call_next(request)
        
        # 计算处理时间
        process_time = time.time() - start_time
        
        # 记录到性能监控
        status_code = response.status_code
        await performance_monitor.record_request(path, method, process_time, status_code)
        
        # 记录响应信息（只记录错误和慢请求）
        if status_code >= 500:
            logger.error(f"← {method} {path} {status_code} ({process_time:.3f}s)")
        elif status_code >= 400:
            logger.warning(f"← {method} {path} {status_code} ({process_time:.3f}s)")
        elif process_time > 1.0:  # 慢请求（超过1秒）
            logger.warning(f"← {method} {path} {status_code} ({process_time:.3f}s) [慢请求]")
        # 正常请求不记录日志，减少日志量
        
        # 添加处理时间到响应头
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    except Exception as e:
        process_time = time.time() - start_time
        await performance_monitor.record_request(path, method, process_time, 500)
        logger.error(f"✗ {method} {path} ERROR ({process_time:.3f}s): {str(e)}", exc_info=True)
        raise


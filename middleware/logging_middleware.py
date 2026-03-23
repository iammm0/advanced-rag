"""请求日志中间件（支持运行时高级配置）。"""
import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List

from fastapi import Request

from services.runtime_config import get_runtime_config_sync
from utils.logger import logger
from utils.monitoring import performance_monitor


_LOG_LEVEL_MAP = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}


@dataclass
class HttpLogConfig:
    base_level: int = logging.INFO
    request_level: int = logging.INFO
    success_level: int = logging.INFO
    slow_level: int = logging.WARNING
    client_error_level: int = logging.WARNING
    server_error_level: int = logging.ERROR
    slow_threshold_s: float = 1.0
    success_enabled: bool = False
    include_query: bool = True
    include_client_ip: bool = True
    include_request_body: bool = False
    request_body_max_chars: int = 1000
    exclude_prefixes: List[str] = None  # type: ignore[assignment]

    def __post_init__(self):
        if self.exclude_prefixes is None:
            self.exclude_prefixes = ["/health", "/api/health"]


def _parse_bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def _parse_int(value: Any, default: int, minimum: int = 0) -> int:
    try:
        parsed = int(value)
        return max(parsed, minimum)
    except (TypeError, ValueError):
        return default


def _parse_float(value: Any, default: float, minimum: float = 0.0) -> float:
    try:
        parsed = float(value)
        return max(parsed, minimum)
    except (TypeError, ValueError):
        return default


def _parse_level(value: Any, default: int) -> int:
    if value is None:
        return default
    normalized = str(value).strip().upper()
    return _LOG_LEVEL_MAP.get(normalized, default)


def _parse_exclude_prefixes(value: Any, default: List[str]) -> List[str]:
    if isinstance(value, list):
        prefixes = [str(item).strip() for item in value if str(item).strip()]
        return prefixes or default
    if isinstance(value, str):
        prefixes = [part.strip() for part in value.split(",") if part.strip()]
        return prefixes or default
    return default


def _load_http_log_config() -> HttpLogConfig:
    params: Dict[str, Any] = {}
    try:
        cfg = get_runtime_config_sync()
        params = dict(cfg.get("params") or {})
    except Exception:
        # 中间件不能因配置读取失败而中断请求流程
        params = {}

    default_level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    base_level = _parse_level(params.get("http_log_level", default_level_name), logging.INFO)

    return HttpLogConfig(
        base_level=base_level,
        request_level=_parse_level(params.get("http_log_request_level"), base_level),
        success_level=_parse_level(params.get("http_log_success_level"), base_level),
        slow_level=_parse_level(params.get("http_log_slow_level"), logging.WARNING),
        client_error_level=_parse_level(params.get("http_log_client_error_level"), logging.WARNING),
        server_error_level=_parse_level(params.get("http_log_server_error_level"), logging.ERROR),
        slow_threshold_s=_parse_float(params.get("http_log_slow_threshold_s"), 1.0, minimum=0.0),
        success_enabled=_parse_bool(params.get("http_log_success_enabled"), False),
        include_query=_parse_bool(params.get("http_log_include_query"), True),
        include_client_ip=_parse_bool(params.get("http_log_include_client_ip"), True),
        include_request_body=_parse_bool(params.get("http_log_include_request_body"), False),
        request_body_max_chars=_parse_int(params.get("http_log_request_body_max_chars"), 1000, minimum=0),
        exclude_prefixes=_parse_exclude_prefixes(
            params.get("http_log_exclude_prefixes"),
            ["/health", "/api/health"],
        ),
    )


def _emit(level: int, message: str, *, exc_info: bool = False):
    if logger.isEnabledFor(level):
        logger.log(level, message, exc_info=exc_info)


def _sanitize_body(raw: bytes, max_chars: int) -> str:
    if max_chars <= 0 or not raw:
        return ""
    text = raw.decode("utf-8", errors="replace")
    text = " ".join(text.split())
    if len(text) <= max_chars:
        return text
    return f"{text[:max_chars]}...(truncated)"


async def log_requests(request: Request, call_next):
    """记录HTTP请求并监控性能。"""
    start_time = time.time()
    cfg = _load_http_log_config()

    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path
    query_params = str(request.query_params) if request.query_params else ""
    path_with_query = f"{path}{'?' + query_params if (query_params and cfg.include_query) else ''}"
    should_skip = any(path.startswith(prefix) for prefix in cfg.exclude_prefixes)

    request_body_msg = ""
    if cfg.include_request_body and method in {"POST", "PUT", "PATCH"}:
        try:
            body_bytes = await request.body()
            body_preview = _sanitize_body(body_bytes, cfg.request_body_max_chars)
            if body_preview:
                try:
                    parsed = json.loads(body_preview)
                    request_body_msg = f" body={json.dumps(parsed, ensure_ascii=False)}"
                except json.JSONDecodeError:
                    request_body_msg = f" body={body_preview}"
        except Exception:
            request_body_msg = " body=<unavailable>"

    if not should_skip:
        ip_msg = f" [IP: {client_ip}]" if cfg.include_client_ip else ""
        _emit(cfg.request_level, f"→ {method} {path_with_query}{ip_msg}{request_body_msg}")

    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        status_code = response.status_code
        await performance_monitor.record_request(path, method, process_time, status_code)

        if not should_skip:
            message = f"← {method} {path} {status_code} ({process_time:.3f}s)"
            if status_code >= 500:
                _emit(cfg.server_error_level, message)
            elif status_code >= 400:
                _emit(cfg.client_error_level, message)
            elif process_time > cfg.slow_threshold_s:
                _emit(cfg.slow_level, f"{message} [慢请求]")
            elif cfg.success_enabled:
                _emit(cfg.success_level, message)

        response.headers["X-Process-Time"] = str(process_time)
        return response
    except Exception as e:
        process_time = time.time() - start_time
        await performance_monitor.record_request(path, method, process_time, 500)
        if not should_skip:
            _emit(
                cfg.server_error_level,
                f"✗ {method} {path} ERROR ({process_time:.3f}s): {str(e)}",
                exc_info=True,
            )
        raise

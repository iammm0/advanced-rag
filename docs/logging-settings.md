# 日志中间件高级配置

本文说明 `middleware/logging_middleware.py` 支持的运行时日志参数。  
这些参数通过 `PUT /api/settings/runtime` 的 `params` 字段下发，可在服务运行中动态生效。

## 1. 使用方式

请求示例：

```http
PUT /api/settings/runtime
Content-Type: application/json
```

```json
{
  "params": {
    "http_log_level": "INFO",
    "http_log_request_level": "INFO",
    "http_log_success_enabled": false,
    "http_log_slow_threshold_s": 1.0
  }
}
```

## 2. 参数说明

| 参数名 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `http_log_level` | `string` | `INFO` | HTTP日志基准级别。可选：`DEBUG/INFO/WARNING/ERROR/CRITICAL` |
| `http_log_request_level` | `string` | 跟随 `http_log_level` | 请求进入日志（`→ METHOD PATH`）级别 |
| `http_log_success_level` | `string` | 跟随 `http_log_level` | 成功响应日志级别（仅在开启成功日志时生效） |
| `http_log_slow_level` | `string` | `WARNING` | 慢请求日志级别 |
| `http_log_client_error_level` | `string` | `WARNING` | 4xx 响应日志级别 |
| `http_log_server_error_level` | `string` | `ERROR` | 5xx 与异常日志级别 |
| `http_log_slow_threshold_s` | `float` | `1.0` | 慢请求阈值（秒），大于该值按慢请求记录 |
| `http_log_success_enabled` | `bool` | `false` | 是否记录普通成功响应（2xx/3xx 且非慢请求） |
| `http_log_include_query` | `bool` | `true` | 请求日志是否带 query 参数 |
| `http_log_include_client_ip` | `bool` | `true` | 请求日志是否带客户端 IP |
| `http_log_include_request_body` | `bool` | `false` | 是否记录请求体（仅 `POST/PUT/PATCH`） |
| `http_log_request_body_max_chars` | `int` | `1000` | 请求体最大记录字符数，超长会截断 |
| `http_log_exclude_prefixes` | `string[]` 或 `string` | `["/health", "/api/health"]` | 按路径前缀排除日志，例如健康检查 |

## 3. 推荐配置

### 开发环境（便于排查）

```json
{
  "params": {
    "http_log_level": "DEBUG",
    "http_log_request_level": "DEBUG",
    "http_log_success_enabled": true,
    "http_log_success_level": "INFO",
    "http_log_slow_threshold_s": 0.5,
    "http_log_include_query": true,
    "http_log_include_client_ip": true,
    "http_log_include_request_body": false
  }
}
```

### 生产环境（控制日志量）

```json
{
  "params": {
    "http_log_level": "INFO",
    "http_log_request_level": "INFO",
    "http_log_success_enabled": false,
    "http_log_slow_threshold_s": 1.0,
    "http_log_slow_level": "WARNING",
    "http_log_client_error_level": "WARNING",
    "http_log_server_error_level": "ERROR",
    "http_log_exclude_prefixes": ["/health", "/api/health"]
  }
}
```

## 4. 行为说明

- 请求进入时记录 `→` 日志；响应返回时按状态码和耗时输出 `←` 日志。
- 5xx 或异常优先按 `http_log_server_error_level` 记录。
- 4xx 按 `http_log_client_error_level` 记录。
- 成功请求默认不记录响应日志；启用 `http_log_success_enabled` 后才会记录。
- 请求体日志会做长度截断，避免超大 payload 影响日志体积。

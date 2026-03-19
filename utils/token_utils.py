from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class TokenBudget:
    """简单 token 预算配置（近似估算，避免强绑定特定 tokenizer）。"""

    chunk_tokens: int
    overlap_tokens: int = 0
    max_chunk_tokens: Optional[int] = None


def estimate_tokens(text: str) -> int:
    """
    近似估算 token 数。

    设计目标：
    - 不引入强依赖（tiktoken/transformers 不一定存在）
    - 对中英文混排有相对稳定的尺度
    - 作为“预算器”而非精确 tokenizer
    """
    if not text:
        return 0

    cjk = 0
    ascii_chars = 0
    other = 0

    for ch in text:
        code = ord(ch)
        if 0x4E00 <= code <= 0x9FFF or 0x3400 <= code <= 0x4DBF:
            cjk += 1
        elif code < 128:
            ascii_chars += 1
        else:
            other += 1

    # 经验近似：
    # - 英文/数字/符号：约 4 chars ≈ 1 token
    # - 中文：1 char ≈ 1 token（略保守，避免超预算）
    # - 其他 unicode：按 2 chars ≈ 1 token
    return int((ascii_chars / 4.0) + cjk + (other / 2.0)) + 1


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """按近似 token 预算截断文本（从尾部截断，保留前文）。"""
    if not text:
        return ""
    if max_tokens <= 0:
        return ""
    if estimate_tokens(text) <= max_tokens:
        return text

    # 逐步二分截断（避免 O(n^2)）
    lo = 0
    hi = len(text)
    best = 0
    while lo <= hi:
        mid = (lo + hi) // 2
        cand = text[:mid]
        t = estimate_tokens(cand)
        if t <= max_tokens:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return text[:best]


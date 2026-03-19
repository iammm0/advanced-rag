"""面向长行业报告的结构 + token 预算分块器"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from chunking.base import BaseChunker
from utils.token_utils import TokenBudget, estimate_tokens


_HEADING_PATTERNS = [
    # Markdown
    re.compile(r"^(#{1,6})\s+(.+?)\s*$", re.MULTILINE),
    # 中文章节：第X章 / 第X节
    re.compile(r"^(第[一二三四五六七八九十0-9]+[章节节])\s*(.+?)\s*$", re.MULTILINE),
    # 数字标题：1 / 1.1 / 1.1.1
    re.compile(r"^(\d+(?:\.\d+){0,4})\s+(.+?)\s*$", re.MULTILINE),
    # 中文编号：一、（一） 1）
    re.compile(r"^([一二三四五六七八九十]+、|\（[一二三四五六七八九十]+\）|\d+\))\s*(.+?)\s*$", re.MULTILINE),
]


def _split_blocks(text: str) -> List[str]:
    # 先按空行切段，保留结构
    blocks = [b.strip() for b in re.split(r"\n\s*\n+", text) if b and b.strip()]
    return blocks


def _detect_heading(block: str) -> Optional[str]:
    first_line = block.splitlines()[0].strip() if block else ""
    if not first_line:
        return None
    for pat in _HEADING_PATTERNS:
        m = pat.match(first_line)
        if m:
            # 标题文本尽量取 group(2)，否则 group(0)
            return (m.group(2) if m.lastindex and m.lastindex >= 2 else m.group(0)).strip()
    return None


class ReportChunker(BaseChunker):
    """
    面向长行业报告的分块器：
    - 段落/条款边界优先
    - 维护 section_path（标题层级的路径）
    - 以 token 预算控制 chunk 尺度
    """

    def __init__(
        self,
        token_budget: TokenBudget = TokenBudget(chunk_tokens=800, overlap_tokens=120, max_chunk_tokens=1200),
        min_chunk_tokens: int = 120,
    ):
        self.token_budget = token_budget
        self.min_chunk_tokens = min_chunk_tokens

    def chunk(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        metadata = metadata or {}
        blocks = _split_blocks(text)
        chunks: List[Dict[str, Any]] = []

        section_path: List[str] = []
        buf: List[str] = []
        buf_tokens = 0

        def flush():
            nonlocal buf, buf_tokens
            if not buf:
                return
            joined = "\n\n".join(buf).strip()
            t = estimate_tokens(joined)
            if t >= self.min_chunk_tokens or not chunks:
                chunks.append(
                    {
                        "text": joined,
                        "chunk_index": len(chunks),
                        "metadata": {
                            **metadata,
                            "section_path": section_path.copy(),
                            "token_count": t,
                            "chunker_type": "report",
                            "content_type": metadata.get("content_type", "text"),
                        },
                    }
                )
            buf = []
            buf_tokens = 0

        for block in blocks:
            heading = _detect_heading(block)
            if heading:
                # 遇到标题先落盘已有缓冲，更新路径
                flush()
                # 简化：将标题追加到路径（不做层级栈回退，先保证可用）
                section_path.append(heading[:200])
                # 标题本身也进入下一块开头，利于语义锚定
                buf = [block]
                buf_tokens = estimate_tokens(block)
                continue

            block_tokens = estimate_tokens(block)

            # 若当前块加入后超预算，先 flush，再起新块
            soft_limit = self.token_budget.chunk_tokens
            hard_limit = self.token_budget.max_chunk_tokens or int(soft_limit * 1.5)
            if buf and (buf_tokens + block_tokens) > soft_limit:
                flush()

            # 单块过大：按句子粗切
            if block_tokens > hard_limit:
                sentences = re.split(r"(?<=[。！？.!?])\s+", block)
                tmp: List[str] = []
                tmp_tokens = 0
                for sent in sentences:
                    sent = sent.strip()
                    if not sent:
                        continue
                    st = estimate_tokens(sent)
                    if tmp and (tmp_tokens + st) > soft_limit:
                        buf = tmp
                        buf_tokens = tmp_tokens
                        flush()
                        tmp = []
                        tmp_tokens = 0
                    tmp.append(sent)
                    tmp_tokens += st
                if tmp:
                    buf = tmp
                    buf_tokens = tmp_tokens
                    flush()
                continue

            buf.append(block)
            buf_tokens += block_tokens

        flush()
        return chunks


"""Entire Code Review 演示模块。

用于验证 Entire 官方预设 Code review Agent 的端到端流程：
本分支推送后，Agent 会对该 Change 进行评审，并在 Trails 中给出结论。
"""

from __future__ import annotations

import re
from typing import Iterable

_HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)(?!-)[a-z0-9-]{1,63}(?:\.(?!-)[a-z0-9-]{1,63})*\.?$"
)


def normalize_hostname(value: str) -> str:
    """把用户输入的域名归一化为小写、无末尾点、无协议的纯主机名。

    非法输入会抛出 ValueError，避免上层把脏数据写进资产表。
    """
    candidate = value.strip().lower()
    if "://" in candidate:
        candidate = candidate.split("://", 1)[1]
    candidate = candidate.split("/", 1)[0]
    if not candidate:
        raise ValueError("hostname must not be empty")
    if not _HOSTNAME_RE.match(candidate):
        raise ValueError(f"invalid hostname: {value!r}")
    return candidate.rstrip(".")


def dedupe_hostnames(values: Iterable[str]) -> list[str]:
    """归一化并去重，保持首次出现的顺序。"""
    seen: dict[str, None] = {}
    for raw in values:
        seen.setdefault(normalize_hostname(raw), None)
    return list(seen)

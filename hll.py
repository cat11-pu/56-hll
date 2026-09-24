"""hll.py：基数估计（基线：精确集合）。"""
from __future__ import annotations


class Distinct:
    def __init__(self, precision: int = 4, sparse_limit: int = 8):
        self.precision = precision
        self.sparse_limit = sparse_limit
        self.seen = set()
        self.merge_count = 0

    def add(self, item: str) -> dict:
        """基线：全收。"""
        self.seen.add(item)
        return {"count": len(self.seen)}

    def estimate(self) -> int:
        """基线：精确值。"""
        return len(self.seen)

    def merge(self, other) -> "Distinct":
        raise NotImplementedError("摘要合并还没实现")

    def registers(self) -> list:
        raise NotImplementedError("寄存器还没实现")

    def persist(self) -> bytes:
        raise NotImplementedError("快照还没实现")

    def restore(self, blob: bytes = None) -> dict:
        raise NotImplementedError("重启恢复还没实现")

    def stats(self) -> dict:
        return {"precision": self.precision, "sparse_limit": self.sparse_limit,
                "seen": len(self.seen), "mode": "sparse"}

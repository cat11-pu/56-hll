"""hll.py：基数估计（HyperLogLog，纯标准库）。

稀疏模式（样本数 <= sparse_limit）保存精确集合；超过后切换为稠密模式，
维护 m = 2^precision 个寄存器，内存占用与基数无关。
"""
from __future__ import annotations

import hashlib
import json
import math


class Distinct:
    def __init__(self, precision: int = 4, sparse_limit: int = 8):
        self.precision = precision
        self.sparse_limit = sparse_limit
        self.m = 1 << precision
        self.seen = set()
        self._registers = None  # None 表示稀疏模式
        self.merge_count = 0

    @property
    def mode(self) -> str:
        return "sparse" if self._registers is None else "dense"

    def _hash(self, item) -> tuple:
        data = item if isinstance(item, bytes) else str(item).encode("utf-8")
        x = int.from_bytes(hashlib.sha1(data).digest()[:4], "big")
        index = x & (self.m - 1)
        w = x >> self.precision
        width = 32 - self.precision
        if w == 0:
            rho = width + 1
        else:
            rho = 1
            while not (w & 1):
                w >>= 1
                rho += 1
        return index, rho

    def _add_dense(self, item) -> None:
        index, rho = self._hash(item)
        if rho > self._registers[index]:
            self._registers[index] = rho

    def _densify(self) -> None:
        self._registers = [0] * self.m
        items = self.seen
        self.seen = set()
        for item in items:
            self._add_dense(item)

    def add(self, item: str) -> dict:
        if self._registers is None:
            self.seen.add(item)
            if len(self.seen) <= self.sparse_limit:
                return {"count": len(self.seen)}
            self._densify()
        else:
            self._add_dense(item)
        return {"count": self.estimate()}

    def estimate(self) -> int:
        if self._registers is None:
            return len(self.seen)
        m = self.m
        if m == 16:
            alpha = 0.673
        elif m == 32:
            alpha = 0.697
        elif m == 64:
            alpha = 0.709
        else:
            alpha = 0.7213 / (1 + 1.079 / m)
        indicator = sum(2.0 ** -reg for reg in self._registers)
        raw = alpha * m * m / indicator
        zeros = self._registers.count(0)
        if raw <= 2.5 * m and zeros:
            raw = m * math.log(m / zeros)
        return int(raw)

    def _dense_view(self) -> list:
        if self._registers is not None:
            return list(self._registers)
        view = [0] * self.m
        for item in self.seen:
            index, rho = self._hash(item)
            if rho > view[index]:
                view[index] = rho
        return view

    def merge(self, other) -> "Distinct":
        merged = Distinct(self.precision, self.sparse_limit)
        if self.mode == "sparse" and other.mode == "sparse":
            union = self.seen | other.seen
            if len(union) <= self.sparse_limit:
                merged.seen = set(union)
                merged.merge_count = self.merge_count + other.merge_count + 1
                return merged
        merged._registers = [max(a, b) for a, b in zip(self._dense_view(), other._dense_view())]
        merged.seen = set()
        merged.merge_count = self.merge_count + other.merge_count + 1
        return merged

    def registers(self) -> list:
        if self._registers is not None:
            return list(self._registers)
        return self._dense_view()

    def persist(self) -> bytes:
        state = {
            "precision": self.precision,
            "sparse_limit": self.sparse_limit,
            "mode": self.mode,
            "registers": self.registers(),
            "items": sorted(self.seen) if self._registers is None else [],
            "merge_count": self.merge_count,
        }
        return json.dumps(state).encode("utf-8")

    def restore(self, blob: bytes = None) -> dict:
        if blob is not None:
            state = json.loads(blob.decode("utf-8"))
            self.precision = state["precision"]
            self.sparse_limit = state["sparse_limit"]
            self.m = 1 << self.precision
            self.merge_count = state.get("merge_count", 0)
            if state["mode"] == "dense":
                self._registers = list(state["registers"])
                self.seen = set()
            else:
                self._registers = None
                self.seen = set(state.get("items", []))
        return {"mode": self.mode, "registers": self.registers()}

    def stats(self) -> dict:
        return {"precision": self.precision, "sparse_limit": self.sparse_limit,
                "seen": len(self.seen), "mode": self.mode}

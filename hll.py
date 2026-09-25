"""hll.py：基数估计（稀疏精确 + 稠密 HyperLogLog）。"""
from __future__ import annotations

import hashlib
import json
import math


class Distinct:
    def __init__(self, precision: int = 4, sparse_limit: int = 8):
        self.precision = precision
        self.sparse_limit = sparse_limit
        self.m = 1 << precision
        self.mode = "sparse"
        self.seen = set()
        self._registers = [0] * self.m
        self.merge_count = 0

    def _hash(self, item: str):
        x = int(hashlib.sha1(item.encode("utf-8")).hexdigest()[:8], 16)
        index = x & (self.m - 1)
        rest = x >> self.precision
        width = 32 - self.precision
        rho = (rest & -rest).bit_length() if rest else width + 1
        return index, rho

    def _switch_to_dense(self) -> None:
        registers = [0] * self.m
        for item in self.seen:
            index, rho = self._hash(item)
            if rho > registers[index]:
                registers[index] = rho
        self._registers = registers
        self.seen = set()
        self.mode = "dense"

    def _dense_view(self) -> list:
        if self.mode == "dense":
            return list(self._registers)
        registers = [0] * self.m
        for item in self.seen:
            index, rho = self._hash(item)
            if rho > registers[index]:
                registers[index] = rho
        return registers

    def _alpha(self) -> float:
        if self.m == 16:
            return 0.673
        if self.m == 32:
            return 0.697
        if self.m == 64:
            return 0.709
        return 0.7213 / (1 + 1.079 / self.m)

    def add(self, item: str) -> dict:
        """稀疏模式精确计数；超过 sparse_limit 后切换稠密模式。"""
        if self.mode == "sparse":
            self.seen.add(item)
            if len(self.seen) > self.sparse_limit:
                self._switch_to_dense()
                return {"count": self.estimate()}
            return {"count": len(self.seen)}
        index, rho = self._hash(item)
        if rho > self._registers[index]:
            self._registers[index] = rho
        return {"count": self.estimate()}

    def estimate(self) -> int:
        """稀疏返回精确值；稠密返回调和平均估计（小范围线性计数校正）。"""
        if self.mode == "sparse":
            return len(self.seen)
        raw = self._alpha() * self.m * self.m / sum(2.0 ** -r for r in self._registers)
        zeros = self._registers.count(0)
        if raw <= 2.5 * self.m and zeros:
            return int(self.m * math.log(self.m / zeros))
        return int(raw)

    def merge(self, other) -> "Distinct":
        left = self._dense_view()
        right = other._dense_view()
        merged = Distinct(self.precision, self.sparse_limit)
        merged._registers = [max(a, b) for a, b in zip(left, right)]
        merged.mode = "dense"
        merged.seen = set()
        self.merge_count += 1
        return merged

    def registers(self) -> list:
        return self._dense_view()

    def persist(self) -> bytes:
        payload = {
            "precision": self.precision,
            "sparse_limit": self.sparse_limit,
            "mode": self.mode,
            "registers": list(self._registers),
            "seen": sorted(self.seen),
        }
        return json.dumps(payload, sort_keys=True).encode("utf-8")

    def restore(self, blob: bytes = None) -> dict:
        if blob is not None:
            text = blob.decode("utf-8") if isinstance(blob, (bytes, bytearray)) else blob
            payload = json.loads(text)
            self.precision = payload["precision"]
            self.sparse_limit = payload["sparse_limit"]
            self.m = 1 << self.precision
            self.mode = payload["mode"]
            self._registers = list(payload["registers"])
            self.seen = set(payload["seen"])
        return {"mode": self.mode, "registers": self.registers(), "seen": len(self.seen)}

    def stats(self) -> dict:
        return {"precision": self.precision, "sparse_limit": self.sparse_limit,
                "seen": len(self.seen), "mode": self.mode}

"""cardapi.py：对外门面（老接口 add/estimate 不能改）。"""
from __future__ import annotations

from hll import Distinct


class Counter:
    def __init__(self, precision: int = 4, sparse_limit: int = 8):
        self.counter = Distinct(precision, sparse_limit)

    def add(self, item: str) -> dict:
        return self.counter.add(item)

    def estimate(self) -> int:
        return self.counter.estimate()

    def merge(self, other) -> "Counter":
        return self.counter.merge(other.counter if hasattr(other, "counter") else other)

    def registers(self) -> list:
        return self.counter.registers()

    def snapshot(self) -> bytes:
        return self.counter.persist()

    def rebuild(self, blob: bytes = None) -> dict:
        return self.counter.restore(blob)

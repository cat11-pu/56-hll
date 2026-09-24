"""check_sample.py：按 sample/stream.json 走一圈，打印验收面。"""
import json
import os
import sys

from hll import Distinct


def main() -> int:
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join("sample", "stream.json")
    with open(path, encoding="utf-8") as handle:
        spec = json.load(handle)
    counter = Distinct(spec["precision"], spec["sparse_limit"])
    for item in spec["items"]:
        counter.add(item)
    estimate = counter.estimate()
    second = Distinct(spec["precision"], spec["sparse_limit"])
    for item in spec["more_items"]:
        second.add(item)
    merged = counter.merge(second)
    blob = counter.persist()
    reborn = Distinct(spec["precision"], spec["sparse_limit"])
    restored = reborn.restore(blob)
    registers = counter.registers()
    exact = len(set(spec["items"]))
    merged_exact = len(set(spec["items"]) | set(spec["more_items"]))
    print("估计值 =", estimate)
    print("真实基数 =", exact)
    print("相对误差（百分比） =", round(abs(estimate - exact) / exact * 100, 1))
    print("误差上限（百分比） =", spec["error_bound"])
    print("寄存器个数 =", len(registers))
    print("寄存器模式 =", counter.stats().get("mode"))
    print("合并后的估计 =", merged.estimate())
    print("合并后的真实基数 =", merged_exact)
    print("恢复后的寄存器 =", restored.get("registers"))
    print("不变量（估计落在误差界内） =", spec["error_invariant"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

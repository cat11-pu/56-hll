# hll

纯 Python 标准库的 HyperLogLog 基数估计。

## 用法

    from hll import Distinct
    from cardapi import Counter  # 对外门面，add/estimate 结构不变

    counter = Distinct(precision=4, sparse_limit=8)
    counter.add("a")            # {"count": ...}；样本数 <= sparse_limit 时精确（稀疏模式）
    counter.estimate()          # 稠密模式：调和平均 + 线性计数校正
    merged = counter.merge(other)   # 逐寄存器取最大，返回新摘要
    blob = counter.persist()        # 快照落盘（bytes）
    counter.restore(blob)           # 重启恢复寄存器与模式

稠密模式维护 `m = 2^precision` 个寄存器，内存不随基数增长。

## 测试

    python3 -m unittest discover -s tests -v

## 场景自检

    python3 check_sample.py

# -*- coding: utf-8 -*-
"""静态 3% vs 动态 2σ 触发对比（2016 以来）
动态方案：事件 = 单日|涨跌| >= k × 滚动20日标准差（k=1.5/2.0/2.5）
看触发频率是否更均匀、不漏不滥。
"""
import os, glob, statistics

MEM = r'E:\仪度六壬择日\yiduluren\_memory'

def load_series():
    rows = {}
    files = sorted(glob.glob(os.path.join(MEM, 'idx_*.txt')) +
                   glob.glob(os.path.join(MEM, 'sh000001_2021_2024.txt')))
    for fp in files:
        with open(fp, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not (line.startswith('| 20') or line.startswith('| 19')):
                    continue
                cols = [c.strip() for c in line.strip('|').split('|')]
                if len(cols) < 3:
                    continue
                try:
                    rows[cols[0]] = (float(cols[1]), float(cols[2]))
                except ValueError:
                    continue
    return sorted(rows.items())

def main():
    series = load_series()
    dates = [d for d, _ in series]
    closes = [cl for _, (op, cl) in series]
    N = len(series)
    chgs = [(closes[i] / closes[i-1] - 1) * 100 for i in range(1, N)]
    dts = dates[1:]  # 与 chgs 对齐

    # 2016 起
    s0 = next(i for i, d in enumerate(dts) if d >= '2016-01-01')

    # 滚动 20 日标准差（用当日及之前 20 个 chgs）
    roll_sd = [None] * len(chgs)
    for i in range(20, len(chgs)):
        roll_sd[i] = statistics.stdev(chgs[i-20:i])

    def by_year(ev_flags):
        from collections import Counter
        c = Counter(d[:4] for d, f in zip(dts, ev_flags) if f)
        return c

    # 静态 3%
    static3 = [abs(c) >= 3.0 for c in chgs]
    # 动态 kσ（k=1.5/2.0/2.5），用当日滚动σ；无σ（前20日）跳过
    for k in (1.5, 2.0, 2.5):
        dyn = [roll_sd[i] is not None and abs(chgs[i]) >= k * roll_sd[i] for i in range(len(chgs))]

        print(f'── 动态 {k}σ（2016 以来）──')
        seg = dts[s0:]
        n_static = sum(1 for d, f in zip(dts, static3) if d >= '2016-01-01' and f)
        n_dyn = sum(1 for d, f in zip(dts, dyn) if d >= '2016-01-01' and f)
        print(f'  静态 3%: {n_static} 次 | 动态 {k}σ: {n_dyn} 次')
        cy = by_year([d >= '2016-01-01' and f for d, f in zip(dts, dyn)])
        cs = by_year([d >= '2016-01-01' and f for d, f in zip(dts, static3)])
        print(f'  静态按年: {dict(sorted(cs.items()))}')
        print(f'  动态按年: {dict(sorted(cy.items()))}')
        # 动态捕获但静态漏掉的事件（动态触发静态未触发），看这些事件平均|涨跌|
        extra = [abs(chgs[i]) for i in range(len(chgs)) if dts[i] >= '2016-01-01' and dyn[i] and not static3[i]]
        if extra:
            print(f'  动态多捕获(静态漏掉): {len(extra)} 次, 平均|涨跌| {statistics.mean(extra):.2f}%, 范围 {min(extra):.1f}~{max(extra):.1f}%')

    # 全样本静态3% σ 分布（验证 3%≈多少σ）
    print('\n全样本 3% 事件对应的当日σ倍数:')
    vals = [abs(chgs[i]) / roll_sd[i] for i in range(len(chgs)) if roll_sd[i] and abs(chgs[i]) >= 3.0]
    if vals:
        print(f'  共 {len(vals)} 次, 中位 {statistics.median(vals):.2f}σ, 范围 {min(vals):.2f}~{max(vals):.2f}σ')
    # 近10年 3% 事件对应 σ 倍数
    vals16 = [abs(chgs[i]) / roll_sd[i] for i in range(len(chgs)) if roll_sd[i] and abs(chgs[i]) >= 3.0 and dts[i] >= '2016-01-01']
    if vals16:
        print(f'  2016以来 {len(vals16)} 次, 中位 {statistics.median(vals16):.2f}σ, 范围 {min(vals16):.2f}~{max(vals16):.2f}σ')

if __name__ == '__main__':
    main()

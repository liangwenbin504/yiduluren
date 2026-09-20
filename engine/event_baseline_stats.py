# -*- coding: utf-8 -*-
"""事件驱动起课 · 条件基线实证
用本地上证指数日线（_memory/idx_*.txt + sh000001_2021_2024.txt）统计：
单日|涨跌|>=3% 事件发生后 5/10/20 个交易日（窗口收益回检）的上涨概率与平均收益。
口径：窗口收益 = close[t+N]/close[t] - 1；不含事件当日。日期升序，重叠段按日期去重。
"""
import os, glob, sys

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
                    op, cl = float(cols[1]), float(cols[2])
                except ValueError:
                    continue
                rows[cols[0]] = (op, cl)
    return sorted(rows.items())

def main():
    series = load_series()
    dates = [d for d, _ in series]
    closes = [cl for _, (op, cl) in series]
    print(f'交易日总数: {len(dates)}  ({dates[0]} ~ {dates[-1]})')

    # 事件定义：单日涨跌幅（收盘vs前收盘）
    events_up, events_dn = [], []
    for i in range(1, len(series)):
        chg = (closes[i] / closes[i-1] - 1) * 100
        if chg >= 3.0:
            events_up.append((i, chg))
        elif chg <= -3.0:
            events_dn.append((i, chg))

    print(f'单日涨>=3%: {len(events_up)} 次 | 跌>=3%: {len(events_dn)} 次')

    def stats(events, label):
        print(f'\n── {label}（事件数 {len(events)}）──')
        for N in (5, 10, 20):
            ups = 0; tot = 0; rets = []
            for i, chg in events:
                j = i + N
                if j >= len(series):
                    continue
                r = (closes[j] / closes[i] - 1) * 100
                rets.append(r); tot += 1
                if r > 0:
                    ups += 1
            if tot:
                avg = sum(rets) / tot
                print(f'  后{N}交易日: 上涨概率 {ups/tot*100:.1f}% ({ups}/{tot}) | 平均收益 {avg:+.2f}%')

    stats(events_up, '大涨≥3% 事件')
    stats(events_dn, '大跌≥3% 事件')

    # 合并 |涨跌|>=3%
    all_ev = sorted(events_up + events_dn)
    print(f'\n── |涨跌|≥3% 合并（事件数 {len(all_ev)}）──')
    for N in (5, 10, 20):
        ups = 0; tot = 0; rets = []
        for i, chg in all_ev:
            j = i + N
            if j >= len(series):
                continue
            r = (closes[j] / closes[i] - 1) * 100
            rets.append(r); tot += 1
            if r > 0:
                ups += 1
        if tot:
            avg = sum(rets) / tot
            print(f'  后{N}交易日: 上涨概率 {ups/tot*100:.1f}% ({ups}/{tot}) | 平均收益 {avg:+.2f}%')

    # 大涨后 5 日继续上涨 vs 大跌后 5 日继续下跌（短期动量）
    print('\n── 短期动量检验 ──')
    n5up = sum(1 for i, chg in events_up if i+5 < len(series) and closes[i+5] > closes[i])
    n5up_tot = sum(1 for i, chg in events_up if i+5 < len(series))
    print(f'大涨后5日继续上涨: {n5up/n5up_tot*100:.1f}% ({n5up}/{n5up_tot})')
    n5dn = sum(1 for i, chg in events_dn if i+5 < len(series) and closes[i+5] < closes[i])
    n5dn_tot = sum(1 for i, chg in events_dn if i+5 < len(series))
    print(f'大跌后5日继续下跌: {n5dn/n5dn_tot*100:.1f}% ({n5dn}/{n5dn_tot})')

if __name__ == '__main__':
    main()

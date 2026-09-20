# -*- coding: utf-8 -*-
"""阈值敏感性分析：|涨跌|>=X% 阈值从 1.5% 到 5% 扫描
评估 3% 是否合理：事件频率(会不会太滥/太稀)、样本量(够不够评估)、
基线分化度(信号强不强)、事件聚集性(样本独立性)、近10年样本量。
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
    # 日涨跌幅序列
    chgs = [(closes[i] / closes[i-1] - 1) * 100 for i in range(1, N)]
    print(f'样本: {N} 交易日 ({dates[0]} ~ {dates[-1]})')
    print(f'日涨跌幅分布: 均值 {statistics.mean(chgs):.3f}% | 标准差 {statistics.stdev(chgs):.3f}%')
    for p in (50, 75, 90, 95, 99, 99.5):
        print(f'  P{p}: {sorted(chgs)[int(len(chgs)*p/100)]:.2f}%')
    print(f'  单日最大涨 {max(chgs):.1f}% | 最大跌 {min(chgs):.1f}%')
    # 3% ≈ 几倍标准差
    sd = statistics.stdev(chgs)
    print(f'  3% ≈ {3/sd:.1f}σ')

    print('\n── 阈值扫描 ──')
    print(f'{"阈值":>5} | {"大涨次数":>6} | {"大跌次数":>6} | {"合计":>5} | {"占比":>6} | {"约每年":>6} | {"大涨后5日涨":>10} | {"大跌后5日涨":>10} | {"分化":>5}')
    for th in (1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0):
        up = [(i, c) for i, c in enumerate(chgs) if c >= th]
        dn = [(i, c) for i, c in enumerate(chgs) if c <= -th]
        def prob(ev, win=5):
            ups = tot = 0
            for i, c in ev:
                j = i + 1 + win
                if j < len(closes):
                    tot += 1
                    if closes[j] > closes[i+1]:
                        ups += 1
            return ups/tot*100 if tot else float('nan')
        pu = prob(up); pd_ = prob(dn)
        years = (N) / 250
        print(f'{th:>5.1f} | {len(up):>6} | {len(dn):>6} | {len(up)+len(dn):>5} | {(len(up)+len(dn))/N*100:>5.2f}% | {(len(up)+len(dn))/years:>5.1f} | {pu:>9.1f}% | {pd_:>9.1f}% | {abs(pu-pd_):>4.1f}')

    # 事件聚集性（3%）：相邻事件间隔
    ev_idx = sorted([i+1 for i, c in enumerate(chgs) if abs(c) >= 3.0])
    gaps = [ev_idx[k+1] - ev_idx[k] for k in range(len(ev_idx)-1)]
    if gaps:
        print(f'\n3% 事件相邻间隔: 中位数 {statistics.median(gaps)} 交易日 | 最小 {min(gaps)} | 最大 {max(gaps)}')

    # 近10年（2016-01-01 起）
    s2016 = [i for i, d in enumerate(dates) if d >= '2016-01-01']
    if s2016:
        base = s2016[0]
        seg = chgs[base-1:]
        u16 = sum(1 for c in seg if c >= 3.0)
        d16 = sum(1 for c in seg if c <= -3.0)
        yrs16 = (len(dates) - base) / 250
        print(f'\n2016 以来（{yrs16:.1f} 年，{len(seg)} 交易日）: 涨≥3% {u16} 次 | 跌≥3% {d16} 次 | 合计 {u16+d16}（约每年 {(u16+d16)/yrs16:.1f} 次）')

if __name__ == '__main__':
    main()

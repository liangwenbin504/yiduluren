# -*- coding: utf-8 -*-
"""叙事优选层：多引擎叙事片段去重/按优先级排序/总长截断（不改评分）。"""


def narr_optimize(parts, total_max: int = 600) -> str:
    """parts: [(优先级 int, 文本), ...]。优先级高者在前；同文本去重；总长限 total_max。
    优先级约定：终局结论 50 / 合参 45 / 课体 40 / 毕法 35 / 时序 30 / 支上 25 /
    类神 20 / 古籍课例 18 / 方位 15 / 应期 12 / 六亲 10 / 射覆细节 8。"""
    seen = set()
    out = []
    for pri, t in parts:
        t = str(t or '').strip()
        if not t or t in seen:
            continue
        seen.add(t)
        out.append((pri, t))
    out.sort(key=lambda x: -x[0])
    res = []
    used = 0
    for pri, t in out:
        if used + len(t) <= total_max:
            res.append(t)
            used += len(t) + 1
        else:
            remain = total_max - used
            if remain > 24:
                res.append(t[:remain] + '…')
            break
    return '；'.join(res)


if __name__ == '__main__':
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    r = narr_optimize([(40, '课体元首'), (50, '终局判吉'), (40, '课体元首'), (8, '细节甲乙丙丁' * 30)])
    print(r)

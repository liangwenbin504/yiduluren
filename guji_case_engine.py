# -*- coding: utf-8 -*-
"""古籍课例检索（叙事佐证层，不参与评分）
索引 data/guji_case_index.json：疏正218+汇选183+指南78+叶飘然761 按干支/课体索引。
占课时附"同干支古籍案"佐证——最贴合"规则从实例生成"的叙事。"""
import json
import os

_ROOT = os.path.dirname(os.path.abspath(__file__))
_IDX = None


def _load():
    global _IDX
    if _IDX is None:
        try:
            with open(os.path.join(_ROOT, 'data', 'guji_case_index.json'), encoding='utf-8') as f:
                _IDX = json.load(f)
        except Exception:
            _IDX = {'by_ganzhi': {}, 'by_keti': {}}
    return _IDX


def guji_case_lookup(ri_gan: str, ri_zhi: str, keti: str = '', topn: int = 2) -> list:
    """检索同干支古籍课例（不足补同课体）。返回 [{'tag','ganzhi','zhanlei','label','叙事'}]。"""
    gz = str(ri_gan) + str(ri_zhi)
    idx = _load()
    if len(gz) != 2:
        return []
    same = [e for e in idx.get('by_ganzhi', {}).get(gz, [])]
    # 有方向标注者优先（叶飘然无 label 排后）
    same.sort(key=lambda e: (0 if e.get('label') else 1))
    picked = same[:topn]
    if len(picked) < topn and keti:
        for e in idx.get('by_keti', {}).get(str(keti), []):
            if e.get('ganzhi') != gz and e not in picked:
                picked.append(e)
            if len(picked) >= topn:
                break
    out = []
    for e in picked:
        lab = {'吉': '（原断吉）', '凶': '（原断凶）', '平': '（原断平）'}.get(e.get('label', ''), '')
        zl = e.get('zhanlei', '')
        out.append({
            'tag': e.get('tag', ''), 'ganzhi': e.get('ganzhi', ''), 'label': e.get('label', ''),
            '叙事': '[%s·%s%s]%s%s' % (e.get('tag', ''), e.get('ganzhi', ''), '·' + zl if zl else '', lab, e.get('brief', '')),
        })
    return out


if __name__ == '__main__':
    import io, sys
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    for g in ('辛卯', '戊寅', '乙卯'):
        r = guji_case_lookup(g[0], g[1])
        print(g, len(r), '条同干支案')
        for e in r[:2]:
            print('  ', e['叙事'][:80])

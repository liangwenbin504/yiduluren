# -*- coding: utf-8 -*-
"""前后端起课一致性全自动测试（2026-08-21 落地）。

架构（规避 Windows 沙箱下 python 客户端连续 HTTP 请求被杀的环境怪问题）：
  Phase A  采集：PowerShell 内联循环 + curl.exe 落盘（curl 已被验证稳定，96 连发 0 失败）
            -> _memory/_consist_data/{key}_qike.json + {key}_analyze.json
  Phase B  对比：纯本地 python 文件对比（无网络/无子进程），抓 qike × analyze 全字段差异
  Phase C  批量：curl 采集 batch + 逐候选 analyze，对比课体/三传/评分/评级

检测维度（前端真实渲染字段）：
  天地盘 tiandi_pan、四课 sike(含天将列)、三传(初/中/末)、三传干支/天将/六亲、
  课体、课格列表、毕法赋命中、综合评分、评级。

用法：
  python auto_consistency_test.py            # 全流程（采集+对比）
  python auto_consistency_test.py --compare-only   # 仅对比已采集数据
历史修复（本测试抓出的真实口径分裂）：
  1. qike 四课缺天将列（analyze 有）→ 补 _tj_ys.get(k[1],'')
  2. qike 毕法走内联 _BFD().detect，analyze 走 judge_orchestrator → 统一到 judge_all
  3. judge_orchestrator 对 y=0 无效日期调 sxtwl.fromSolar(0,0,0) → 农历月错乱(11月→冬) → 季节法毕法分裂 → 加 y>0 守卫
  4. qike 增加可选 date 参数，有日期则用真实农历月季节（与 analyze 完全同口径）
"""
import sys, io, os, json, subprocess, collections, urllib.parse

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, '_memory', '_consist_data')
TASKS = os.path.join(ROOT, '_memory', '_tasks.json')
BASE = 'http://127.0.0.1:5555'

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

DATES = ['2026-08-01','2026-08-04','2026-08-07','2026-08-10','2026-08-13','2026-08-16','2026-08-19','2026-08-22']
MOUNTAINS = ['壬', '子']
SHICHENS = ['子','寅','辰','午','申','戌']


def gen_tasks():
    """本地引擎算四柱/月将 → 任务清单 JSON。"""
    sys.path.insert(0, ROOT)
    from engine.sizhu_engine import get_sizhu
    from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen
    eng = DaLiuRenLuMaGuiRen()
    tasks = []
    for ds in DATES:
        y, m, d = int(ds[:4]), int(ds[5:7]), int(ds[8:10])
        for mtn in MOUNTAINS:
            for sc in SHICHENS:
                sizhu = get_sizhu(y, m, d, sc)
                rg, rz = sizhu['日柱'][0], sizhu['日柱'][1]
                yj = eng.get_yuejiang_by_date(y, m, d)
                tasks.append({'key': ds.replace('-','') + '_' + mtn + '_' + sc,
                              'date': ds, 'mountain': mtn, 'shichen': sc,
                              'ri_gan': rg, 'ri_zhi': rz, 'yue_jiang': yj})
    with open(TASKS, 'w', encoding='utf-8') as f:
        json.dump(tasks, f, ensure_ascii=False)
    print(f'[A] 任务清单 {len(tasks)} 组 → {TASKS}')


def fetch_all():
    """PowerShell 内联 + curl 采集（规避 python 客户端网络被杀）。"""
    os.makedirs(DATA, exist_ok=True)
    ps = r'''
$tasks = Get-Content '__TASKS__' -Raw -Encoding UTF8 | ConvertFrom-Json
$out = '__DATA__'
$n = 0
foreach ($t in $tasks) {
  $qkF = Join-Path $out ($t.key + '_qike.json')
  $anF = Join-Path $out ($t.key + '_analyze.json')
  if ((Test-Path $qkF) -and (Test-Path $anF)) { continue }
  $u1 = 'http://127.0.0.1:5555/api/qike?ri_gan=' + [uri]::EscapeDataString($t.ri_gan) + '&ri_zhi=' + [uri]::EscapeDataString($t.ri_zhi) + '&yue_jiang=' + [uri]::EscapeDataString($t.yue_jiang) + '&shi_chen=' + [uri]::EscapeDataString($t.shichen) + '&date=' + $t.date
  curl.exe -s -m 120 -o $qkF $u1
  $u2 = 'http://127.0.0.1:5555/api/zeri/analyze?date=' + $t.date + '&mountain=' + [uri]::EscapeDataString($t.mountain) + '&shichen=' + [uri]::EscapeDataString($t.shichen)
  curl.exe -s -m 300 -o $anF $u2
  $n++
  if (($n % 20) -eq 0) { Write-Host ('[A] fetched ' + $n) }
}
Write-Host ('[A] fetch done +' + $n)
'''.replace('__TASKS__', TASKS).replace('__DATA__', DATA)
    r = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-Command', ps],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1800)
    print(r.stdout)
    if r.stderr.strip():
        print('[A] stderr:', r.stderr[:400])


def compare_qike_analyze():
    files = sorted(f for f in os.listdir(DATA) if f.endswith('_analyze.json'))
    diff_fields = collections.Counter()
    examples = []
    checked = ok_pairs = load_errs = 0

    def load(p):
        with open(os.path.join(DATA, p), 'r', encoding='utf-8') as f:
            return json.load(f)

    for an_f in files:
        key = an_f[:-len('_analyze.json')]
        try:
            q, a = load(key + '_qike.json'), load(an_f)
        except Exception:
            load_errs += 1
            continue
        qd, qsc = (q.get('data') or {}), (q.get('data') or {}).get('sanchuan') or {}
        asc = a.get('sanchuan') or {}
        checked += 1
        pairs = [
            ('天地盘', qd.get('tiandi_pan'), a.get('tiandi_pan')),
            ('四课(含天将)', qd.get('sike'), a.get('sike')),
            ('三传(初/中/末)', [qsc.get('初传'), qsc.get('中传'), qsc.get('末传')],
                               [asc.get('初传'), asc.get('中传'), asc.get('末传')]),
            ('三传干支', qsc.get('三传干支'), asc.get('三传干支')),
            ('三传天将', qsc.get('三传天将'), asc.get('三传天将')),
            ('三传六亲', qsc.get('三传六亲'), asc.get('三传六亲')),
            ('课体', qsc.get('课体'), asc.get('课体')),
            ('课格列表', sorted(qsc.get('课格列表') or []), sorted(asc.get('课格列表') or [])),
            ('毕法赋命中', sorted(qsc.get('毕法赋命中') or []), sorted(asc.get('毕法赋命中') or [])),
        ]
        cur = []
        for fname, qv, av in pairs:
            if qv != av:
                diff_fields[fname] += 1
                if len(examples) < 8:
                    examples.append((key, fname, qv, av))
                cur.append(fname)
        if not cur:
            ok_pairs += 1

    print(f'[B] qike × analyze 对比 {checked} 组：一致 {ok_pairs}  加载失败 {load_errs}')
    if diff_fields:
        print(f'[B] ❌ 不一致字段: {dict(diff_fields)}')
        for key, fname, qv, av in examples:
            print(f'  [{fname}] {key}')
            print(f'    qike    : {json.dumps(qv, ensure_ascii=False)[:140]}')
            print(f'    analyze : {json.dumps(av, ensure_ascii=False)[:140]}')
        return False
    print('[B] ✅ qike × analyze 全部一致（天地盘/四课/三传/干支/天将/六亲/课体/课格/毕法）')
    return True


def compare_batch_analyze():
    """批量候选 × 单课分析（curl 采集 + 本地对比）。"""
    OUT = os.path.join(ROOT, '_memory', '_batch_cmp')
    os.makedirs(OUT, exist_ok=True)
    body = json.dumps({'start_date': '2026-08-01', 'end_date': '2026-08-22',
                       'mountain': '壬', 'zetiri_type': '安葬', 'jiri_count': 60, 'min_liuren': 0},
                      ensure_ascii=False)
    bf = os.path.join(OUT, 'batch.json')
    bbody = os.path.join(OUT, '_batch_body.json')
    with open(bbody, 'w', encoding='utf-8') as f:
        f.write(body)
    ps = r'''
$bb = '%s'
$bf = '%s'
curl.exe -s -m 600 -X POST -H 'Content-Type: application/json' --data-binary "@$bb" -o $bf 'http://127.0.0.1:5555/api/zeri/batch'
$j = Get-Content $bf -Raw -Encoding UTF8 | ConvertFrom-Json
if ($j.error) { Write-Host ('[C] batch ERR: ' + $j.error); exit 1 }
$res = @($j.results)
Write-Host ('[C] 批量候选 ' + $res.Count)
$i = 0
foreach ($it in $res) {
  $af = Join-Path '%s' ('an2_' + $i + '.json')
  curl.exe -s -m 300 -o $af ('http://127.0.0.1:5555/api/zeri/analyze?date=' + $it.date + '&mountain=' + [uri]::EscapeDataString('壬') + '&shichen=' + [uri]::EscapeDataString($it.shichen))
  $i++
}
Write-Host ('[C] fetched ' + $i)
''' % (bbody.replace("'", "''"), bf, OUT)
    r = subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-Command', ps],
                       capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=1800)
    print(r.stdout)
    if r.stderr.strip():
        print('[C] stderr:', r.stderr[:400])
    with open(bf, 'r', encoding='utf-8') as f:
        bres = json.load(f)
    results = bres.get('results') or []

    def load(p):
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)

    diff = collections.Counter()
    examples = []
    for i, it in enumerate(results):
        an = load(os.path.join(OUT, f'an2_{i}.json'))
        asc = an.get('sanchuan') or {}
        bsc = it.get('sanchuan') or {}
        pairs = [
            ('课体', it.get('keti'), asc.get('课体')),
            ('三传', [bsc.get('初传'), bsc.get('中传'), bsc.get('末传')],
                    [asc.get('初传'), asc.get('中传'), asc.get('末传')]),
            ('综合评分', it.get('total_score'), an.get('score')),
            ('评级', it.get('grade'), an.get('grade')),
        ]
        for fname, bv, av in pairs:
            if bv != av:
                diff[fname] += 1
                if len(examples) < 8:
                    examples.append((it.get('date'), it.get('shichen'), fname, bv, av))
    if diff:
        print(f'[C] ❌ 不一致: {dict(diff)}')
        for dt, sc, fname, bv, av in examples:
            print(f'  [{fname}] {dt} {sc}时 batch={bv} analyze={av}')
        return False
    print('[C] ✅ batch × analyze 全部一致（课体/三传/评分/评级）')
    return True


if __name__ == '__main__':
    compare_only = '--compare-only' in sys.argv
    if not compare_only:
        gen_tasks()
        fetch_all()
    r1 = compare_qike_analyze()
    r2 = compare_batch_analyze()
    print()
    print('═══ 前后端起课一致性测试 ═══')
    print('qike × analyze :', '✅ PASS' if r1 else '❌ FAIL')
    print('batch × analyze:', '✅ PASS' if r2 else '❌ FAIL')
    sys.exit(0 if (r1 and r2) else 1)

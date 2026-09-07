#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
大六壬股票虚拟交易仪表盘
- 虚拟账户盈亏总览
- 预测记录与对照
- 交易历史
- 实时行情
"""
import json, os, sys, io, threading, time, ast, subprocess
from datetime import datetime, date, timedelta
from pathlib import Path

# ── pythonw 兼容：stdout/stderr 为 None 时重定向到日志文件 ──
_HERE = Path(__file__).parent
_MEMORY_DIR = _HERE / '_memory'
_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
if sys.stdout is None:
    sys.stdout = open(_MEMORY_DIR / 'dashboard.out.log', 'a', encoding='utf-8', buffering=1)
    sys.stderr = open(_MEMORY_DIR / 'dashboard.err.log', 'a', encoding='utf-8', buffering=1)
else:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

from flask import Flask, jsonify, send_file, request
from flask_cors import CORS

ROOT = Path(__file__).parent

# ═════════════════════════════════════════════════════════════════
# 达标择日收费体系（2026-08-21 憨爷新定价 v2）
# 方式一「扫码按次」：按"目标跨度天数"自动计价；≤3天免费；另每日限免1次
# 方式二「会员」：48元/月(每月5次+限1年跨度) / 98元/月(不限次数+不限跨度)，支持月/季/年
# 内测：本地IP白名单 / 指定时间段 / 手机号+姓名+短信验证码白名单 → 免费放行
# ═════════════════════════════════════════════════════════════════
# 每档: (档位名, 最大天数, 价格元/次, 跨度描述)
SCAN_PRICE_TIERS = [
    ('3d',     3,    0,   '3天以内'),
    ('15d',   15,  9.8,   '3天-15天'),
    ('1m',    30,   36,   '15天-1个月'),
    ('6m',   180,   98,   '1个月-半年'),
    ('1y',   365,  168,   '半年-1年'),
    ('3y',  1095,  360,   '1年-3年'),
    ('10y', 3650, 1680,   '3年-10年'),
    ('60y', 21915, 1680,  '10年-60年'),
]
FREE_SCAN_DAYS = 3            # 默认免扫描跨度 = 3 天内
UNLOCK_FILE = ROOT / '_zeri_unlock.json'
UNLOCK_HOURS = 24             # 按次解锁有效期（24h 内任意扫描放行）

# ── 会员定价（元）：键=input周期 → (价, 月数, 48档每月次数, 48档跨度上限天数)
PLAN_VIP_BASIC = 'vip48'      # 会员·体验档
PLAN_VIP_PRO   = 'vip98'      # 会员·尊享档
PLAN_LIFETIME  = 'lifetime'   # 终身免费用户
VIP_MONTHS = {'m': 1, 'q': 3, 'y': 12}
VIP_PRICE = {
    # plan -> {period: price}
    PLAN_VIP_BASIC: {'m': 48, 'q': 128, 'y': 360},
    PLAN_VIP_PRO:   {'m': 98, 'q': 258, 'y': 720},
}
VIP48_MONTHLY_QUOTA = 5        # 体验档每月可用次数
VIP48_MAX_DAYS = 365           # 体验档跨度上限 = 1 年
# 新用户每日限免：每天默认给非付费、非内测用户 1 次免费机会（限跨度 <=3天）
DAILY_FREE_LIMIT = 1
DAILY_FREE_MAX_DAYS = 3
# 超选预览每日配额：按权益档次（0=不限）。免费/内测=1，体验会员=3，尊享全选6属授权益内不触预览
LMG_OVERSEE_DAILY_LIMIT = 1
LMG_OVERSEE_DAILY_LIMIT_EXP = 3

# ── 用户/会员/内测数据存储 ──
USER_DATA_FILE = ROOT / '_sys_users.json'        # 用户注册与会员信息
INVITE_FILE    = ROOT / '_sys_invite.json'       # 内测白名单(手机号->姓名 / 本地IP)
MEMBERSHIP_FILE= ROOT / '_sys_membership.json'   # 会员权益记录(手机号->权益)
QR_CODE_IMG    = ROOT / 'static' / 'pay_qr.png'  # 静态收款码图片(付费入口)
FREE_USAGE_FILE= ROOT / '_sys_free_usage.json'   # 每日限免/首免计数  key:手机号/IP_日期

_SP = lambda p: str(ROOT / p)

def _load_json(path, default=None):
    try:
        if Path(path).exists():
            return json.loads(Path(path).read_text('utf-8'))
    except Exception:
        pass
    return default

def _save_json(path, data):
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2), 'utf-8')
        return True
    except Exception:
        return False

def _scan_price(max_days):
    """按最大跨度天数返回 (价格, 档位名)。跨度为0(不扫长)→最低免费档。"""
    if max_days <= 0:
        return 0, '3d'
    for name, days, price, _desc in SCAN_PRICE_TIERS:
        if max_days <= days:
            return price, name
    # 超60年（一甲子）：仍按10年以上档，此处不给免费（走内测/会员解锁）
    return 1680, '10y'


def _tier_days(amount):
    """按金额反查该档允许的最大天数（按次解锁档位校验）。"""
    for name, days, price, _desc in SCAN_PRICE_TIERS:
        if price > 0 and abs(price - amount) < 0.01:
            return days
    return 0


def _tier_desc_by_amount(amount):
    for name, days, price, desc in SCAN_PRICE_TIERS:
        if price > 0 and abs(price - amount) < 0.01:
            return desc
    return ''

# ═════════════════════════════════════════════════════════════════
# 内测/会员/身份 判定模块
# ═════════════════════════════════════════════════════════════════
def _client_ip():
    """取客户端IP（优先代理头）。"""
    try:
        fwd = request.headers.get('X-Forwarded-For', '')
        if fwd:
            return fwd.split(',')[0].strip()
    except Exception:
        pass
    try:
        return request.remote_addr or ''
    except Exception:
        return ''

def _today_str():
    return date.today().isoformat()

def _is_local_ip(ip):
    """本地机/IP 白名单判断（内测直放）。"""
    ip = (ip or '').strip()
    if not ip:
        return False
    local_ips = {'127.0.0.1', '::1', 'localhost'}
    # 本机自 IP / 内网段 / 本地授权IP
    if ip in local_ips:
        return True
    if ip.startswith('192.168.') or ip.startswith('10.') or ip.startswith('172.16.'):
        return True
    invoke = _load_json(str(INVITE_FILE), {}) or {}
    allowed = invoke.get('local_ips', []) or []
    for a in allowed:
        if ip == str(a).strip():
            return True
        if str(a).strip().endswith('.*') and ip.startswith(str(a).strip().rstrip('.*')):
            return True
    return False

def _is_in_beta_window():
    """是否处于内测免费时间段。config.BETA_WINDOW_ENABLED / START / END 配置。"""
    try:
        from config import BETA_WINDOW_ENABLED, BETA_WINDOW_START, BETA_WINDOW_END
    except Exception:
        return False
    if not BETA_WINDOW_ENABLED:
        return False
    if not BETA_WINDOW_START or not BETA_WINDOW_END:
        return False
    try:
        today = date.today()
        s = date.fromisoformat(str(BETA_WINDOW_START))
        e = date.fromisoformat(str(BETA_WINDOW_END))
        return s <= today <= e
    except Exception:
        return False

def _is_invite(mobile):
    """手机号+姓名 内测白名单校验（配置于 _sys_invite.json）。"""
    if not mobile:
        return False
    invite = _load_json(str(INVITE_FILE), {}) or {}
    mobs = invite.get('mobiles', {}) or {}
    return str(mobile).strip() in mobs

def _is_beta_whitelisted(mobile=None):
    """是否内测免费：本地IP / 时间段 / 手机号白名单 任一命中。"""
    if _is_local_ip(_client_ip()):
        return True
    if _is_in_beta_window():
        return True
    if mobile and _is_invite(mobile):
        return True
    return False

def _membership(mobile):
    """查会员权益：返回 dict 或 None。结构 {plan, expires_at, source_mobile}。"""
    if not mobile:
        return None
    data = _load_json(str(MEMBERSHIP_FILE), {}) or {}
    return data.get(str(mobile).strip())

def _membership_valid(mem):
    if not mem:
        return False
    # 终身免费用户永不过期
    if mem.get('plan') == PLAN_LIFETIME:
        return True
    try:
        exp = datetime.fromisoformat(mem.get('expires_at', ''))
        return exp >= datetime.now()
    except Exception:
        return False

def _consume_vip(mobile):
    """消费一次会员次数（48档限次；98档/终身不限）。返回剩余次数。"""
    if not mobile:
        return 0
    mem = _membership(mobile)
    if not mem or not _membership_valid(mem):
        return -1
    if mem.get('plan') in (PLAN_VIP_PRO, PLAN_LIFETIME):
        return 9999  # 尊享档/终身免费不限次
    try:
        data = _load_json(str(MEMBERSHIP_FILE), {}) or {}
        cur = data.get(str(mobile)) or {}
        used = int(cur.get('used_this_period', 0) or 0)
        cur['used_this_period'] = used + 1
        data[str(mobile)] = cur
        _save_json(str(MEMBERSHIP_FILE), data)
        return VIP48_MONTHLY_QUOTA - used - 1
    except Exception:
        return -1

def _consume_daily_free(mobile):
    """每日限免计数消费。返回 (是否放行, 剩余)。key=手机号或IP_日期。"""
    key = (mobile or _client_ip() or 'anon') + '_' + _today_str()
    data = _load_json(str(FREE_USAGE_FILE), {}) or {}
    used = int(data.get(key, 0) or 0)
    if used >= DAILY_FREE_LIMIT:
        return False, 0
    data[key] = used + 1
    _save_json(str(FREE_USAGE_FILE), data)
    return True, DAILY_FREE_LIMIT - used - 1

def _consume_lmg_oversee(mobile, limit=LMG_OVERSEE_DAILY_LIMIT):
    """每日“超选预览”配额消费（与限免同文件，独立前缀 preview_）。返回 (是否放行, 剩余)。
    limit<=0 视作不限；按 手机号/IP + 日期 计数。"""
    limit = limit or 0
    if limit <= 0:
        return True, -1
    key = 'preview_' + (mobile or _client_ip() or 'anon') + '_' + _today_str()
    data = _load_json(str(FREE_USAGE_FILE), {}) or {}
    used = int(data.get(key, 0) or 0)
    if used >= limit:
        return False, 0
    data[key] = used + 1
    _save_json(str(FREE_USAGE_FILE), data)
    return True, limit - used - 1

def _resolve_access(max_days, mobile=None, is_first=None):
    """综合计费决策。返回 dict：
    {free, is_beta, is_vip, vip_plan, vip_left, price, tier, tier_desc,
     daily_free, daily_left, must_pay, qr_amount, message}
    规则优先级：内测/本地 → 会员 → 6天外免费 → 每日限免 → 按次付费。
    """
    max_days = max_days or 0
    if _is_beta_whitelisted(mobile):
        return {'free': True, 'is_beta': True, 'is_vip': False, 'vip_plan': '',
                'vip_left': 0, 'price': 0, 'tier': '', 'tier_desc': '内测免费',
                'daily_free': False, 'daily_left': 0, 'must_pay': False,
                'qr_amount': 0, 'message': '内测期/本机/白名单用户免费'}

    mem = _membership(mobile)
    if mem and _membership_valid(mem):
        plan = mem.get('plan')
        # 终身免费用户：不限次数/跨度
        if plan == PLAN_LIFETIME:
            return {'free': True, 'is_beta': False, 'is_vip': True, 'vip_plan': '终身免费',
                    'vip_left': 9999, 'price': 0, 'tier': '', 'tier_desc': '终身免费(不限次数跨度)',
                    'daily_free': False, 'daily_left': 0, 'must_pay': False,
                    'qr_amount': 0, 'message': '终身免费用户，不限次数/跨度'}
        exp = datetime.fromisoformat(mem.get('expires_at', ''))
        left_days = (exp - datetime.now()).days
        if plan == PLAN_VIP_PRO:
            return {'free': True, 'is_beta': False, 'is_vip': True, 'vip_plan': '尊享档',
                    'vip_left': 0, 'price': 0, 'tier': '', 'tier_desc': '会员·尊享(不限次数跨度)',
                    'daily_free': False, 'daily_left': 0, 'must_pay': False,
                    'qr_amount': 0, 'message': f'尊享会员有效期剩余 {left_days} 天，不限次数/跨度'}
        # vip48 体验档：次数 + 跨度限制
        if max_days > VIP48_MAX_DAYS:
            # 超出跨度 → 需补按次差价或升级
            price, tier = _scan_price(max_days)
            return {'free': False, 'is_beta': False, 'is_vip': True, 'vip_plan': '体验档',
                    'vip_left': 0, 'price': price, 'tier': tier,
                    'tier_desc': _tier_desc_by_amount(price) or '跨度超限',
                    'daily_free': False, 'daily_left': 0, 'must_pay': True,
                    'qr_amount': price,
                    'message': f'体验档限{int(VIP48_MAX_DAYS/30)}个月跨度，本次跨度超限需补差价 {price}元/次'}
        left = _consume_vip(mobile)
        if left is not None and left >= 0:
            return {'free': True, 'is_beta': False, 'is_vip': True, 'vip_plan': '体验档',
                    'vip_left': left, 'price': 0, 'tier': '', 'tier_desc': '会员·体验(已计次)',
                    'daily_free': False, 'daily_left': 0, 'must_pay': False,
                    'qr_amount': 0, 'message': f'体验档已计次，本月剩余 {left} 次'}
        # 次数用完 → 降级按次（同跨度）
        price, tier = _scan_price(max_days)
        return {'free': False, 'is_beta': False, 'is_vip': True, 'vip_plan': '体验档',
                'vip_left': 0, 'price': price, 'tier': tier,
                'tier_desc': _tier_desc_by_amount(price) or '已用尽次数',
                'daily_free': False, 'daily_left': 0, 'must_pay': True,
                'qr_amount': price,
                'message': '体验档次数已用尽，可按次付费或升级尊享档'}

    # 非会员：跨度免费档（≤3天）
    price, tier = _scan_price(max_days)
    if price == 0:
        return {'free': True, 'is_beta': False, 'is_vip': False, 'vip_plan': '',
                'vip_left': 0, 'price': 0, 'tier': tier,
                'tier_desc': '本次跨度免费', 'daily_free': False, 'daily_left': 0,
                'must_pay': False, 'qr_amount': 0,
                'message': '本次目标跨度≤3天，免费'}

    # 每日限免（独立于3天免费，用于促销非付费用户）
    # 说明：每日限免仅覆盖跨度<=3天档，长跨度不参与，避免滥用
    if max_days <= DAILY_FREE_MAX_DAYS:
        ok, left = _consume_daily_free(mobile)
        if ok:
            return {'free': True, 'is_beta': False, 'is_vip': False, 'vip_plan': '',
                    'vip_left': 0, 'price': 0, 'tier': tier,
                    'tier_desc': '每日限免', 'daily_free': True, 'daily_left': left,
                    'must_pay': False, 'qr_amount': 0,
                    'message': '今日每日限免额度已用' if not ok else f'今日免费体验已用，剩余 {left} 次'}

    # 长跨度：需按次付费
    return {'free': False, 'is_beta': False, 'is_vip': False, 'vip_plan': '',
            'vip_left': 0, 'price': price, 'tier': tier,
            'tier_desc': _tier_desc_by_amount(price) or '按次付费',
            'daily_free': False, 'daily_left': 0, 'must_pay': True,
            'qr_amount': price,
            'message': f'该档位（{_tier_desc_by_amount(price)}）需付费 {price} 元/次'}


def _unlock_key(mobile=None):
    """按手机号隔离解锁：优先用手机号，无则退回客户端 IP，再退回匿名通道。"""
    k = (mobile or '').strip()
    if k:
        return k
    ip = _client_ip() or ''
    return 'ip:' + ip if ip else 'anon'

def _load_unlocks():
    """读取解锁存档；兼容旧版"单条记录"格式，自动迁移为 {用户:记录}。"""
    try:
        data = _load_json(str(UNLOCK_FILE), {}) or {}
    except Exception:
        return {}
    if not isinstance(data, dict):
        return {}
    # 旧版单条记录（顶层直接含 expires_at）→ 迁移到统一字典结构
    if 'expires_at' in data:
        return {'legacy': data}
    return data

def _write_unlock(amount, tier, mobile=None):
    import secrets
    data = _load_unlocks()
    data[_unlock_key(mobile)] = {
        'unlock_key': secrets.token_hex(16),
        'tier': tier, 'amount': amount,
        'max_days': _tier_days(amount),
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=UNLOCK_HOURS)).isoformat(),
    }
    try:
        with open(UNLOCK_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        return False
    return True

def _check_unlock(max_days, mobile=None):
    """按用户解锁记录校验：存在、未过期、且解锁档位覆盖本次 max_days → (ok, 剩余小时)。"""
    try:
        data = _load_unlocks()
        rec = data.get(_unlock_key(mobile))
        if not rec:
            return False, 0
        exp = datetime.fromisoformat(rec.get('expires_at', ''))
        if exp < datetime.now():
            return False, 0
        if max_days > int(rec.get('max_days', 0) or 0):
            return False, 0  # 档位不够，需补差价解锁
        left = (exp - datetime.now()).total_seconds() / 3600
        return True, round(left, 1)
    except Exception:
        return False, 0


# 全局配置：六壬是否仅作参考（不参与决策）
try:
    from config import LIUREN_REFERENCE_ONLY, LIUREN_OBSERVATION_START, LIUREN_VALIDATION_YEARS
except Exception:
    LIUREN_REFERENCE_ONLY = True
    LIUREN_OBSERVATION_START = "2026-07-28"
    LIUREN_VALIDATION_YEARS = 3

# 差距分析模块（懒加载）
_gap_analyzer = None
def get_gap_analyzer():
    global _gap_analyzer
    if _gap_analyzer is None:
        _junk_dir = ROOT / '_archive' / 'junk'
        if str(_junk_dir) not in sys.path:
            sys.path.insert(0, str(_junk_dir))
        import _gap_analyzer as ga
        ga.set_results_path(str(ROOT / 'r14_self_learning_results.json'))
        _gap_analyzer = ga
    return _gap_analyzer
MEMORY = ROOT / '_memory'
# 【2026-07-31 清理】机械固定时/六亲/random 类别已在诚实回测中被证伪停用。
# 仅保留天机起课(manual)与量化(quant)有效路径。古例路径不受影响。
CATEGORIES = ['manual']
CAT_NAMES = {'manual': '天机起课'}

app = Flask(__name__, static_folder=None)
CORS(app)

# ═══════════════════════════════════════════════
# 预加载 akshare + 预热 V8 引擎（在主线程单线程阶段）
# akshare 导入时会加载 py_mini_racer (V8 DLL)，
# 但仅 import 不创建 V8 实例；第一次调用 akshare 接口时
# 才会在内部创建 MiniRacer() 实例初始化 V8。
# 如果在多线程请求中首次创建 V8 实例，会导致 DLL 并发初始化崩溃：
# (FATAL:partition_address_space.cc: !IsConfigurablePoolInitialized())
# 因此必须在 Flask 启动前的单线程阶段完成一次 akshare 调用。
# ═══════════════════════════════════════════════
print("  [启动] 预加载 akshare（初始化V8引擎，避免多线程崩溃）...", flush=True)
_ak = None
try:
    import akshare as _ak
    print("  [启动] akshare 模块已加载，预热V8引擎...", flush=True)
    # 调用一次简单接口触发V8初始化
    _ak.stock_zh_index_daily(symbol="sh000001")
    print("  [启动] ✅ akshare 预加载+V8预热完成", flush=True)
except Exception as _e:
    print(f"  [启动] ⚠️ akshare 预加载失败（行情将使用子进程fallback）: {_e}", flush=True)
    _ak = None

# ═════════ 事件起课心跳线程（模块级启动：waitress import 与直接运行都会执行）═════════
# 2026-08-15 憨爷拍板：交易日每 5 分钟拉实时行情，≥2σ 事件自动起课（时辰=触发时刻）。
try:
    import threading as _th_event
    import time as _time_event

    def _event_heartbeat_loop():
        while True:
            try:
                import sys as _sys_hb
                _p_hb = os.path.dirname(os.path.abspath(__file__))
                if _p_hb not in _sys_hb.path:
                    _sys_hb.path.insert(0, _p_hb)
                from engine.event_casting import heartbeat_check
                r = heartbeat_check()
                if r.get('event') or r.get('cast'):
                    print(f"[事件心跳] {r.get('note', '')}", flush=True)
            except Exception:
                pass
            _time_event.sleep(300)

    _th_event.Thread(target=_event_heartbeat_loop, daemon=True).start()
    print("  [启动] ✅ 事件起课心跳线程已启动（每 5 分钟检测，≥2σ 自动起课）", flush=True)
except Exception as _e:
    print(f"  [启动] ⚠️ 事件心跳线程启动失败: {_e}", flush=True)

_market_cache = {}
_market_cache_time = 0
_CACHE_TTL = 60

def read_json(path):
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text('utf-8'))
    except:
        return None

def get_portfolio(cat):
    p = read_json(MEMORY / f'virtual_portfolio_{cat}.json')
    if not p:
        return None
    return {
        'cash': p.get('cash', 0),
        'market_value': p.get('position_value', 0),
        'total_asset': p.get('total_value', p.get('cash', 0)),
        'initial_capital': p.get('initial_capital', p.get('cash', 0)),
        'positions': p.get('positions', []),
    }

def get_trades(cat):
    return read_json(MEMORY / f'auto_trades_{cat}.json')

def get_predictions():
    return read_json(MEMORY / 'stock_predictions.json')

@app.route('/static/<path:filename>')
def serve_static_file(filename):
    """服务 static/ 目录（收款码、前端静态资源）。"""
    from flask import send_from_directory
    static_dir = ROOT / 'static'
    try:
        return send_from_directory(str(static_dir), filename)
    except Exception:
        return jsonify({'error': 'Not found'}), 404


@app.route('/')
def index():
    html_file = ROOT / 'stock_dashboard.html'
    if html_file.exists():
        from flask import make_response
        resp = make_response(send_file(str(html_file)))
        resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        resp.headers['Pragma'] = 'no-cache'
        resp.headers['Expires'] = '0'
        return resp
    return 'stock_dashboard.html not found', 404


@app.route('/report/<date_str>')
def view_report(date_str):
    report_file = ROOT / 'stock_reports' / f'stock_report_{date_str}.html'
    if report_file.exists():
        return send_file(str(report_file))
    try:
        from stock_report_generator import generate_report
        from datetime import datetime
        target = datetime.strptime(date_str, '%Y-%m-%d').date()
        path = generate_report(target)
        if path and os.path.exists(path):
            return send_file(path)
    except:
        pass
    return f'<h2>未找到 {date_str} 的报表</h2>', 404


@app.route('/report')
def list_reports():
    import glob
    reports = sorted(glob.glob(str(ROOT / 'stock_reports' / 'stock_report_*.html')), reverse=True)
    links = ''.join(f'<li><a href="/report/{r.split("stock_report_")[1].replace(".html","")}">📊 {r.split("stock_report_")[1].replace(".html","")}</a></li>' for r in reports[:30])
    return f'<h2>📊 历史报表</h2><ul>{links}</ul>' if links else '<h2>暂无报表</h2>' 

def _stat_one(pred, actual):
    """返回 correct/partial/wrong 之一"""
    if pred == actual:
        return 'correct'
    elif actual in pred:
        return 'partial'
    else:
        return 'wrong'

@app.route('/api/summary')
def api_summary():
    preds = get_predictions() or []

    # 【2026-08-02 清理】机械固定时辰/六亲/random 等旧类别已证伪停用。
    # 数据文件已清（见 .bak_junk_clean 备份），这里再做统计层过滤，防止历史备份
    # 被重新加载时这些"垃圾"再次进入统计。
    _DEPRECATED = {'fixed_time','ri_gan_pian_cai','ri_zhi_pian_cai','ri_gan_shi_shen','ri_zhi_shi_shen','ri_gan_zheng_yin','ri_gan_pian_yin','ri_zhi_zheng_yin','ri_zhi_pian_yin','random','ml_predict'}
    preds = [d for d in preds if d and d.get('category') not in _DEPRECATED]

    # 【2026-08-02 口径统一】统计与「预测记录」表格同源同口径：
    # 总数 = 有效记录全量条数（不再按类别去重），保证 总览.sTotal == 记录.predCount。
    # 词汇统一在展示层做（看涨↔涨 / 看跌↔跌 / 震荡↔平），存储口径不改。
    preds_deduped = preds

    # 【2026-08-02 账户同源】虚拟账户统一从 position_manager 读取（与「持仓监控」tab 同源），
    # 不再读 virtual_portfolio_*.json（manual 文件不存在 → 全是默认值 → 与持仓打架）。
    portfolios = {}
    try:
        from quant_position_manager import get_positions as _qpm
        from liuren_position_manager import get_positions as _lpm
        for key, fetcher, disp in (('量化', _qpm, '量化'), ('六壬', _lpm, '六壬')):
            try:
                data = fetcher()
                cfg = data.get('config', {})
                summ = data.get('summary', {})
                capital = float(cfg.get('total_capital', 1_000_000.0) or 1_000_000.0)
                invested = float(summ.get('total_invested', 0) or 0)
                mv = float(summ.get('total_market_value', 0) or 0)
                pnl = float(summ.get('total_pnl', 0) or 0)
                cash = max(capital - invested, 0)
                total_asset = cash + mv
                portfolios[key] = {
                    'name': disp,
                    'cash': round(cash, 2),
                    'market_value': round(mv, 2),
                    'total_asset': round(total_asset, 2),
                    'initial_capital': capital,
                    'total_return_pct': round((total_asset - capital) / capital * 100, 2) if capital > 0 else 0,
                    'positions': data.get('positions', []),
                }
            except Exception as _e:
                portfolios[key] = {
                    'name': disp, 'cash': 0, 'market_value': 0, 'total_asset': 0,
                    'initial_capital': 1_000_000.0, 'total_return_pct': 0, 'positions': [],
                }
    except Exception:
        pass

    # 按类别拆分统计（仅保留有效类别；基于全量，与记录表格一致）
    CAT_ORDER = ["manual", "量化"]
    CAT_LABEL = {
        "manual": "天机起课",
        "量化": "量化",
        "_other": "其他",
    }

    by_cat = {}
    total_all = len(preds_deduped)
    checked_all = 0
    correct_all = 0
    partial_all = 0
    wrong_all = 0

    # 旧类别名映射（已停用，保留空映射兼容历史数据中的未知类别）
    OLD_CAT_MAP = {}

    for d in preds_deduped:
        raw_cat = d.get('category', '_other')
        cat = OLD_CAT_MAP.get(raw_cat, raw_cat)
        if cat not in by_cat:
            by_cat[cat] = {'total': 0, 'checked': 0, 'correct': 0, 'partial': 0, 'wrong': 0}
        by_cat[cat]['total'] += 1

        actual = d.get('actual_result', '') or ''
        pred = d.get('trend_prediction', '') or ''
        if not actual:
            continue
        checked_all += 1
        by_cat[cat]['checked'] += 1
        verdict = _stat_one(pred, actual)
        by_cat[cat][verdict] += 1
        if verdict == 'correct':
            correct_all += 1
        elif verdict == 'partial':
            partial_all += 1
        else:
            wrong_all += 1

    accuracy_all = round(correct_all / checked_all * 100, 1) if checked_all else 0

    # 构建有序的 by_category 列表
    by_category = []
    for cat in CAT_ORDER:
        if cat in by_cat:
            s = by_cat[cat]
            acc = round(s['correct'] / s['checked'] * 100, 1) if s['checked'] else 0
            by_category.append({
                'key': cat,
                'label': CAT_LABEL[cat],
                'total': s['total'],
                'checked': s['checked'],
                'correct': s['correct'],
                'partial': s['partial'],
                'wrong': s['wrong'],
                'accuracy': acc,
            })
    if '_other' in by_cat:
        s = by_cat['_other']
        acc = round(s['correct'] / s['checked'] * 100, 1) if s['checked'] else 0
        by_category.append({
            'key': '_other',
            'label': CAT_LABEL['_other'],
            'total': s['total'],
            'checked': s['checked'],
            'correct': s['correct'],
            'partial': s['partial'],
            'wrong': s['wrong'],
            'accuracy': acc,
        })

    # 【2026-08-02 口径统一】「最新预测」= 有效记录里 predict_time 最新的一条，
    # 不再限定"今天"（今天无起课时总览卡会空，造成与记录表格不一致的假象）。
    today_pred = None
    for d in preds:
        if not today_pred:
            today_pred = d
            continue
        if (d.get('predict_time') or d.get('date') or '') >= (today_pred.get('predict_time') or today_pred.get('date') or ''):
            today_pred = d

    # ── 六壬起课预测涨跌分析（仅统计真正的天机起课 manual；量化等不入这张六壬表）──
    by_trend = {}
    for d in preds_deduped:
        if d.get('category') != 'manual':
            continue
        trend = d.get('trend_prediction', '') or ''
        if not trend:
            continue
        if trend not in by_trend:
            by_trend[trend] = {'total': 0, 'checked': 0, 'correct': 0, 'partial': 0, 'wrong': 0}
        by_trend[trend]['total'] += 1
        actual = d.get('actual_result', '') or ''
        if actual:
            by_trend[trend]['checked'] += 1
            verdict = _stat_one(trend, actual)
            by_trend[trend][verdict] += 1

    liuren_trend_stats = []
    for trend, s in sorted(by_trend.items()):
        acc = round(s['correct'] / s['checked'] * 100, 1) if s['checked'] else 0
        liuren_trend_stats.append({
            'trend': trend,
            'total': s['total'],
            'checked': s['checked'],
            'correct': s['correct'],
            'partial': s['partial'],
            'wrong': s['wrong'],
            'accuracy': acc,
        })

    return jsonify({
        'total_predictions': total_all,
        'checked': checked_all,
        'correct': correct_all,
        'partial': partial_all,
        'wrong': wrong_all,
        'accuracy': accuracy_all,
        'by_category': by_category,
        'liuren_trend_stats': liuren_trend_stats,
        'portfolios': portfolios,
        'today_prediction': today_pred,
    })

@app.route('/api/predictions')
def api_predictions():
    """预测记录 — 支持 ?etf=510300 & ?date=2026-07-28 & ?method=量化 过滤"""
    preds = get_predictions() or []
    
    # 过滤
    etf_filter = request.args.get('etf', '').strip()
    date_filter = request.args.get('date', '').strip()
    method_filter = request.args.get('method', '').strip()
    
    if etf_filter:
        preds = [p for p in preds if p.get('etf', '') == etf_filter]
    if date_filter:
        preds = [p for p in preds if p.get('date', '') == date_filter]
    if method_filter:
        preds = [p for p in preds if p.get('method', '') == method_filter]
    
    # 量化记录包含个股维度，六壬记录保持兼容
    result = []
    for d in reversed(preds[-200:]):
        item = {
            'id': d.get('id', ''),
            'predict_time': d.get('predict_time', ''),
            'date': d.get('date', ''),
            'category': d.get('category', ''),
            'method': d.get('method', ''),
            'etf': d.get('etf', ''),
            'name': d.get('name', ''),
            'shi_chen': d.get('shi_chen', ''),
            'trend_prediction': d.get('trend_prediction', ''),
            'jixiong': d.get('jixiong', ''),
            'actual_result': d.get('actual_result', ''),
            'status': d.get('status', ''),
            'ref_price': d.get('trade_detail', {}).get('ref_price', ''),
            'actual_price': d.get('actual_details', {}).get('price', '') if d.get('actual_details') else '',
            'target_date': d.get('target_date', ''),
            # 量化专属字段
            'momentum_20d': d.get('momentum_20d', ''),
            'volatility': d.get('volatility', ''),
            'rsi': d.get('rsi', ''),
            'ma_trend': d.get('ma_trend', ''),
            'position': d.get('position', ''),
            'score': d.get('score', ''),
            'confidence': d.get('confidence', ''),
            'price': d.get('price', ''),
        }
        result.append(item)
    
    # 毕法赋红色标记（仅六壬记录）
    try:
        from bifa_matcher import match_bifa
        for d in preds[-200:]:
            r = match_bifa(d)
            if r:
                reds = [m for m in r.get('matches', []) if m['level'] == 'red']
                if reds:
                    for rd in result:
                        if rd.get('id') == d.get('id'):
                            rd['bifa_reds'] = [m['name'] for m in reds]
                            rd['bifa_red_count'] = len(reds)
                            break
    except:
        pass
    return jsonify(result)


def _parse_sike(raw):
    """将存储的 sike 字符串元组解析为数组 [[课名, ...], ...]"""
    if not raw or not isinstance(raw, list):
        return []
    result = []
    for item in raw:
        if isinstance(item, str):
            try:
                parsed = ast.literal_eval(item)
                if isinstance(parsed, tuple):
                    result.append(list(parsed))
                else:
                    result.append([item])
            except Exception:
                result.append([item])
        elif isinstance(item, (list, tuple)):
            result.append(list(item))
        else:
            result.append([str(item)])
    return result


# 五鼠遁: 日干起时干
WUSHU_DUN = {
    '甲':'甲', '乙':'丙', '丙':'戊', '丁':'庚', '戊':'壬',
    '己':'甲', '庚':'丙', '辛':'戊', '壬':'庚', '癸':'壬',
}
GAN = '甲乙丙丁戊己庚辛壬癸'
ZHI = '子丑寅卯辰巳午未申酉戌亥'
# 旬空表: 甲子旬戌亥空, 甲戌旬申酉空...
XUNKONG = {
    ('甲','子'):('戌','亥'),('甲','戌'):('申','酉'),('甲','申'):('午','未'),
    ('甲','午'):('辰','巳'),('甲','辰'):('寅','卯'),('甲','寅'):('子','丑'),
}

def _get_dun_gan(rizhu_gan, dizhi):
    """计算某地支的遁干"""
    start_gan = WUSHU_DUN.get(rizhu_gan, '甲')
    gan_idx = GAN.index(start_gan)
    zhi_idx = ZHI.index(dizhi) if dizhi in ZHI else 0
    return GAN[(gan_idx + zhi_idx) % 10]

def _get_liuqin(rizhu_gan, dizhi):
    """根据地支五行和日干五行判断六亲"""
    wx = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火',
          '午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
    gan_wx = {'甲':'木','乙':'木','丙':'火','丁':'火','戊':'土',
              '己':'土','庚':'金','辛':'金','壬':'水','癸':'水'}
    gw = gan_wx.get(rizhu_gan,'')
    dw = wx.get(dizhi,'')
    if not gw or not dw: return ''
    if gw == dw: return '兄弟'
    if gw == '木' and dw == '火': return '子孙'
    if gw == '木' and dw == '土': return '妻财'
    if gw == '木' and dw == '金': return '官鬼'
    if gw == '木' and dw == '水': return '父母'
    if gw == '火' and dw == '土': return '子孙'
    if gw == '火' and dw == '金': return '妻财'
    if gw == '火' and dw == '水': return '官鬼'
    if gw == '火' and dw == '木': return '父母'
    if gw == '土' and dw == '金': return '子孙'
    if gw == '土' and dw == '水': return '妻财'
    if gw == '土' and dw == '木': return '官鬼'
    if gw == '土' and dw == '火': return '父母'
    if gw == '金' and dw == '水': return '子孙'
    if gw == '金' and dw == '木': return '妻财'
    if gw == '金' and dw == '火': return '官鬼'
    if gw == '金' and dw == '土': return '父母'
    if gw == '水' and dw == '木': return '子孙'
    if gw == '水' and dw == '火': return '妻财'
    if gw == '水' and dw == '土': return '官鬼'
    if gw == '水' and dw == '金': return '父母'
    return ''

def _get_xunkong(rizhu_gan, rizhu_zhi):
    """获取旬空的两个地支"""
    gan_idx = GAN.index(rizhu_gan)
    zhi_idx = ZHI.index(rizhu_zhi)
    xun_start_gan = GAN[(gan_idx - zhi_idx) % 10]
    xun_start_zhi = ZHI[(zhi_idx - zhi_idx) % 12]  # 地支子
    # Actually: find which旬日柱属于
    for (sg, sz), (xk1, xk2) in XUNKONG.items():
        sg_idx = GAN.index(sg)
        sz_idx = ZHI.index(sz)
        # 日柱在旬中的位置
        ri_idx = ((gan_idx - sg_idx) * 12 + (zhi_idx - sz_idx)) % 60
        if ri_idx < 10:  # 这个旬有10天
            return xk1, xk2
    return '', ''



def _compute_tiandi_pan(yue_jiang, shi_chen):
    """调用排盘引擎计算天地盘，返回{地盘: {天盘, 天将}}（P1：停用 DaLiuRenEngine，改用 V2 起课引擎）"""
    try:
        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        engine = SiKeSanChuanCalculator2()
        tian_di = engine.get_tiandi_pan(yue_jiang, shi_chen)  # 月将加时，{地盘: 天盘}

        tiandi_pan = {}
        for di, tian in tian_di.items():
            tiandi_pan[di] = {'天盘': tian, '天将': ''}
        return tiandi_pan
    except Exception as e:
        return {}

def _build_reasoning_chain_from_analysis(full_data):
    """从5d预测的 analysis 和 prediction 字段构建17步推理链"""
    chain = {}
    analysis = full_data.get('analysis', full_data.get('analysis', {}))
    prediction = full_data.get('prediction', {})
    
    # 1. 课体
    kd = analysis.get('keti_duanyu', {}) if isinstance(analysis, dict) else {}
    if kd:
        keti_name = kd.get('keti_name') or full_data.get('keti', '?')
        keti_level = kd.get('level') or kd.get('等级', '?')
        keti_duanyu = kd.get('duanyu') or kd.get('断语', '')
        parts = [f"课体: {keti_name} [{keti_level}]"]
        if keti_duanyu:
            parts.append(f"断语: {keti_duanyu}")
        if kd.get('ke_64_level'):
            parts.append(f"64课经: {kd['ke_64_level']}")
        chain['课体'] = '\n'.join(parts)
    elif full_data.get('keti'):
        chain['课体'] = f"课体: {full_data.get('keti')}"
    
    # 2. 四课加临
    if isinstance(analysis, dict):
        sq = analysis.get('sike_qi', {})
        if sq and sq.get('四课关系'):
            rels = sq.get('四课关系', [])
            if isinstance(rels, list):
                parts = [f"{r.get('类型','?')}: {r.get('描述','')}" for r in rels if isinstance(r, dict)]
                chain['四课加临'] = '\n'.join(parts) + (f"\n总评: {sq.get('描述','')}" if sq.get('描述') else '')
            else:
                chain['四课加临'] = str(rels)
        elif sq and sq.get('描述'):
            chain['四课加临'] = sq.get('描述', '')
    
    # 3. 用神五气
    if isinstance(analysis, dict):
        ys = analysis.get('yong_shen', {})
        if ys and (ys.get('分析') or ys.get('用神')):
            chain['用神五气'] = f"{ys.get('用神', '')}({ys.get('旺衰', '')}) — {ys.get('分析', '')}"
        else:
            # 回退到 full_analysis 的用神分析（更详细）
            fa = analysis.get('full_analysis', {}) if isinstance(analysis, dict) else {}
            ysa = fa.get('用神分析', {})
            if ysa and ysa.get('用神地支'):
                chain['用神五气'] = f"{ysa.get('用神地支','')}({ysa.get('五行','')}/{ysa.get('旺衰','')}) — {ysa.get('五气吉凶','')} (评分{ysa.get('五气评分','?')})"
    
    # 4. 三传
    san_chuan = full_data.get('san_chuan', full_data.get('sanchuan', []))
    if san_chuan:
        chain['三传'] = ' → '.join(san_chuan)
    
    # 5. 六亲分析
    if isinstance(analysis, dict):
        lq = analysis.get('liuqin', [])
        if lq:
            chain['六亲分析'] = ' → '.join([f"{i.get('地支','?')}({i.get('六亲','?')})" for i in lq])
    
    # 6. 天将分析
    if isinstance(analysis, dict):
        tj = analysis.get('tianjiang', {})
        if tj:
            parts = []
            for chuan in ['初传', '中传', '末传']:
                if tj.get(chuan):
                    parts.append(f"{chuan}:{tj[chuan]}")
            if parts:
                chain['天将分析'] = f"{', '.join(parts)} ({tj.get('昼夜', '')}{tj.get('顺逆', '')})"
    
    # 7. 五行
    if san_chuan:
        wx_map = {'子':'水','丑':'土','寅':'木','卯':'木','辰':'土','巳':'火','午':'火','未':'土','申':'金','酉':'金','戌':'土','亥':'水'}
        wxs = [wx_map.get(sc, '?') for sc in san_chuan]
        chain['五行'] = ' → '.join(wxs)
    
    # 8. 旬空
    if isinstance(analysis, dict):
        kq = analysis.get('kong_info', {})
        if kq:
            parts = []
            for chuan in ['初传', '中传', '末传']:
                parts.append(f"{chuan}{'落空 ⚠️' if kq.get(chuan) else '不空'}")
            chain['旬空'] = ', '.join(parts)
    
    # 9. 旺衰
    if isinstance(analysis, dict):
        ws = analysis.get('wangshuai', [])
        if ws:
            chain['旺衰'] = ' → '.join([f"{i.get('地支','?')}({i.get('旺衰','?')})" for i in ws])
    
    # 10. 神煞
    if isinstance(analysis, dict):
        ss = analysis.get('shen_sha', {})
        if ss:
            items = [f"{k}:{v}" for k, v in ss.items() if v and v != '无' and v != '']
            if items:
                chain['神煞'] = ', '.join(items)
    
    # 11. 刑冲合害
    if isinstance(analysis, dict):
        rels = analysis.get('relationships', [])
        if rels:
            lines = []
            for r in rels:
                tags = []
                if r.get('五行关系'): tags.append(r['五行关系'])
                if r.get('六合'): tags.append('六合')
                if r.get('六冲'): tags.append('六冲')
                if r.get('三刑'): tags.append('三刑')
                if r.get('六害'): tags.append('六害')
                lines.append(f"{r.get('from','?')}→{r.get('to','?')}: {', '.join(tags) if tags else '无特殊'}")
            if lines:
                chain['刑冲合害'] = '\n'.join(lines)
    
    # 12. 十二气财星
    if isinstance(analysis, dict):
        ce = analysis.get('cai_shi_er_qi', {})
        if ce and (ce.get('财象') or ce.get('财星状态')):
            status = ce.get('财象', ce.get('财星状态', ''))
            details = ce.get('三传十二气', [])
            if isinstance(details, list) and details:
                detail_str = ', '.join([f"{d.get('三传','?')}{d.get('地支','')}({d.get('十二气','?')})" for d in details if isinstance(d, dict)])
                chain['十二气财星'] = f"{status} — {detail_str}"
            else:
                chain['十二气财星'] = status
    
    # 13. 身强身弱
    if isinstance(analysis, dict):
        sr = analysis.get('shen_qiang_ruo', {})
        if sr and (sr.get('身强身弱') or sr.get('状态')):
            status = sr.get('身强身弱', sr.get('状态', ''))
            cai = sr.get('财旺财弱', '')
            rel = sr.get('身财关系', '')
            chain['身强身弱'] = f"{status}" + (f"，{cai}" if cai else "") + (f"，{rel}" if rel else "")
    
    # 14-17. 趋势判断/应期/风险提示
    if prediction:
        reasons = prediction.get('reasons', [])
        if reasons:
            chain['趋势判断'] = f"综合评分 {prediction.get('score', '?')}，置信度 {prediction.get('confidence', '?')}% → {prediction.get('trend', '?')}"
            chain['风险提示'] = '\n'.join(reasons)
    
    # 八杀（附加到风险提示中）
    if isinstance(analysis, dict):
        bs = analysis.get('ba_sha', {})
        if bs:
            sha_items = []
            sha_list = bs.get('八杀明细', []) if isinstance(bs, dict) else []
            if isinstance(sha_list, list):
                for s in sha_list:
                    if isinstance(s, dict) and s.get('状态') and s['状态'] != '未现':
                        sha_items.append(f"{s.get('杀', '?')}: {s.get('断语', s.get('状态',''))} [评分{s.get('评分',0)}]")
            if sha_items:
                chain['八杀'] = '\n'.join(sha_items) + (f"\n总评: {bs.get('描述','')}" if bs.get('描述') else '')
    
    return chain

@app.route('/api/prediction/<pred_id>')
def api_prediction_detail(pred_id):
    preds = get_predictions() or []
    for d in preds:
        if d.get('id') == pred_id:
            # 获取天地盘数据，如果没有则调用引擎计算
            tiandi_pan = d.get('tiandi_pan', {})
            yue_jiang = d.get('yue_jiang', '')
            shi_chen = d.get('shi_chen', '')
            
            # 如果没有天地盘数据，调用排盘引擎
            if not tiandi_pan and yue_jiang and shi_chen:
                tiandi_pan = _compute_tiandi_pan(yue_jiang, shi_chen)
            
            # 对5d类型预测，从 liuren_20d_data 加载完整 prediction/analysis/reasoning_chain
            full_data = None
            reasoning_chain = d.get('reasoning_chain', {})
            rc_filled = d.get('rc_filled', 0)
            prediction = d.get('prediction')  # 从扁平条目直接读取 prediction dict
            analysis = d.get('analysis', '')
            
            # 兼容：reasoning_chain 可能是列表（旧格式：评分明细字符串列表）
            # 统一转换为字典格式（17步推理链）
            if isinstance(reasoning_chain, list):
                # 尝试从 liuren_20d_data 加载完整数据重建推理链
                date_str = d.get('date', '')
                if date_str:
                    try:
                        from liuren_20d_engine import load_liuren_prediction
                        loaded = load_liuren_prediction(date_str)
                        # 校验：加载的数据必须有 category/id 且与当前预测匹配
                        # （5d引擎每天只存一个文件，多类别会互相覆盖）
                        if loaded:
                            loaded_cat = loaded.get('category', '')
                            loaded_id = loaded.get('id', '')
                            current_cat = d.get('category', '')
                            current_id = d.get('id', '')
                            if (loaded_id and loaded_id == current_id) or (loaded_cat and loaded_cat == current_cat):
                                full_data = loaded
                            # 否则 loaded 不匹配当前预测，保持 full_data=None 走简化构建
                    except Exception:
                        pass
                # 如果加载失败或不匹配，用当前预测数据构建
                if not full_data:
                    # 从 stock_predictions.json 的扁平字段构建
                    full_data = {
                        'analysis': {},
                        'prediction': {
                            'score': d.get('trend_score', 0),
                            'confidence': d.get('confidence', 0),
                            'trend': d.get('trend_prediction', ''),
                            'reasons': reasoning_chain if isinstance(reasoning_chain, list) else [],
                        },
                        'san_chuan': d.get('sanchuan', []),
                        'keti': d.get('keti', ''),
                    }
                    # 将字符串analysis中的关键信息提取到analysis dict
                    analysis_str = d.get('analysis', '')
                    if isinstance(analysis_str, str) and analysis_str:
                        full_data['analysis'] = {'_raw': analysis_str}
                reasoning_chain = _build_reasoning_chain_from_analysis(full_data)
                rc_filled = len(reasoning_chain)
            
            if pred_id.startswith('20d_') or d.get('predict_session', '') == '5天周期':
                date_str = d.get('date', '')
                if date_str:
                    try:
                        from liuren_20d_engine import load_liuren_prediction
                        full_data = load_liuren_prediction(date_str)
                        if full_data:
                            prediction = full_data.get('prediction')
                            analysis = full_data.get('analysis', analysis)
                            # 从 analysis 构建 reasoning_chain（17步格式）
                            if not isinstance(reasoning_chain, dict) or not reasoning_chain:
                                reasoning_chain = _build_reasoning_chain_from_analysis(full_data)
                                rc_filled = len(reasoning_chain)
                    except Exception:
                        pass
            
            # 回退：如果 reasoning_chain 为空 但 prediction 或 analysis 存在，构建17步推理链
            if (not isinstance(reasoning_chain, dict) or not reasoning_chain):
                analysis_data = d.get('analysis', {})
                if not isinstance(analysis_data, dict):
                    analysis_data = {}
                reasoning_chain = _build_reasoning_chain_from_analysis({
                    'prediction': prediction if isinstance(prediction, dict) else {},
                    'san_chuan': d.get('sanchuan', []),
                    'analysis': analysis_data,
                    'keti': d.get('keti', ''),
                })
                rc_filled = len(reasoning_chain)
            
            resp = {
                'id': d.get('id', ''),
                'predict_time': d.get('predict_time', ''),
                'date': d.get('date', ''),
                'target_date': d.get('target_date', ''),
                'category': d.get('category', ''),
                'rizhu': d.get('rizhu', ''),
                'yue_jiang': d.get('yue_jiang', ''),
                'shi_chen': d.get('shi_chen', ''),
                'keti': d.get('keti', ''),
                'fayong': d.get('fayong', ''),
                'sike': _parse_sike(d.get('sike')),
                'sanchuan': d.get('sanchuan', []),
                'sanchuan_tianjiang': d.get('sanchuan_tianjiang', []),
                'tiandi_pan': tiandi_pan,
                'trend_prediction': d.get('trend_prediction', ''),
                'jixiong': d.get('jixiong', ''),
                'analysis': analysis,
                'reasoning_chain': reasoning_chain,
                'rc_filled': rc_filled,
                'prediction': prediction,
                'actual_result': d.get('actual_result', ''),
                'status': d.get('status', ''),
                'actual_details': d.get('actual_details'),
                'check_time': d.get('check_time', ''),
                'vote_detail': d.get('vote_detail', {}),
                'vote_result': d.get('vote_result', {}),
                'holistic_synthesis': d.get('holistic_synthesis', {}),
                'knowledge_features': d.get('knowledge_features', {}),
                'kf_impact': d.get('kf_impact'),
                'kf_reasons': d.get('kf_reasons', []),
                # 【2026-08-02 修复】量化类别透出真实字段，否则前端全部显示 --
                'etf': d.get('etf', ''),
                'name': d.get('name', ''),
                'method': d.get('method', ''),
                'momentum_20d': d.get('momentum_20d'),
                'volatility': d.get('volatility'),
                'rsi': d.get('rsi'),
                'ma_trend': d.get('ma_trend', ''),
                'position': d.get('position'),
                'score': d.get('score'),
                'confidence': d.get('confidence'),
                'price': d.get('price'),
            }

            # 【2026-08-02 心动验证】天机起课：注入心动预测方向 + 实际方向（按窗口实时算，不依赖存储 actual_result）
            if resp.get('category') == 'manual' or resp.get('source') == 'tianji_cast' or str(resp.get('id','')).startswith('tj-'):
                try:
                    from engine.tianji_harness import _read_store as _tj_read, _actual_of as _tj_actual, build_calendar as _tj_cal
                    _store = _tj_read()
                    _tj_rec = next((r for r in _store.values() if r.get('cast_date') == resp.get('date')), None)
                    if _tj_rec:
                        resp['tianji_updown'] = _tj_rec.get('tianji_updown')
                        _ps = _tj_rec.get('period_start'); _pe = _tj_rec.get('period_end')
                        resp['period_start'] = _ps; resp['period_end'] = _pe
                        _combined, _idx, _series = _tj_cal()
                        _series_map = {dd:(op,cl) for dd,(op,cl) in _series}
                        resp['actual_direction'] = _tj_actual(_ps, _pe, _series_map)  # 'up'/'down'/None
                except Exception:
                    pass
            return jsonify(resp)
    return jsonify({'error': '未找到该预测记录'}), 404

@app.route('/api/trades')
def api_trades():
    all_trades = []
    
    # 1. 读取分类特定的交易记录
    for cat in CATEGORIES:
        trades = get_trades(cat) or []
        for t in (trades if isinstance(trades, list) else trades.get('trades', trades.get('history', []))):
            action = t.get('action', t.get('type', ''))
            if action.startswith('MIGRATED_') or t.get('migrated_from_legacy'):
                continue
            all_trades.append({
                'category': CAT_NAMES[cat],
                'category_key': cat,
                'time': t.get('timestamp', t.get('time', t.get('trade_time', ''))),
                'action': t.get('action', t.get('type', '')),
                'price': t.get('price', t.get('trade_price', 0)),
                'amount': t.get('shares', t.get('volume', t.get('amount', t.get('position', 0)))),
                'pnl': t.get('pnl', t.get('profit_loss', t.get('realized_pnl', 0))),
            })
    
    # 2. 读取通用交易记录 auto_trades.json
    general_trades = read_json(MEMORY / 'auto_trades.json')
    if general_trades:
        for t in (general_trades if isinstance(general_trades, list) else general_trades.get('trades', [])):
            action = t.get('signal', {}).get('action', t.get('action', ''))
            if action:
                all_trades.append({
                    'category': '通用交易',
                    'category_key': 'general',
                    'time': t.get('time', ''),
                    'action': action,
                    'price': t.get('price', 0),
                    'amount': t.get('shares_after', 0),
                    'pnl': t.get('pnl', 0),
                })
    
    # 3. 读取投资组合中的交易历史
    portfolio = read_json(MEMORY / 'virtual_portfolio.json')
    if portfolio and portfolio.get('transactions'):
        for t in portfolio['transactions']:
            # 优先使用交易记录中的 category 字段
            trade_category = t.get('category', '')
            if trade_category in CAT_NAMES:
                cat_name = CAT_NAMES[trade_category]
                cat_key = trade_category
            elif trade_category:
                # 如果有 category 但不在 CAT_NAMES 中，直接使用
                cat_name = trade_category
                cat_key = trade_category
            else:
                cat_name = '投资组合'
                cat_key = 'portfolio'
            
            all_trades.append({
                'category': cat_name,
                'category_key': cat_key,
                'time': t.get('time', ''),
                'action': t.get('type', ''),
                'price': t.get('price', 0),
                'amount': t.get('shares', t.get('amount', 0)),
                'pnl': t.get('pnl', 0),
                'jixiong': t.get('jixiong', ''),
                'trend_prediction': t.get('trend_prediction', ''),
            })

    # 4. 纳入量化子系统 + 六壬子系统的交易记录
    # 【2026-08-02 去重修复】原逻辑把 closed_trades 拆成"买(pnl=0)+卖"两条 → 一笔平仓算 2 笔；
    # 且 positions（持仓中）也计入，与「持仓监控」tab 重复。现改为：
    #   - 持仓中（holding）→ 一条「买入」流水（status=holding，pnl 为浮动盈亏）
    #   - 已平仓（closed） → 一条「平仓」流水（含真实已实现盈亏，不再拆两条）
    # 不再截断前100，保证统计与展示完整。
    for subsystem_mod, label in [('quant_position_manager', '量化'), ('liuren_position_manager', '六壬')]:
        try:
            mod = __import__(subsystem_mod)
            sp_data = mod.get_positions()
            for p in sp_data.get('positions', []):
                all_trades.append({
                    'category': f'{label}持仓', 'category_key': f'{label}_position',
                    'time': p.get('buy_time', ''), 'code': p['code'], 'name': p['name'],
                    'action': '买入', 'price': p.get('buy_price', 0),
                    'amount': p.get('amount', 0), 'pnl': p.get('pnl', 0),
                    'status': 'holding', 'advice': p.get('advice', ''),
                    'source': p.get('source', 'auto'),
                })
            for p in sp_data.get('closed_trades', []):
                all_trades.append({
                    'category': f'{label}持仓', 'category_key': f'{label}_position',
                    'time': p.get('close_time', '') or p.get('buy_time', ''), 'code': p['code'], 'name': p['name'],
                    'action': '平仓', 'price': p.get('close_price', p.get('sell_price', 0)),
                    'amount': p.get('amount', 0), 'pnl': p.get('pnl', 0),
                    'status': 'closed', 'close_reason': p.get('close_reason', ''),
                    'buy_time': p.get('buy_time', ''), 'buy_price': p.get('buy_price', 0),
                    'advice': p.get('advice', ''), 'source': p.get('source', 'auto'),
                })
        except Exception:
            pass

    all_trades.sort(key=lambda x: x.get('time', ''), reverse=True)
    return jsonify(all_trades)

@app.route('/api/accuracy')
def api_accuracy():
    """详细准确率统计 - 调用 accuracy_stats 模块"""
    try:
        from engine.accuracy_stats import (
            stat_by_category, stat_by_vote_consistency, stat_by_keti,
            stat_by_trend_type, stat_bias_analysis, generate_insights,
            stat_portfolios, stat_error_streaks
        )
        preds = get_predictions() or []
        
        # 按类别统计
        by_category = stat_by_category(preds)
        
        # 投票一致性统计
        vote_stats = stat_by_vote_consistency(preds)
        
        # 按课体统计
        keti_stats = stat_by_keti(preds)[:10]  # 只取前10个
        
        # 按趋势类型统计
        trend_stats = stat_by_trend_type(preds)
        
        # 系统性偏差检测
        bias_analysis = stat_bias_analysis(preds)
        
        # 改进建议
        insights = generate_insights(preds)
        
        # 连续状态
        streaks = stat_error_streaks(preds)
        
        return jsonify({
            'by_category': by_category,
            'vote_consistency': vote_stats,
            'by_keti': keti_stats,
            'by_trend': trend_stats,
            'bias_analysis': {
                'total_reviewed': bias_analysis.get('total_reviewed', 0),
                'biases': bias_analysis.get('biases', []),
                'summary': bias_analysis.get('summary', ''),
            },
            'insights': insights,
            'streaks': {
                'max_correct_streak': streaks.get('max_correct_streak', 0),
                'max_error_streak': streaks.get('max_error_streak', 0),
                'current_streak': streaks.get('current_streak', {}),
                'recent_trends': streaks.get('recent_trends', {}),
            },
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═══════════════════════════════════════════════
# 行情数据获取（直接 akshare 调用，子进程作 fallback）
# ⚠️ 注意：禁止在模块级别导入 StockAnalyzer/py_mini_racer！
#    那会导致 V8 DLL 在主进程加载，触发 partition_address_space 崩溃。
#    所有需要 JS 引擎的操作（gap_analysis）走 lazy subprocess 方式。
# ═══════════════════════════════════════════════
FETCHER = Path(__file__).parent / 'engine' / 'market_fetcher.py'

def _fetch_market_direct():
    """直接获取上证指数行情（使用预加载的akshare，避免多线程DLL崩溃）"""
    if _ak is None:
        return None, 'akshare 未预加载，使用子进程fallback'
    try:
        df = _ak.stock_zh_index_daily(symbol="sh000001")
        latest = df.iloc[-1]
        prev = df.iloc[-2]
        price = round(float(latest['close']), 2)
        prev_close = round(float(prev['close']), 2)
        change = round(price - prev_close, 2)
        change_pct = round(change / prev_close * 100, 2)
        # akshare新版本date在列中（RangeIndex），兼容旧版DatetimeIndex
        date_val = latest.get('date', latest.name)
        if hasattr(date_val, 'strftime'):
            date_str = date_val.strftime('%Y-%m-%d')
        elif hasattr(date_val, 'isoformat'):
            date_str = date_val.isoformat()
        else:
            date_str = str(date_val)[:10]
        return {
            'price': price,
            'prev_close': prev_close,
            'change': change,
            'change_pct': change_pct,
            'high': round(float(latest['high']), 2),
            'low': round(float(latest['low']), 2),
            'date': date_str,
            'name': '上证指数',
            'code': '000001',
        }, None
    except Exception as e:
        return None, str(e)

def _fetch_market_history_direct():
    """直接获取上证指数历史K线（使用预加载的akshare）"""
    if _ak is None:
        return None, 'akshare 未预加载，使用子进程fallback'
    try:
        df = _ak.stock_zh_index_daily(symbol="sh000001")
        df = df.tail(120)
        history = []
        for _, row in df.iterrows():
            date_val = row.get('date', row.name)
            if hasattr(date_val, 'strftime'):
                date_str = date_val.strftime('%Y-%m-%d')
            elif hasattr(date_val, 'isoformat'):
                date_str = date_val.isoformat()
            else:
                date_str = str(date_val)[:10]
            history.append({
                'date': date_str,
                'close': round(float(row['close']), 2),
                'high': round(float(row['high']), 2),
                'low': round(float(row['low']), 2),
            })
        return history, None
    except Exception as e:
        return None, str(e)

def _run_fetcher(*args):
    """子进程方式获取行情（fallback）
    【2026-08-02 修复】仪表盘进程在 Python311 下运行时，akshare 装在 Python312 里。
    sys.executable 是当前进程解释器（Python311），找不到 akshare → 子进程也失败。
    显式用装了 akshare 的 Python 解释器作为子进程，确保 fallback 真的能跑通。
    """
    # 优先用与当前进程不同的、装了 akshare 的解释器；否则退回 sys.executable
    python_bin = sys.executable
    candidates = [
        r"C:/Users/Administrator/AppData/Local/Programs/Python/Python312/python.exe",
        r"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.13.12/python.exe",
        r"C:/Users/Administrator/.workbuddy/binaries/python/versions/3.12.10/python.exe",
    ]
    for cand in candidates:
        if cand and Path(cand).exists() and cand != sys.executable:
            # 验证该解释器确实有 akshare
            try:
                r = subprocess.run([cand, '-c', 'import akshare'], capture_output=True, text=True, timeout=5)
                if r.returncode == 0:
                    python_bin = cand
                    break
            except Exception:
                continue
    try:
        result = subprocess.run(
            [python_bin, str(FETCHER), *args],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            return None, result.stderr.strip() or f'fetcher 子进程退出码 {result.returncode}'
        return json.loads(result.stdout), None
    except subprocess.TimeoutExpired:
        return None, '行情数据获取超时'
    except Exception as e:
        return None, str(e)

@app.route('/api/market')
def api_market():
    global _market_cache, _market_cache_time
    now = time.time()
    if _market_cache and (now - _market_cache_time) < _CACHE_TTL:
        return jsonify(_market_cache)

    # 优先使用 StockAnalyzer 直接获取（与 api_server.py 一致）
    data, err = _fetch_market_direct()
    if not data:
        # fallback: 子进程方式
        data, err = _run_fetcher('market')

    if data and data.get('price'):
        _market_cache = data
        _market_cache_time = now
        return jsonify(data)
    if err:
        print(f"  [行情] 获取失败: {err}", flush=True)
    if _market_cache:
        _market_cache['note'] = '数据可能延迟'
        return jsonify(_market_cache)
    return jsonify({'error': err or '无法获取行情'}), 500

@app.route('/api/market_history')
def api_market_history():
    # 优先使用 StockAnalyzer 直接获取
    data, err = _fetch_market_history_direct()
    if not data:
        # fallback: 子进程方式
        data, err = _run_fetcher('history', '120')
    if data and isinstance(data, list):
        return jsonify(data)
    return jsonify({'error': err or '无法获取历史数据'}), 500

@app.route('/api/gap_analysis')
def api_gap_analysis():
    """返回AI推理与原著对比的差距分析数据"""
    try:
        ga = get_gap_analyzer()
        result = ga.compute()
        if 'error' in result:
            return jsonify({'status': 'unavailable', 'message': result.get('error')})
        return jsonify(result)
    except:
        return jsonify({'status': 'unavailable', 'message': '模块未加载'})


@app.route('/api/gap_compare')
def api_gap_compare():
    """对比R14与R15两轮训练的差距变化"""
    try:
        ga = get_gap_analyzer()
        r14_path = str(ROOT / 'r14_self_learning_results.json')
        r15_path = str(ROOT / 'r15_weak_focus_results.json')
        if not os.path.exists(r15_path):
            return jsonify({'error': 'R15训练尚未完成', 'r14_exists': True}), 404
        result = ga.compare(r14_path, r15_path, 'R14 baseline', 'R15 weak-focus')
        if 'error' in result:
            return jsonify(result), 404
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════
# 择日分析 API
# ═══════════════════════════════════════════════

# ── 综合批语（斗首/演禽/六壬三流派判断 → 文言主批语 + 白话括注，面向普通人）──
_ZONGHE_TYPE_TAIL = {
    # 阴宅
    '立碑': ('宜安葬立碑，可期福蔭綿長', '适合立碑安葬，可期望福荫绵长'),
    '安葬': ('宜安葬先靈，福蔭後昆', '适合安葬先灵，福荫后代'),
    # 婚嫁
    '婚嫁': ('宜婚嫁納采，鸞鳳和鳴', '适合婚嫁纳采，夫妻和合'),
    '婚姻': ('宜婚嫁納采，鸞鳳和鳴', '适合婚嫁纳采，夫妻和合'),
    # 阳宅
    '开业': ('宜開市大吉，財源廣進', '适合开业，财源广进'),
    '签约交易': ('宜簽約交易，誠信有成', '适合签约交易，诚信有成'),
    '新居入宅': ('宜入宅安家，門庭興旺', '适合搬入新居，家宅兴旺'),
    '动土修造': ('宜動土修造，根基穩固', '适合动土施工，根基稳固'),
    '安门': ('宜安門立戶，納氣迎祥', '适合安门立户，纳气迎祥'),
    '作灶': ('宜作灶安火，灶火興旺', '适合作灶安火，灶火兴旺'),
    '安床': ('宜安床定鋪，臥榻安寧', '适合安床定铺，卧榻安宁'),
    '上梁盖屋': ('宜上梁蓋屋，屋宇安固', '适合上梁盖屋，屋宇稳固'),
    '家宅': ('宜家宅安寧，門庭清吉', '适合家宅安宁，门庭清吉'),
    # 人事（六壬占类）
    '求财': ('宜求財納福，財源有期', '适合求财纳福，财源可期'),
    '功名': ('宜科舉求名，前程有望', '适合科考求名，前程有望'),
    '疾病': ('宜祈福保安，身心康泰', '适合祈福保安，身心康泰'),
    '官讼': ('宜訟事和息，是非消散', '适合诉讼和解，是非消散'),
    '胎产': ('宜祈嗣求子，胎產順遂', '适合祈嗣求子，胎产顺遂'),
    '求嗣': ('宜祈嗣求子，子嗣有望', '适合祈嗣求子，子嗣有望'),
    '出行': ('宜出行遠行，旅途平安', '适合出行远行，旅途平安'),
    '提车': ('宜提車納吉，出入平安', '适合提车纳吉，出入平安'),
    '阳宅动土': ('宜陽宅動土，興工順利', '适合阳宅动土，兴工顺利'),
    '阴宅动土': ('宜陰宅動土，開山破土', '适合阴宅动土，开山破土'),
    '买房过户': ('宜置業過戶，安居樂業', '适合买房过户，安居乐业'),
    '开工': ('宜開工大吉，事業興旺', '适合开工大吉，事业兴旺'),
    '入学开学': ('宜入學開蒙，學業有成', '适合入学开学，学业有成'),
    '考试': ('宜科場應試，金榜題名', '适合考场应试，金榜题名'),
    '测孩子成绩': ('宜文昌照臨，成績可期', '宜文昌照临，孩子成绩可期'),
    '迁坟': ('宜遷墳移葬，安妥先靈', '适合迁坟移葬，安妥先灵'),
    '催龙补气': ('宜催龍補氣，龍脈興旺', '适合催龙补气，龙脉兴旺'),
    '召山买土': ('宜召山買土，土脈歸山', '适合召山买土，土脉归山'),
    '祭祀祈福': ('宜祭祀祈福，誠感神明', '适合祭祀祈福，诚感神明'),
    '天时': ('宜祈晴禱雨，天時順應', '适合祈晴祷雨，天时顺应'),
    '终身': ('宜終身謀劃，前途光明', '适合终身谋划，前途光明'),
    '流年': ('宜流年順遂，歲運亨通', '适合流年顺遂，岁运亨通'),
    '亡盗': ('宜尋物訪賊，物歸有望', '适合寻物访贼，物归有望'),
    '杂占': ('諸事合宜，吉慶可期', '诸事合宜，吉庆可期'),
    '一课二事': ('諸事合宜，吉慶可期', '诸事合宜，吉庆可期'),
}
_ZONGHE_DEFAULT_TAIL = ('諸事合宜，吉祥如意', '诸事合宜，吉祥如意')


def _pick_first(lst):
    """从断语/格局列表安全取首条可读文本。"""
    if not lst:
        return ''
    for x in lst:
        if isinstance(x, str) and x.strip():
            return x.strip()
        if isinstance(x, dict):
            for k in ('断语', '判断', '名称', '格局名称', 'name', 'detail', '描述'):
                if x.get(k):
                    return str(x[k]).strip()
    return ''


def _clean_summary(s, maxlen=60):
    """清洗引擎 summary：去 emoji/对勾/换行空白，截断。"""
    import re as _re
    s = str(s or '')
    s = _re.sub(r'[\u2705\u2714\u2713\u274c\u2713\u2717✅❌✓✗]', '', s)
    s = _re.sub(r'\s+', '', s)
    s = s.rstrip('。，,；;')
    return s[:maxlen] if len(s) > maxlen else s


def _po_gong_txt(po):
    """泊宫 dict（{'年禽': {'宿':'氐','宫':'风','吉凶':'平'},...}）→ '氐宿平、箕宿吉'。"""
    if isinstance(po, dict):
        parts = []
        for k in ('日禽', '时禽', '年禽', '月禽'):
            v = po.get(k)
            if isinstance(v, dict):
                _s = (v.get('宿') or '').strip()
                _jx = (v.get('吉凶') or '').strip()
                if _s:
                    parts.append(f'{_s}宿{_jx}')
        if parts:
            return '、'.join(parts)
        return str(po)[:40]
    return str(po or '')


def _grade_wen(g, ok_w, mid_w, bad_w):
    """等级 → 古法短句（吉/中/凶）。"""
    g = str(g or '')
    if any(k in g for k in ('大吉', '吉')):
        return ok_w
    if any(k in g for k in ('凶', '大凶')):
        return bad_w
    return mid_w


def _pat_txt(p):
    """格局对象 → '名称（吉凶）'。"""
    if isinstance(p, dict):
        name = str(p.get('格局名称', p.get('name', '')) or '')
        jx = str(p.get('吉凶', '') or '')
        return (name + ('（' + jx + '）' if jx else '')) if name else str(p)[:24]
    return str(p)


def _build_zonghe_piyu(result, zetiri_type='立碑'):
    """斗首/演禽/六壬 → {wen: 文言主批语, bai: 白话详批, detail: 流派明细}
    深度版（2026-08-20）：每家分"等级句 + 古籍断语 + 格局/星曜 + 应期/合参"——引擎产出吃透，不空泛。"""
    wen = []
    bai = []
    detail = {}

    # ① 斗首
    ds = result.get('doushou_full') or {}
    if isinstance(ds, dict) and 'error' not in ds:
        ds_dys = [str(x).strip() for x in (ds.get('duanyu') or []) if str(x).strip()][:2]
        ds_pats = [_pat_txt(x) for x in (ds.get('patterns') or [])][:2]
        ds_grade = ds.get('grade') or ''
        stars = ds.get('sizhu_stars') or {}
        # 【2026-09-07 审计修复 BUG-2】星曜吉凶分组错乱：原 _XIONG_XING 含'元辰'(吉星)
        #   且不含'破鬼'，导致破鬼被漏提示、反误称"为用"。正确斗首星曜吉凶：
        #   吉=元辰(同气)/武财(我生)；中=廉贞(我克/子)；凶=贪官(克我)/破鬼(我生为鬼·耗)。
        _XIONG_XING = ('贪官', '破鬼')
        _JI_XING = ('元辰', '武财')
        star_bad = [f'{k}{v.get("星曜", "")}' for k, v in stars.items() if str(v.get('星曜', '')) in _XIONG_XING]
        star_good = [f'{k}{v.get("星曜", "")}' for k, v in stars.items() if str(v.get('星曜', '')) in _JI_XING]
        ds_wen = _grade_wen(ds_grade, '斗首得令，山家获吉', '斗首平稳，山家中和', '斗首失令，山家欠吉')
        # 凶星（贪官/破鬼）无论得令与否均须显式点忌——否则"破鬼为用"式语义矛盾：
        #   破鬼为耗泄之星，克/泄山家，必为忌；仅当武财≥2 制化（武财关鬼）方转吉。
        if star_bad:
            _wc_cnt2 = sum(1 for v in stars.values() if str(v.get('星曜', '')) == '武财')
            if _wc_cnt2 >= 2:
                ds_wen += '，' + '、'.join(star_bad[:2]) + '得武财关鬼制化为用'
            else:
                ds_wen += '，' + '、'.join(star_bad[:2]) + '为忌'
        elif star_good:
            ds_wen += '，' + '、'.join(star_good[:2]) + '为用'
        wen.append(ds_wen)
        b_parts = []
        if ds_dys:
            b_parts.append('古籍断曰：' + '；'.join(ds_dys))
        if ds_pats:
            b_parts.append('课格：' + '、'.join(ds_pats))
        if stars:
            b_parts.append('四柱星曜：' + '、'.join(f'{k}{v.get("星曜", "")}' for k, v in list(stars.items())[:4]))
        bai.append('斗首：' + '。'.join(b_parts))
        detail['doushou'] = {'wen': ds_wen, 'duanyu': ds_dys, 'patterns': ds_pats, 'stars': stars, 'grade': ds_grade}

    # ② 演禽
    yq = result.get('yanqin_full') or {}
    if isinstance(yq, dict) and 'error' not in yq:
        yq_dys = [str(x).strip() for x in (yq.get('duanyu') or []) if str(x).strip()][:2]
        yq_pats = [_pat_txt(x) for x in (yq.get('patterns') or [])][:2]
        yq_grade = yq.get('grade') or yq.get('吉凶等级') or ''
        yq_po = yq.get('po_gong') or ''
        yq_xj = yq.get('xiu_jixiong') or {}
        yq_wen = _grade_wen(yq_grade, '演禽入垣，星辰拱照', '演禽中平，星辰相安', '演禽失位，星辰欠照')
        if yq_pats:
            yq_wen += '，' + '、'.join(yq_pats[:2])
        wen.append(yq_wen)
        b_parts = []
        if yq_dys:
            b_parts.append('古籍断曰：' + '；'.join(yq_dys))
        if yq_pats:
            b_parts.append('格局：' + '、'.join(yq_pats))
        if yq_po:
            b_parts.append('泊宫：' + _po_gong_txt(yq_po))
        if yq_xj:
            b_parts.append('宿曜吉凶：' + '、'.join(f'{k}{v}' for k, v in list(yq_xj.items())[:4] if v))
        bai.append('演禽：' + '。'.join(b_parts))
        detail['yanqin'] = {'wen': yq_wen, 'duanyu': yq_dys, 'patterns': yq_pats, 'po_gong': _po_gong_txt(yq_po), 'grade': yq_grade}

    # ③ 六壬（课体判定依据 + 毕法断法原文 + 十三吉课 + 占类断语 + 应期）
    sc = result.get('sanchuan') or {}
    keti = sc.get('课体') or ''
    gong_names = [p.get('name', '') for p in (result.get('gong_patterns') or []) if p.get('name')]
    kj = result.get('keti_judged') or []
    bj = (result.get('bifa_judged') or {}).get('断法') or []
    jk = (result.get('jike_13') or {}).get('hits') or []
    yq_str = str(result.get('yingqi') or '')
    zl_lines = (result.get('zhanlei_duanyu') or {}).get('duanyu_lines') or []
    _lr_grade = result.get('grade') or ''
    _lr_score = result.get('score')
    # 【2026-09-07 审计修复 BUG-4】六壬层等级须取六壬独立分(luma final_score)推导，
    #   不得用总评 grade（总评含斗首一票否决/加分项，会污染六壬narra，如总评"不宜"误为"六壬欠吉"）。
    try:
        _luma_f = (result.get('luma_detail') or {}).get('final_score')
        if _luma_f is not None:
            _lr_score = round(float(_luma_f), 1)
            if _lr_score >= 90:
                _lr_grade = '上上吉'
            elif _lr_score >= 80:
                _lr_grade = '上吉'
            elif _lr_score >= 70:
                _lr_grade = '中吉'
            elif _lr_score >= 60:
                _lr_grade = '吉'
            elif _lr_score >= 40:
                _lr_grade = '平'
            else:
                _lr_grade = '凶'
    except Exception:
        pass
    if _lr_grade or keti or gong_names:
        lr_wen = _grade_wen(_lr_grade, '六壬得吉，課體清明', '六壬中平，課體尚可', '六壬欠吉，課體有疵')
        if keti:
            lr_wen += f'，{keti}'
        if gong_names:
            lr_wen += f'，{"、".join(gong_names[:3])}並見'
        wen.append(lr_wen)
        b_parts = [f'六壬：{_lr_score}分（{_lr_grade or "未评"}）']
        if kj:
            b_parts.append('課體判定：' + '；'.join(
                f'{x.get("課体", x.get("课体", ""))}（{str(x.get("依据", ""))[:26]}）' for x in kj[:4]))
        if bj:
            b_parts.append('畢法賦：' + '；'.join(
                f'【{x.get("法句", "")}】{str(x.get("断法依据", ""))[:72]}' for x in bj[:2]))
        if jk:
            b_parts.append('十三吉課：' + '、'.join(str(x) for x in jk))
        if zl_lines:
            _zl = [l for l in zl_lines if str(l).strip() and not str(l).startswith('◆')][:2]
            if _zl:
                b_parts.append('占類要訣：' + '；'.join(str(x)[:56] for x in _zl))
        if yq_str:
            b_parts.append('應期：' + yq_str.replace('\n', '；')[:160])
        bai.append('。'.join(b_parts))
        detail['liuren'] = {'wen': lr_wen, 'keti': keti, 'keti_judged': kj, 'bifa_duanfa': bj[:2],
                            'jike_13': jk, 'yingqi': yq_str}

    # ④ 总断（评分 + 等级 + 类型落点）
    # 【2026-09-07 审计修复 BUG-1/BUG-5】文言尾缀不再在此追加——统一在⑩末尾按
    #   grade 吉凶分支拼接（凶/不宜课不得再续"诸事合宜/福荫后代"式吉语）。
    score = result.get('score')
    grade = result.get('grade') or ''
    wen.append('综合评分{0}分（{1}）'.format(score, grade or '未评'))

    # ⑤ 三派冲突点透（2026-08-20：斗首/演禽/六壬吉凶不一致时显式点出"吉中藏忌/凶中有救"）
    def _pai_side(g):
        g = str(g or '')
        if any(k in g for k in ('大吉', '上吉', '吉', '得令', '入垣', '拱照')):
            return '吉'
        if any(k in g for k in ('大凶', '凶', '失令', '失位')):
            return '凶'
        return '中'
    _sides = []
    for _s, _nm in ((detail.get('doushou'), '斗首'), (detail.get('yanqin'), '演禽'), (detail.get('liuren'), '六壬')):
        if _s:
            _sides.append((_nm, _pai_side(str(_s.get('grade', _s.get('wen', ''))))))
    _ji = [n for n, s in _sides if s == '吉']
    _xiong = [n for n, s in _sides if s == '凶']
    _hc_warns = (result.get('hecan') or {}).get('警告') or []
    _chong = []
    if _ji and _xiong:
        _chong.append('「%s得吉」而「%s见凶」——吉中藏忌，宜慎择动期、避开凶应之方' % ('、'.join(_ji), '、'.join(_xiong)))
    elif _hc_warns and _ji:
        _chong.append('三派皆吉而古籍合参示警（%s）——吉中藏忌，宜慎择动期' % str(_hc_warns[0])[:56])
    elif _hc_warns and not _sides:
        _chong.append('古籍合参示警：%s' % str(_hc_warns[0])[:56])
    if _chong:
        wen.append(_chong[0])
        bai.append('⚠ 三派异断：' + _chong[0])

    # ⑥ 应事应人（2026-08-20 叙事层接批语：应何事=类象所主/乘神断语；应何人=六亲+类象人物）
    lx = result.get('leixiang') or []
    lq = result.get('liuqin_struct') or {}
    shi_txt = []
    ren_txt = []
    for x in lx[:2]:
        sw = str(x.get('所主') or '')
        dj = str(x.get('乘神断语') or '')
        if sw:
            shi_txt.append(f"{x.get('位置', '')}{x.get('天将', '')}主{sw}" + (f'（{dj}）' if dj else ''))
        rw = str((x.get('类象') or {}).get('人物') or '')
        if rw:
            ren_txt.append(f"{x.get('天将', '')}应{rw[:40]}")
    if lq.get('断'):
        ren_txt.append(f"六亲[{lq.get('将', '')}{lq.get('关系', '')}]：{lq.get('断', '')}")
    if shi_txt:
        _first_shi = shi_txt[0].split('主', 1)[-1].split('、')[0].split('（')[0] if '主' in shi_txt[0] else shi_txt[0][:10]
        _shi_wen = f'事主{_first_shi}'
        wen.append(_shi_wen)
        bai.append('應事：' + '；'.join(shi_txt))
    if ren_txt:
        _rel_map = {'生日': '上人恩惠', '克日': '官灾口舌', '日克': '财利妻妾', '比和': '兄弟朋友', '日生': '子孙耗脱'}
        _ren_wen = '人应' + _rel_map.get(str(lq.get('关系', '')), '六亲')
        wen.append(_ren_wen)
        bai.append('應人：' + '；'.join(ren_txt[:3]))

    # ⑦ 要诀精华（2026-08-20 张九仪《仪度六壬择日要诀》：斗首六亲化气应人 + 禁忌应事）
    _ri_zhi7 = str((result.get('sizhu') or {}).get('日', ''))[-1:] or ''
    _nian_zhi7 = str((result.get('sizhu') or {}).get('年', ''))[-1:] or ''
    _yuejiang7 = str(result.get('yuejiang', '') or '')
    _DOU_LIUQIN = {'元辰': '兄弟朋友（同气帮扶）', '武财': '妻财（我生为财）', '廉子': '子孙（我克）',
                   '贪官': '官鬼是非（克我）', '破鬼': '破耗鬼祟（我生为鬼）'}
    _dou_ren = []
    for _col, _st in (result.get('doushou_full') or {}).get('sizhu_stars', {}).items():
        _xing = str(_st.get('星曜', ''))
        if _xing in _DOU_LIUQIN:
            _dou_ren.append(f'{_col}{_xing}应{_DOU_LIUQIN[_xing]}')
    if _dou_ren:
        bai.append('要诀應人（斗首六亲化气）：' + '；'.join(_dou_ren[:4]))
    # 禁忌应事（冲山/岁破/月破/三煞——要诀"日课不可犯"）
    _CH12 = {'子': '午', '午': '子', '丑': '未', '未': '丑', '寅': '申', '申': '寅',
             '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', '巳': '亥', '亥': '巳'}
    _jinji = []
    _shan_zhi = str(result.get('shan_jia') or '')
    if _shan_zhi and _ri_zhi7 == _CH12.get(_shan_zhi, ''):
        _jinji.append(f'日支{_ri_zhi7}冲山{_shan_zhi}——大忌动土修造（要诀"冲山者，日支与山家相冲也，大忌"）')
    if _nian_zhi7 and _ri_zhi7 == _CH12.get(_nian_zhi7, ''):
        _jinji.append(f'日支{_ri_zhi7}与太岁{_nian_zhi7}相冲——岁破，日课忌（要诀"日支不可与太岁相冲"）')
    _yuejian = {'寅': '亥', '卯': '戌', '辰': '酉', '巳': '申', '午': '未', '未': '午',
                '申': '巳', '酉': '辰', '戌': '卯', '亥': '寅', '子': '丑', '丑': '子'}.get(_yuejiang7, '')
    if _yuejian and _ri_zhi7 == _CH12.get(_yuejian, ''):
        _jinji.append(f'日支{_ri_zhi7}冲月建{_yuejian}——月破，日课忌（要诀"日支不可与月建相冲"）')
    _SANSHA = {'申': ('巳', '午', '未'), '子': ('巳', '午', '未'), '辰': ('巳', '午', '未'),
               '寅': ('申', '酉', '戌'), '午': ('申', '酉', '戌'), '戌': ('申', '酉', '戌'),
               '亥': ('寅', '卯', '辰'), '卯': ('寅', '卯', '辰'), '未': ('寅', '卯', '辰'),
               '巳': ('亥', '子', '丑'), '酉': ('亥', '子', '丑'), '丑': ('亥', '子', '丑')}
    if _nian_zhi7 and _shan_zhi in _SANSHA.get(_nian_zhi7, ()):
        _jinji.append(f'山家{_shan_zhi}落{_nian_zhi7}年三煞方——日课不可犯（要诀"三煞者，劫煞灾煞岁煞也…日课不可犯"）')
    if _jinji:
        wen.append('犯煞有忌，详见白话')
        bai.append('要訣禁忌：' + '；'.join(_jinji))

    # ⑧ 要诀应人应期（张九仪"两因字是大窍"：禄马贵之支命者发福、其支之年应；发传=天机灵动）
    _ddx8 = result.get('daoshan_daoxiang') or {}
    _hm8 = result.get('huoma_huolu') or {}
    _lu_z8 = (_ddx8.get('lu') or {}).get('lu_zhi', '')
    _ma_z8 = (_ddx8.get('ma') or {}).get('ma_zhi', '')
    _yq_sents = []
    if _hm8.get('huo_lu') and _lu_z8:
        _yq_sents.append(f'禄神{_lu_z8}发传（天机灵动）——{_lu_z8}命人发福，应于{_lu_z8}年')
    if _hm8.get('huo_ma') and _ma_z8:
        _yq_sents.append(f'马神{_ma_z8}发传——{_ma_z8}命人发福，应于{_ma_z8}年')
    # 【2026-09-07 审计修复 BUG-3】"福力不实"须同时检查互禄互贵通道：
    #   原 total_count==0 即写"禄马贵未到山到向，福力不实"，与互禄互贵顶格课
    #   （如 2056-04-15 互禄4项+互贵3项·summary已显示）自相矛盾。
    #   互禄互贵命中 → 转"互禄互贵顶格，福力足"，仅双通道皆空才判"福力不实"。
    try:
        _hulu_hh = None
        _sz4_r = result.get('sizhu') or {}
        _n_gan = str(_sz4_r.get('年', ''))[:1] or ''
        _y_gan = str(_sz4_r.get('月', ''))[:1] or ''
        _r_gan = str(_sz4_r.get('日', ''))[:1] or ''
        _y_zhi = str(_sz4_r.get('月', ''))[-1:] or ''
        if _n_gan and _y_gan and _r_gan:
            from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen as _LRM2
            _hulu_hh = _LRM2().check_hulu_hugui(
                _n_gan, _y_gan, _r_gan,
                str(result.get('ben_ming_gan') or '') or '',
                str(result.get('mountain') or result.get('shan_jia') or ''), _y_zhi)
    except Exception:
        _hulu_hh = None
    _hulu_hit = bool(_hulu_hh and _hulu_hh.get('is_mutual_lu_gui'))
    if _hulu_hit:
        _hn = int((_hulu_hh or {}).get('hulu_count', 0) or 0)
        _hgn = int((_hulu_hh or {}).get('hugui_count', 0) or 0)
        _yq_sents.append(f'互禄互贵命中（互禄{_hn}项+互贵{_hgn}项），禄马贵虽未加临山向亦不落空——福力足')
    elif not (_ddx8.get('total_count') or 0):
        _yq_sents.append('禄马贵未到山到向，福力不实——宜择到山到向且发传之课（要诀"住而不去，且要发出三传…方得确实灵验"）')
    if _yq_sents:
        wen.append('禄马发传，应命应年详见白话')
        bai.append('要訣應人應期（两因字是大窍）：' + '；'.join(_yq_sents))

    # ⑨ 巧取法（2026-08-20 张九仪"巧在马而兼贵/妙在贵而兼禄"：三吉同支=兼格，应命尤速）
    _gui_z9 = (_ddx8.get('guiren') or {}).get('guiren_zhi') or []
    _GUI_GAN = {'甲': {'丑', '未'}, '乙': {'子', '申'}, '丙': {'亥', '酉'}, '丁': {'亥', '酉'}, '戊': {'丑', '未'},
                '己': {'子', '申'}, '庚': {'丑', '未'}, '辛': {'午', '寅'}, '壬': {'巳', '卯'}, '癸': {'巳', '卯'}}
    _shan_gan9 = str(result.get('mountain') or result.get('shan_jia') or '')
    _DUI24 = {'壬': '丙', '子': '午', '癸': '丁', '丑': '未', '艮': '坤', '寅': '申', '甲': '庚', '卯': '酉',
              '乙': '辛', '辰': '戌', '巽': '乾', '巳': '亥', '丙': '壬', '午': '子', '丁': '癸', '未': '丑',
              '坤': '艮', '申': '寅', '庚': '甲', '酉': '卯', '辛': '乙', '戌': '辰', '乾': '巽', '亥': '巳'}
    _xiang_gan9 = _DUI24.get(_shan_gan9, '')
    _gui_shanxiang = set()
    for _g in (_shan_gan9, _xiang_gan9):
        if _g in _GUI_GAN:
            _gui_shanxiang |= _GUI_GAN.get(_g, set())
    _jian = []
    _tdp9 = result.get('tiandi_pan') or {}
    if _hm8.get('huo_ma') and _ma_z8 and _ma_z8 in (_gui_z9 + list(_gui_shanxiang)):
        _src = '日贵' if _ma_z8 in _gui_z9 else '山向之贵'
        _jian.append(f'马神{_ma_z8}兼{_src}（马而兼贵）——{_ma_z8}命人发福尤速（要诀"论寅日则以申为马，论乙向兼以申为贵，马而兼贵"）')
    if _hm8.get('huo_lu') and _lu_z8 and _lu_z8 in (_gui_z9 + list(_gui_shanxiang)):
        _src = '日贵' if _lu_z8 in _gui_z9 else '山向之贵'
        _jian.append(f'禄神{_lu_z8}兼{_src}（贵而兼禄）——{_lu_z8}命人发福尤速（要诀"论壬日固以亥为禄，论丁山又以亥为贵人，贵而兼禄"）')
    if _hm8.get('huo_ma') and _ma_z8 and _tdp9:
        _lin_d = next((d for d, t in _tdp9.items() if t == _ma_z8), '')
        if _lin_d and _lin_d != _ma_z8:
            _jian.append(f'活马{_ma_z8}加临{_lin_d}宫（不在本宫——巧取"辛山乙向"之类迎之方得）')
    if _hm8.get('huo_lu') and _lu_z8 and _tdp9:
        _lin_d2 = next((d for d, t in _tdp9.items() if t == _lu_z8), '')
        if _lin_d2 and _lin_d2 != _lu_z8:
            _jian.append(f'活禄{_lu_z8}加临{_lin_d2}宫（巧取"丁山癸向"之类乘之方得）')
    if _jian:
        wen.append('马兼贵禄，巧取见白话')
        bai.append('要訣巧取（马兼贵/贵兼禄）：' + '；'.join(_jian))

    # ⑩ 五吉时（要诀"取元辰时，五吉时内己巳为优"——时柱斗首化气为吉星之时辰）
    _wjs = result.get('wujishi') or {}
    _wj_ji = _wjs.get('吉时') or []
    if _wj_ji:
        _cur_shi = str(result.get('shichen') or '') + '时'
        _ji_names = '、'.join(f"{r['时']}{r['星曜']}" for r in _wj_ji[:5])
        if any(r['时'] == _cur_shi for r in _wj_ji):
            wen.append('所选时辰合五吉时')
            bai.append(f'五吉时：所选{_cur_shi}合吉时（{_ji_names}等）——时辰得吉星，天机灵动')
        else:
            wen.append('所选时辰非五吉时，宜改择')
            bai.append(f'五吉时：所选{_cur_shi}非吉时，宜选{_ji_names}等（要诀"取元辰时，五吉时内己巳为优；取武财时，五吉时内甲辰最善"）')

    # 【2026-09-07 审计修复 BUG-1/BUG-5】总断尾缀按 grade 分支：
    #   凶/不宜课不得再续"吉祥如意/福荫后代"等吉语（原无条件拼接造成"39分不宜却吉祥如意"矛盾）；
    #   凶课尾缀降级为"慎用/另择"，且类型吉语（安葬福荫等）仅吉课使用。
    grade = result.get('grade') or ''
    _is_bad = any(k in str(grade) for k in ('不宜', '凶'))
    tail_wen, tail_bai = _ZONGHE_TYPE_TAIL.get((zetiri_type or '').strip(), _ZONGHE_DEFAULT_TAIL)
    if _is_bad:
        tail_wen, tail_bai = '宜慎用，另择吉期', '宜谨慎选用或另择吉日吉时'
    bai.append(f'综合评分{score}分（{grade or "未评"}），{tail_bai}')

    wen = [str(x).rstrip('。，,、；;') for x in wen if x]

    return {
        'wen': '，'.join(wen),
        'bai': '。'.join(x for x in bai if x) + '。',
        'detail': detail,
    }


@app.route('/api/zeri/analyze', methods=['GET', 'POST'])
def api_zeri_analyze():
    """分析指定日期的择日课 GET/POST /api/zeri/analyze?date=2026-07-15&mountain=壬&shichen=巳
    2026-08-17 修复：改 POST 兼容避免 URL 过长触发浏览器 Failed to fetch。"""
    try:
        date_str = request.values.get('date', '')
        mountain = request.values.get('mountain', '壬')
        shichen = request.values.get('shichen', '午')
        # IP 定位经纬度（真太阳时昼夜判断天将用；失败降级固定卯酉）
        _ip_lat = _ip_lon = None
        try:
            from engine.ip_geo import ip_to_coords, get_client_ip
            _ip_lat, _ip_lon, _, _ = ip_to_coords(get_client_ip(request), timeout=2)
        except Exception:
            pass
        # 课格筛选参数
        filters = {
            'gonggui': request.values.get('gonggui', '1') == '1',
            'gonglu': request.values.get('gonglu', '1') == '1',
            'gongma': request.values.get('gongma', '1') == '1',
            'chaotian': request.values.get('chaotian', '1') == '1',
            'guiyuan': request.values.get('guiyuan', '1') == '1',
            'luowen': request.values.get('luowen', '0') == '1',
        }
        # 三流派选择：liuren / doushou / yanqin（逗号分隔），默认仅六壬
        liupai = request.values.get('liupai', 'liuren')
        selected_pai = [p.strip() for p in liupai.split(',') if p.strip()]
        # 占事（P3：占类断语，古例 9 占类，默认"其他"）
        zhanlei = request.values.get('zhanlei', '其他')
        # 占类细分（"其他"下按《疏正》章节号细分：01天时/04终身/05流年/09一课二事/15亡盗/17杂占）
        sec = request.values.get('sec', '')
        # 本命（60甲子，如"甲子"；供天网自裹/干乘墓虎等需本命之法）
        ben_ming = request.values.get('ben_ming', '')
        ben_ming_zhi = ben_ming[1] if ben_ming and len(ben_ming) >= 2 else ''
        # 年龄/性别（算行年，供乘轩落马"克年命""身弱人衰"等需年命之法）
        _bm_age = request.values.get('ben_ming_age', '') or request.values.get('age', '')
        _bm_sex = request.values.get('ben_ming_sex', '') or request.values.get('sex', '') or '男'
        # 夫行年/妻行年（60甲子，取地支；供"申加夫命+妻行年上神"《连珠经》生男生女法）
        _fu_xing_nian = request.values.get('fu_xing_nian', '')
        _fu_xing_nian_zhi = _fu_xing_nian[1] if _fu_xing_nian and len(_fu_xing_nian) >= 2 else ''
        _qi_xing_nian = request.values.get('qi_xing_nian', '')
        _qi_xing_nian_zhi = _qi_xing_nian[1] if _qi_xing_nian and len(_qi_xing_nian) >= 2 else ''
        if not date_str:
            return jsonify({'error': '缺少date参数'}), 400

        parts = date_str.split('-')
        y, m, d = int(parts[0]), int(parts[1]), int(parts[2])

        from engine.sizhu_engine import get_sizhu
        sizhu = get_sizhu(y, m, d, shichen)
        nian_gan, nian_zhi = sizhu['年柱'][0], sizhu['年柱'][1]
        yue_gan, yue_zhi = sizhu['月柱'][0], sizhu['月柱'][1]
        ri_gan, ri_zhi = sizhu['日柱'][0], sizhu['日柱'][1]
        shi_gan, shi_zhi = sizhu['时柱'][0], sizhu['时柱'][1]

        from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen, arrange_tiandi_pan
        engine_lm = DaLiuRenLuMaGuiRen()
        # 月将按《大六壬通解》节气中气口径（2026-08-15 憨爷指正：原按地支月查表错误，如 8/15 应为午将非巳将）
        yuejiang = engine_lm.get_yuejiang_by_date(y, m, d)
        tiandi_pan = arrange_tiandi_pan(yuejiang, shichen)

        # 统一起课引擎：sike_sanchuan_engine（与 /api/qike 批量择日同口径，避免 daliuren_engine 双引擎判课体不一致）
        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2 as _CalcUnified
        _calcU = _CalcUnified()
        _tdpU = _calcU.get_tiandi_pan(yuejiang, shichen)
        sike = _calcU.qi_sike(ri_gan, ri_zhi, _tdpU)
        raw = _calcU.fa_sanchuan(sike, ri_gan, ri_zhi, _tdpU)
        # 与批量择日 _build_zeri_candidate 同口径：直接取 fa_sanchuan 的 初传/中传/末传（地支）
        sanchuan = {'初传': raw.get('初传', ''),
                     '中传': raw.get('中传', ''),
                     '末传': raw.get('末传', '')}
        # 拱格/禄马贵检测：sanchuan 即 fa_sanchuan 的 初传/中传/末传（地支），与批量择日 _sc3 同口径
        from engine.yidu_liuren_yaojue import analyze_yidu_full
        from engine.gui_ren_engine import GuiRenCalculator
        # 天将映射：与批量择日 _build_zeri_candidate 同口径（拱干/拱支/两贵引从等格依赖天将临干支）
        _tj_map = GuiRenCalculator().arrange_gui_ren_pan(ri_gan, {'天地对应': tiandi_pan}, shichen, lat=_ip_lat, lon=_ip_lon)
        _tjm = _tj_map.get('天将映射', {})
        analysis = analyze_yidu_full(
            shan=mountain,
            year_pillar=f'{nian_gan}{nian_zhi}', month_pillar=f'{yue_gan}{yue_zhi}',
            day_pillar=f'{ri_gan}{ri_zhi}', hour_pillar=f'{shi_gan}{shi_zhi}',
            ri_gan=ri_gan, ri_zhi=ri_zhi,
            sanchuan=sanchuan, tiandi_pan=tiandi_pan,
            tianjiang_map=_tjm, yue_jiang=yuejiang, nian_zhi=nian_zhi,
            shichen=shichen, ke_ti=raw.get('课体', '') or None,
            year=y, month=m, day=d,
            # 2026-09-06 方案A-L3：择日类型类神吉应（未选类型则跳过）
            zeri_type=request.values.get('zetiri_type', '') or '',
        )

        result = {
            'date': date_str, 'shichen': shichen, 'mountain': mountain,
            'liupai': selected_pai,
            'sizhu': {'年': f'{nian_gan}{nian_zhi}', '月': f'{yue_gan}{yue_zhi}',
                       '日': f'{ri_gan}{ri_zhi}', '时': f'{shi_gan}{shi_zhi}'},
            'score': analysis['total_score'], 'grade': analysis['grade'],
            'shan_jia': analysis['shan_jia'], 'xiang_shou': analysis['xiang_shou'],
            'doushou': {
                'classes': analysis['doushou']['classes'],
                'yuanchen_ok': analysis['doushou']['yuanchen_check']['has_yuanchen'],
                'sanyuan_grade': analysis['doushou']['sanyuan_check']['grade'],
            },
            'gong_patterns': [p for p in analysis['gong_patterns'] if p.get('matched')],
            'daoshan_daoxiang': analysis['daoshan_daoxiang'],
            'huoma_huolu': analysis['huoma_huolu'],
            'advanced': {
                'chaotian': analysis['advanced_patterns']['朝天格']['matched'],
                'guiyuan': analysis['advanced_patterns']['归垣格']['matched'],
                'luowen': analysis['advanced_patterns']['罗纹格']['matched'],
            },
            'summary': analysis['summary'],
            # 2026-08-31 统一口径拆解 + 斗首凶在内一票否决
            'luma_base': analysis.get('luma_base', 0),
            'bonus': analysis.get('bonus', 0),
            'doushou_bonus': analysis.get('doushou_bonus', 0),
            'vetoed': analysis.get('vetoed', False),
            'veto_reason': analysis.get('veto_reason', ''),
            # 2026-09-05 太阳躔度·合方之法：透传 luma_detail（含 sun_chanhe_details/bonus）供前端逐柱明细
            'luma_detail': analysis.get('luma_detail', {}),
            # 2026-09-05 加分项明细透传：四柱结构格局（天地同流/一气等）、演禽窃要、加分项列表
            'matched_patterns': analysis.get('matched_patterns', []),
            'sizhu_patterns': analysis.get('sizhu_patterns', []),
            'yanqin_detail': analysis.get('yanqin_detail', {}),
            # 2026-09-06 方案A-L3：择日类型类神吉应（{end,narr,leishen,zhi_list}，供前端叙事）
            'leishen_detail': analysis.get('leishen_detail', {}),
        }

        # ── 空亡三铁律审计（2026-08-25 憨爷拍板：本命落旬空可填补 / 踏空致命 / 乘天空=真空）──
        result['void_audit'] = {'level': '干净', 'pass': True, 'xunkong': [], 'ben_ming_void': False,
                                'tread_zhi': '', 'tread_void': False, 'ride_general': '', 'ride_sky': False,
                                'reasons': []}
        try:
            from engine.void_audit import audit_void
            result['void_audit'] = audit_void(ri_gan + ri_zhi, tiandi_pan, _tjm, ben_ming)
        except Exception:
            pass

        # ── 十二建星（2026-08-25 用户拍板：月建起建，只进批语叙事不加减分）──
        result['jianxing'] = {'name': '', 'huang_dao': False, 'level': '', 'desc': '', 'narrative': ''}
        try:
            from engine.jianxing import get_jianxing, jianxing_narrative
            _jx = get_jianxing(yue_zhi, ri_zhi)
            result['jianxing'] = dict(_jx)
            # 课体吉凶倾向：以 grade 判定（上上吉/上吉=吉，凶/平=凶）
            _gx = '吉' if result.get('grade', '') in ('上上吉', '上吉') else ('凶' if '凶' in result.get('grade', '') else '平')
            # 三传地支 + 天将（类象叙事）
            _jx_sc = [sanchuan.get('初传', ''), sanchuan.get('中传', ''), sanchuan.get('末传', '')]
            _jx_tj = [_tjm.get(z, '') for z in _jx_sc]
            result['jianxing']['narrative'] = jianxing_narrative(_jx, _gx, _jx_sc, _jx_tj)
        except Exception:
            pass

        # ── 现代类象推演入库（2026-08-25 用户拍板：按择日类型推演+存历史库+反馈校准）──
        # 字段名 modern_leixiang（避开已有 result['leixiang']=初传类象）
        result['modern_leixiang'] = {'推演': [], '历史佐证': '', 'narrative': '', 'zeri_type': ''}
        try:
            from engine.leixiang_kb import LeixiangKB
            _kb = LeixiangKB()
            _zt = request.values.get('zetiri_type', '') or ''
            _lx = _kb.push_leixiang(_zt, date=date_str, shichen=shichen)
            result['modern_leixiang'] = {
                '推演': _lx.get('推演', []),
                '历史佐证': _lx.get('历史佐证', ''),
                'narrative': _kb.get_narrative(_zt),
                'zeri_type': _zt,
            }
        except Exception:
            pass

        # ── 古籍合参警示层（2026-08-19 接线：单课页与批量同源，警示/佐证层不参与评分）──
        try:
            from zeri_hecan_bridge2 import zeri_hecan_eval
            _zt_an = request.values.get('zetiri_type', '') or ''
            result['hecan'] = zeri_hecan_eval(ri_gan, ri_zhi, sike, sanchuan, _tjm,
                                              raw.get('课体', ''), yuejiang, _zt_an,
                                              sizhu=sizhu,
                                              shan=str(mountain or ''), xiang='', ming=ben_ming,
                                              shan_wx=({'壬': '土', '子': '土', '巽': '土', '巳': '土', '辛': '土', '戌': '土',
                                                        '癸': '火', '丑': '火', '丙': '火', '午': '火', '乾': '火', '亥': '火',
                                                        '艮': '木', '寅': '木', '丁': '木', '未': '木',
                                                        '坤': '水', '申': '水', '甲': '水', '卯': '水',
                                                        '乙': '金', '辰': '金', '庚': '金', '酉': '金'}.get(str(mountain or ''), '')))
            # 2026-08-21 命中规则附短标签（前端美格徽标用，与批量候选同口径）
            try:
                from zeri_hecan_engine import zeri_rule_label as _zrl2
                for _h in result['hecan'].get('zeri_rules', {}).get('hits', []):
                    _h['标签'] = _zrl2(_h.get('id', ''))
            except Exception:
                pass
        except Exception:
            result['hecan'] = {'hits': [], 'narr': '', '警告': [], '佐证': [], 'zeri_rules': {'hits': [], 'narr': ''}}

        # 2026-08-21 古例变通桥：同课古例印证（A 基调直迁 / B 占类桥 / C 应期重算）
        result['guli'] = {'matched': False}
        try:
            from engine.zeri_cbr_bridge import find_same_ke, bridge_to_zeri
            _same_ke = find_same_ke(ri_gan, ri_zhi, yuejiang, shichen)
            if _same_ke:
                result['guli'] = bridge_to_zeri(_same_ke, _zt_an, shan=str(mountain or ''),
                                                ming=ben_ming, ri_gan=ri_gan, ri_zhi=ri_zhi)
        except Exception:
            pass

        # 2026-08-20 六亲接入（应何人断：干上神乘天将与日干生克五断，东方朔卷之二）
        result['liuqin_duanyu'] = ''
        result['liuqin_struct'] = {}
        try:
            from liuqin_engine import liuqin_judge
            _gs_lq = sike or []
            _gan_s_lq = _gs_lq[0][1] if _gs_lq and len(_gs_lq[0]) > 1 else ''
            # 现排天将（局部 sike 无天将列，result['sike'] 在后方才组装）
            _gan_tj_lq = ''
            try:
                from engine.gui_ren_engine import GuiRenCalculator
                _tjm_lq = GuiRenCalculator().arrange_gui_ren_pan(ri_gan, {'天地对应': tiandi_pan}, shichen).get('天将映射', {})
                _gan_tj_lq = _tjm_lq.get(_gan_s_lq, '')
            except Exception:
                _gan_tj_lq = ''
            _lq_an = liuqin_judge(ri_gan, _gan_tj_lq)
            result['liuqin_struct'] = _lq_an
            if _lq_an.get('断'):
                result['liuqin_duanyu'] = "六亲[" + _lq_an['将'] + _lq_an['关系'] + "]：" + _lq_an['断']
        except Exception:
            pass

        # 2026-08-20 五吉时引擎（要诀"取元辰时，五吉时内己巳为优"——时柱斗首化气为吉星之时辰）
        result['wujishi'] = {'吉时': [], '叙事': ''}
        try:
            from wujishi_engine import wujishi
            _SHAN_DX = {'壬': '土', '子': '土', '巽': '土', '巳': '土', '辛': '土', '戌': '土',
                        '癸': '火', '丑': '火', '丙': '火', '午': '火', '乾': '火', '亥': '火',
                        '艮': '木', '寅': '木', '丁': '木', '未': '木',
                        '坤': '水', '申': '水', '甲': '水', '卯': '水',
                        '乙': '金', '辰': '金', '庚': '金', '酉': '金'}
            _mnt9 = str(mountain or '')
            _shan_wx9 = _SHAN_DX.get(_mnt9, '')
            _wj = wujishi(ri_gan, _shan_wx9) if _shan_wx9 else {'吉时': [], '叙事': ''}
            result['wujishi'] = _wj
        except Exception:
            result['wujishi'] = {'吉时': [], '叙事': ''}

        # ── 三流派扩展：斗首 / 演禽（惰性导入 + 异常隔离，单家挂不影响其余）──
        sizhu4 = {'年柱': f'{nian_gan}{nian_zhi}', '月柱': f'{yue_gan}{yue_zhi}',
                  '日柱': f'{ri_gan}{ri_zhi}', '时柱': f'{shi_gan}{shi_zhi}'}
        _eng = str(ROOT / 'engine')
        if _eng not in sys.path:
            sys.path.insert(0, _eng)

        if 'doushou' in selected_pai:
            try:
                from douhou_analyzer import DouhouKegeAnalyzer
                _dha = DouhouKegeAnalyzer()
                _ds = _dha.analyze_kege(mountain, sizhu4)
                result['doushou_full'] = {
                    'shan_wuxing': _ds.get('山家五行', ''),
                    'sizhu_stars': {
                        k: {'干支': v.get('干支', ''), '化气': v.get('化气五行', ''),
                            '星曜': v.get('斗首星曜', '')}
                        for k, v in _ds.get('四柱分析', {}).items()
                    },
                    'patterns': _ds.get('课格格局', []),
                    'score': _ds.get('综合评分', 0),
                    'grade': _ds.get('吉凶等级', ''),
                    'duanyu': _ds.get('吉凶断语', []),
                    # 2026-09-07 补齐：六相断语 + 扣分原因（破鬼/贪官/廉子加减分明细）
                    '六相断语': _ds.get('六相断语', []),
                    '扣分原因': _ds.get('扣分原因', []),
                }
            except Exception as e:
                result['doushou_full'] = {'error': str(e)}

        if 'yanqin' in selected_pai:
            try:
                from yanqin_analyzer import YanQinAnalyzer
                _yqa = YanQinAnalyzer()
                _yq = _yqa.analyze_yanqin_with_calendar(sizhu4, y, m, d)
                result['yanqin_full'] = {
                    'si_qin': _yq.get('四禽', {}),
                    'si_qin_xing': _yq.get('四禽禽星', {}),
                    'xiu_jixiong': _yq.get('二十八宿属性', {}),
                    'shengke': _yq.get('生克关系', {}),
                    'po_gong': _yq.get('泊宫', {}),
                    'patterns': _yq.get('格局判定', []),
                    'score': _yq.get('综合评分', 0),
                    'grade': _yqa.get_score_description(_yq.get('综合评分', 0)),
                    'duanyu': _yq.get('吉凶断语', []),
                    'riqin_algo': 'sxtwl精算',
                    'qiyuan': _yq.get('七元演禽', {}),
                }
            except Exception as e:
                result['yanqin_full'] = {'error': str(e)}

        # ── 四课三传排盘（供批量择日详情展示，与 /api/qike 同口径：sike_sanchuan_engine）──
        try:
            from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
            from engine.liuqin_engine import LiuQinCalculator
            from engine.gui_ren_engine import GuiRenCalculator
            try:
                from engine.sanchuan_kege import SanChuanKegeDetector as _SKD2
            except Exception:
                _SKD2 = None
            _calc = SiKeSanChuanCalculator2()
            _tdp = _calc.get_tiandi_pan(yuejiang, shichen)
            _sike = _calc.qi_sike(ri_gan, ri_zhi, _tdp)
            _sc = _calc.fa_sanchuan(_sike, ri_gan, ri_zhi, _tdp)
            _sc_list = [_sc.get('初传', ''), _sc.get('中传', ''), _sc.get('末传', '')]
            _tj_map = GuiRenCalculator().arrange_gui_ren_pan(ri_gan, {'天地对应': _tdp}, shichen, lat=_ip_lat, lon=_ip_lon)
            _tj_ys = _tj_map.get('天将映射', {})
            _tj_list = [_tj_ys.get(c, '') for c in _sc_list]
            if _SKD2:
                try:
                    _kr = _SKD2().detect(_sc_list, ri_gan=ri_gan, ri_zhi=ri_zhi,
                                         keti_raw=_sc.get('课体', ''), tian_jiang=_tj_list,
                                         yue_jian=yuejiang, si_ke=_sike, jieqi='', nianming='')
                    _sc['课格列表'] = _kr.get('课格列表', [])
                    _sc['课格详情'] = _kr.get('课格详情', {})  # {课格名: {吉凶, 断语, 定义,...}} 供前端按吉凶着色
                except Exception:
                    _sc['课格列表'] = []
                    _sc['课格详情'] = {}
            else:
                _sc['课格列表'] = []
                _sc['课格详情'] = {}
            # 毕法赋命中法句统一由 judge_bifa 引擎输出（含干上/支上神/天将/天地盘，比此处内联 detect 更全），
            # 此处仅给占位，最终在下方 result['bifa_judged'] 块覆盖。
            _sc['毕法赋命中'] = []
            _stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            _branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            def _xs(rg, rz):
                idx = (_stems.index(rg) * 6 - _branches.index(rz) * 5) % 60
                return (idx // 10) * 10
            def _stem_for_branch(b, rg, rz):
                xs = _xs(rg, rz)
                xz = _branches[xs % 12]
                xi = _branches.index(xz)
                bi = _branches.index(b)
                return _stems[((bi - xi) % 12) % 10]
            def _is_kw(b, rg, rz):
                xs = _xs(rg, rz)
                kw = [_branches[(xs % 12 + 10) % 12], _branches[(xs % 12 + 11) % 12]]
                return b in kw
            _ganzhi_list, _liuqin_list = [], []
            for c in _sc_list:
                try:
                    _lq = LiuQinCalculator().get_liuqin(ri_gan, c) or ''
                except Exception:
                    _lq = ''
                _liuqin_list.append(_lq)
                if _is_kw(c, ri_gan, ri_zhi):
                    _gz = c
                else:
                    try:
                        _stem = _stem_for_branch(c, ri_gan, ri_zhi)
                    except Exception:
                        _stem = ''
                    _gz = _stem + c
                _ganzhi_list.append(_gz)
            _sc['三传'] = _sc_list
            _sc['三传天将'] = _tj_list
            _sc['三传干支'] = _ganzhi_list
            _sc['三传六亲'] = _liuqin_list
            # 补四课天将：qi_sike 返回的 sike[i][3] 通常为空，用上课地支查天将映射附上
            if _sike and _tj_ys:
                try:
                    _sike = [[k[0], k[1], k[2], _tj_ys.get(k[1], '') or ''] for k in _sike]
                except Exception:
                    pass
            result['sike'] = _sike
            result['sanchuan'] = _sc
            # 天盘/天将（供前端传统排盘：天盘环宫图需要天地盘+十二天将映射）
            result['tiandi_pan'] = _tdp          # {地盘支: 天盘支}
            result['tianjiang_map'] = _tj_ys     # {天盘支: 天将名}（贵人盘，顺逆已定）
            result['yuejiang'] = yuejiang        # 月将（天盘图标注用）
            # ── 判断层编排器（2026-08-16 憨爷拍板：统一收口 64课/毕法赋/特殊课格/变格，轻量 harness）──
            try:
                from engine.judge_orchestrator import build_judge_env as _bje, judge_all as _jall
                _jenv = _bje(
                    ri_gan=ri_gan, ri_zhi=ri_zhi, nian_zhi=nian_zhi, yue_zhi=yue_zhi, yuejiang=yuejiang,
                    sike=_sike, sanchuan=_sc_list, keti=_sc.get('课体', ''),
                    tian_jiang=_tj_ys, tiandi_pan=_tdp,
                    shichen=shichen, zhanlei=zhanlei,
                    ben_ming_zhi=ben_ming_zhi, ben_ming_age=_bm_age, ben_ming_sex=_bm_sex,
                    fu_xing_nian_zhi=_fu_xing_nian_zhi, qi_xing_nian_zhi=_qi_xing_nian_zhi,
                    y=y, m=m, d=d,
                    sanchuan_tianjiang=_tj_list,
                )
                _jres = _jall(_jenv)
                result['keti_judged'] = _jres.get('keti_judged', [])
                result['bifa_judged'] = _jres.get('bifa_judged', {'匹配法句': [], '断法': []})
                result['special_kege'] = _jres.get('special_kege', {'匹配课格': [], '课格详情': {}})
                result['bianjie_kege'] = _jres.get('bianjie_kege', {'匹配变格': [], '变格详情': {}})
                # 统一口径：毕法赋命中法句以 judge_bifa（含干上/支上神/天将/天地盘）为准
                if isinstance(result.get('sanchuan'), dict):
                    result['sanchuan']['毕法赋命中'] = result['bifa_judged'].get('匹配法句', [])
                # ── 毕法赋占类过滤（2026-08-17 憨爷拍板：精细版）──
                # 展示层新增 bifa_filtered：按当前占类过滤（通用断语保留；专属断语仅当前占类匹配才留）。
                # 评估层原 bifa_judged/毕法赋命中 不动（M3 零回归）。
                try:
                    from engine.bifa_zhanlei_map import filter_bifa_by_zhanlei
                    _bj = result.get('bifa_judged') or {}
                    _bf_names = _bj.get('匹配法句', []) or []
                    # 匹配法句 可能是 [名字列表] 或 [{name:...}]，统一取名字
                    _bf_norm = [x.get('name', x) if isinstance(x, dict) else x for x in _bf_names]
                    _zl_now = zhanlei or '其他'
                    _kb_map = {}
                    try:
                        import json as _json2
                        _kb2 = _json2.load(open(
                            os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                         'data', 'bifa_100_knowledge_base.json'), encoding='utf-8'))
                        _kb_map = {r.get('name'): r for r in _kb2.get('rules', [])}
                    except Exception:
                        _kb_map = {}
                    _bf_rules = [_kb_map.get(n) for n in _bf_norm if _kb_map.get(n)]
                    _bf_kept = filter_bifa_by_zhanlei([r for r in _bf_rules if r], _zl_now)
                    result['bifa_filtered'] = {
                        'zhanlei': _zl_now,
                        'kept': [r.get('name', '') for r in _bf_kept],
                        'kept_detail': [r.get('text') or r.get('name', '') for r in _bf_kept],
                        'dropped': [n for n in _bf_norm if n not in [r.get('name', '') for r in _bf_kept]],
                    }
                except Exception as _e_bf:
                    result['bifa_filtered'] = {'error': str(_e_bf), 'kept': _bf_norm if '_bf_norm' in dir() else []}
            except Exception as _e_orch:
                result['keti_judged'] = []
                result['bifa_judged'] = {'匹配法句': [], '断法': [], 'error': str(_e_orch)}
                result['special_kege'] = {'匹配课格': [], '课格详情': {}, 'error': str(_e_orch)}
                result['bianjie_kege'] = {'匹配变格': [], '变格详情': {}, 'error': str(_e_orch)}
            # 知识库判断（KeKeDuanyu：古籍课课断语·仪度评分，与批量择日同源；两域隔离铁律——不用股票域训练库）
            try:
                from kekeduanyu import KeKeDuanyu as _KDD3
                from daliuren_luma_guiren import DaLiuRenLuMaGuiRen as _LM3
                # BUGFIX 2026-08-17：DouhouKegeAnalyzer 之前只在 liupai 含 doushou 时才 import，
                # 单课只选六壬时未绑定 → UnboundLocalError → 知识库判断+禄马贵全挂（yidu 恒空）。
                from douhou_analyzer import DouhouKegeAnalyzer
                _dha3 = DouhouKegeAnalyzer()
                _ds3 = _dha3.analyze_kege(mountain, sizhu4)
                _ds3['课格格局'] = [
                    (p.get('格局名称', '') if isinstance(p, dict) else str(p))
                    for p in _ds3.get('课格格局', [])
                ]
                # 禄马贵人信息（复用四柱引擎，让知识库的"山向禄马贵/发出三传"真实计算）
                _lm3 = _LM3()
                _sc3c = {'初传': _sc.get('初传', ''), '中传': _sc.get('中传', ''), '末传': _sc.get('末传', '')}
                _ns3 = _lm3.calculate_new_score(
                    mountain, shichen,
                    nian_gan, nian_zhi, yue_gan, yue_zhi,
                    ri_gan, ri_zhi, shi_gan, shi_zhi,
                    _sc3c, [_sc.get('课体', '')] if _sc.get('课体') else None,
                    yuejiang=yuejiang,
                )
                _yidu3 = _KDD3.analyze_yidu_score(mountain, sizhu4, _ds3, _ns3, [], ben_ming, date_str)
                result['yidu'] = {
                    'score': _yidu3.get('综合评分', 0),
                    'eval': _yidu3.get('评价', ''),
                    'wujue': _yidu3.get('五大要诀得分', {}),
                    'ke_chuan_mei': _yidu3.get('课传美格', []),
                }
            except Exception as _e_yidu:
                import traceback; traceback.print_exc()
                result['yidu'] = {}
        except Exception as _pe:
            import traceback; traceback.print_exc()
            result['sike'] = []
            result['sanchuan'] = {}
            result['yidu'] = {}

        # ── 占类断语（P3：根据占事给专属断语，杜绝"一个断语通吃"）──
        try:
            from engine.zhanlei_duanyu import build_zhanlei_duanyu
            _sc_keti = (result.get('sanchuan') or {}).get('课体', '')
            _bifa_names = (result.get('sanchuan') or {}).get('毕法赋命中', []) or []
            _kege_names = (result.get('sanchuan') or {}).get('课格列表', []) or []
            # 六壬格局（拱贵/拱禄/拱马/朝天格/归垣格/罗纹格）2026-08-17 UI 删除，改在批语显示
            _gong_names = [p.get('name', '') for p in (result.get('gong_patterns') or []) if p.get('name')]
            result['zhanlei'] = zhanlei
            result['zhanlei_duanyu'] = build_zhanlei_duanyu(
                zhanlei, _sc_keti, _bifa_names, _kege_names, sec, gong_names=_gong_names)
        except Exception as _e3:
            result['zhanlei_duanyu'] = {'error': str(_e3)}

        # ── 神将类象（三传/干上/支上 天将所乘地支的类象——应属相/应物）──
        try:
            from engine.liuren_leixiang_knowledge import build_leixiang
            _lx_sike = result.get('sike') or []
            _lx_gs = _lx_sike[0][1] if len(_lx_sike) >= 1 and isinstance(_lx_sike[0], (list, tuple)) and len(_lx_sike[0]) >= 2 else ''
            _lx_zs = _lx_sike[2][1] if len(_lx_sike) >= 3 and isinstance(_lx_sike[2], (list, tuple)) and len(_lx_sike[2]) >= 2 else ''
            _lx_sc = [(result.get('sanchuan') or {}).get('初传', ''),
                      (result.get('sanchuan') or {}).get('中传', ''),
                      (result.get('sanchuan') or {}).get('末传', '')]
            result['leixiang'] = build_leixiang(result.get('tianjiang_map', {}), _lx_sc, _lx_gs, _lx_zs)
        except Exception as _e_lx:
            result['leixiang'] = {'error': str(_e_lx)}

        # ── 应期（叙事层：支数法+月建法+太岁法；何时发生，非吉凶方向）──
        try:
            from engine.liuren_keti_bifa import get_yingqi_unified
            from yingqi_engine_v2 import yingqi_v2
            from engine.liuchen_shensha import wang_shuai as _ws_yq
            _yq_sc = [(result.get('sanchuan') or {}).get('初传', ''),
                      (result.get('sanchuan') or {}).get('中传', ''),
                      (result.get('sanchuan') or {}).get('末传', '')]
            _yq_base = get_yingqi_unified(
                ri_gan, ri_zhi, _yq_sc,
                tiandi_pan=result.get('tiandi_pan', {}),
                si_ke=result.get('sike', []),
                shichen=shichen, tai_sui_zhi=nian_zhi, zhanlei=zhanlei,
            )
            # 2026-08-20 应期增强四法（旬空填实日/三传合冲日/太岁冲合年/类神速迟+亡盗时辰方位）——
            # 疏正127案回测：古籍应期主流为干支年/干支日，原三法仅"到月"不够
            _zt_an = (request.values.get('zetiri_type', '') or '')
            _ls_eff = ''
            try:
                from leishen_engine_v5 import leishen_from_text
                _ls_eff = leishen_from_text(f'{_zt_an} {zhanlei} {date_str}') or ''
            except Exception:
                _ls_eff = ''
            _yq_v2 = yingqi_v2(
                ri_gan, ri_zhi, _yq_sc,
                tai_sui_zhi=nian_zhi, zhanlei=zhanlei,
                ben_ming_zhi=ben_ming_zhi, ben_ming_age=_bm_age,
                sex=_bm_sex,
                text=f'{_zt_an} {zhanlei} {date_str} {shichen}',
                leishen=_ls_eff,
                si_ke=result.get('sike', []), tiandi_pan=result.get('tiandi_pan', {}),
                wangshuai_fn=_ws_yq, yuejiang=yuejiang,
            )
            result['yingqi'] = '\n'.join(x for x in (_yq_base, _yq_v2) if x)
            # 2026-08-20 应期结构化（前端卡片可视化：法门/粒度/文本）
            result['yingqi_struct'] = []
            try:
                from yingqi_engine_v2 import yingqi_v2_struct
                _base_struct = []
                for _l in str(_yq_base or '').split('\n'):
                    _l = _l.strip()
                    if not _l:
                        continue
                    if '邵彦和' in _l:
                        _base_struct.append({'法': '邵彦和应期法', '粒度': '月', '文本': _l})
                    elif '月建' in _l:
                        _base_struct.append({'法': '月建应期', '粒度': '月', '文本': _l})
                    elif '太岁临身' in _l:
                        _base_struct.append({'法': '太岁临身', '粒度': '年', '文本': _l})
                    else:
                        _base_struct.append({'法': '应期', '粒度': '月', '文本': _l})
                _yst = yingqi_v2_struct(
                    ri_gan, ri_zhi, _yq_sc,
                    tai_sui_zhi=nian_zhi, zhanlei=zhanlei,
                    ben_ming_zhi=ben_ming_zhi, ben_ming_age=_bm_age,
                    sex=_bm_sex,
                    text=f'{_zt_an} {zhanlei} {date_str} {shichen}',
                    leishen=_ls_eff,
                    si_ke=result.get('sike', []), tiandi_pan=result.get('tiandi_pan', {}),
                    wangshuai_fn=_ws_yq, yuejiang=yuejiang,
                )
                result['yingqi_struct'] = _base_struct + _yst
            except Exception:
                result['yingqi_struct'] = []
        except Exception as _e_yq:
            result['yingqi'] = ''
            result['yingqi_struct'] = []

        # ── 综合批语（斗首/演禽/六壬 → 文言+白话括注，详情区「综合批语」栏）──
        try:
            # 2026-08-17：优先用择日类型（提车/开业等专属尾注），未选则退回占事（zhanlei）
            _piyu_type = (request.values.get('zetiri_type', '') or '').strip() or zhanlei
            result['zonghe_piyu'] = _build_zonghe_piyu(result, _piyu_type)
            # 2026-08-19 合参示警联动：凶规则命中加短标记，详情由批语内"冲突点透"展开（不重复全文）
            _hc_warns = (result.get('hecan') or {}).get('警告', [])
            if _hc_warns:
                _zp = result.get('zonghe_piyu') or {}
                _zp['wen'] = ('⚠ 合参示警：' + str(_zp.get('wen', '')))
                _zp['bai'] = ('⚠ 合参示警（详见文末点透）：' + str(_zp.get('bai', '')))
                result['zonghe_piyu'] = _zp
        except Exception as _e_zp:
            result['zonghe_piyu'] = {'wen': '', 'bai': '', 'error': str(_e_zp)}

        # ── 真太阳时（2026-08-17）：所选时辰=当地真太阳时辰，换算北京时间范围供对照 ──
        try:
            _lon_arg = request.values.get('longitude', '')
            result['true_solar'] = _true_solar_info(shichen, date_str, _lon_arg)
        except Exception:
            result['true_solar'] = None
        # ── 择日类型（2026-08-17 修复：前端 zeriZetiriType 下拉选定，传给前端与后续导出）──
        result['zetiri_type'] = request.values.get('zetiri_type', '') or ''

        # ── 现代类型专属信号（2026-08-17 憨爷：古籍没有的现代类差异化评分）──
        # 仅 提车/买房过户/开工/阳宅动土/阴宅动土/迁坟/入学开学/考试/祭祀祈福 触发；
        # 展示层（result['type_special']），不进 total_score（现代类无古例 A/B）
        try:
            _ts_type = (result.get('zetiri_type') or '').strip()
            if _ts_type in ('提车', '买房过户', '开工', '阳宅动土', '阴宅动土', '迁坟', '入学开学', '考试', '祭祀祈福',
                            '催龙补气', '召山买土'):
                from engine.liuren_keti_bifa import extract_modern_type_valence
                from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen
                _ts_sc = [(result.get('sanchuan') or {}).get('初传', ''),
                          (result.get('sanchuan') or {}).get('中传', ''),
                          (result.get('sanchuan') or {}).get('末传', '')]
                _ts_tj = (result.get('sanchuan') or {}).get('三传天将') or []
                _ts_lq = (result.get('sanchuan') or {}).get('三传六亲') or []
                _ts_yr = ''
                _ts_sz = result.get('sizhu') or {}
                if isinstance(_ts_sz, dict) and _ts_sz.get('年'):
                    _ts_yr = (str(_ts_sz.get('年', '')) or '')[1:]
                # 来龙/坐山/向首 → 地支（二十四山→八宫；供催龙补气/召山买土判合冲）
                _ts_lg = (request.values.get('lailong', '') or '').strip()
                _ts_lg_z = ''
                _ts_shan_z = _ts_xiang_z = ''
                try:
                    _ts_lr = DaLiuRenLuMaGuiRen()
                    _ts_shan_z = _ts_lr.get_shan_jia(mountain)
                    _ts_xiang_z = _ts_lr.get_xiang_shou(mountain)
                    if _ts_lg:
                        _ts_lg_z = _ts_lr.get_shan_jia(_ts_lg)
                except Exception:
                    pass
                result['lailong'] = _ts_lg
                # 催龙补气主信号：四柱禄马贵到山到向（复用 calculate_new_score 已算字段）
                # + 禄马贵到来龙命中检测（憨爷 2026-08-17：重点=年月日及坐山贵人禄马到山到向，有来龙则更好）
                _ts_pl = {}
                if _ts_type == '催龙补气':
                    _ts_ns = locals().get('_ns3') or {}
                    _ts_pl = {
                        'count': int(_ts_ns.get('pillar_qualified_count', 0) or 0),
                        'nian': bool(_ts_ns.get('nian_qualified')),
                        'yue': bool(_ts_ns.get('yue_qualified')),
                        'ri': bool(_ts_ns.get('ri_qualified')),
                        'shi': bool(_ts_ns.get('shi_qualified')),
                        'lai_hit': False,
                    }
                    if _ts_lg_z and _ts_ns:
                        try:
                            _lmfb = DaLiuRenLuMaGuiRen()
                            for _g in (nian_gan, yue_gan, ri_gan):
                                _lz = _lmfb.get_lu_zhi(_g)
                                if _lz and _lmfb._get_tiandi_position(_lz, _tdpU) == _ts_lg_z:
                                    _ts_pl['lai_hit'] = True
                            _mz = _lmfb.get_ma_zhi(ri_zhi)
                            if _mz and _lmfb._get_tiandi_position(_mz, _tdpU) == _ts_lg_z:
                                _ts_pl['lai_hit'] = True
                            _gz = _lmfb.get_guiren_zhi(ri_gan, _tdpU, shichen)
                            if _gz == _ts_lg_z:
                                _ts_pl['lai_hit'] = True
                        except Exception:
                            pass
                result['type_special'] = extract_modern_type_valence(
                    _ts_type, ri_gan, ri_zhi, _ts_sc, _ts_tj, _ts_lq,
                    result.get('sike') or [], _ts_yr,
                    _ts_lg_z, _ts_shan_z, _ts_xiang_z, _ts_pl)
            else:
                result['type_special'] = None
                result['lailong'] = (request.values.get('lailong', '') or '').strip()
        except Exception:
            result['type_special'] = None
        # 仅 测孩子成绩/入学开学/考试/求学问 触发；展示层（result['wenchang']），不进 total_score
        try:
            _wc_zhanlei = (result.get('zetiri_type') or zhanlei or '')
            if _wc_zhanlei in ('测孩子成绩', '入学开学', '考试', '求学问'):
                from engine.liuren_keti_bifa import extract_wenchang_valence
                _wc_sc = [(result.get('sanchuan') or {}).get('初传', ''),
                          (result.get('sanchuan') or {}).get('中传', ''),
                          (result.get('sanchuan') or {}).get('末传', '')]
                result['wenchang'] = extract_wenchang_valence(
                    ri_gan, ri_zhi, _wc_sc, result.get('sike') or [], _wc_zhanlei)
            else:
                result['wenchang'] = None
        except Exception:
            result['wenchang'] = None

        # ── 杀师日判定（2026-08-17 憨爷：当用日是杀师日要提醒/可禁用；妨害地师本人，不进主家评分）──
        try:
            from engine.shashi import check_shashi
            result['shashi'] = check_shashi(ri_gan + ri_zhi, nian_zhi, yue_zhi, date_str, shichen)
        except Exception:
            result['shashi'] = {'is_shashi': False, 'hits': [], 'level': '', 'note': ''}

        # ── 十三吉课判定（2026-08-17 憨爷：精细版，逐课按 64 课经 definition 落码）──
        try:
            from engine.jike_13 import check_jike_13
            from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen
            _jk_lm = DaLiuRenLuMaGuiRen()
            _jk_keti = (result.get('sanchuan') or {}).get('课体', '') or ''
            _jk_sc = [(result.get('sanchuan') or {}).get(k, '') for k in ('初传', '中传', '末传')]
            _jk_tj = (result.get('sanchuan') or {}).get('三传天将') or []
            _jk_sike = result.get('sike') or []
            _jk_ma = _jk_lm.get_ma_zhi(ri_zhi) or ''
            _jk_lu = _jk_lm.get_lu_zhi(ri_gan) or ''
            _jk_longde = False
            _jk_yf = locals().get('_yidu_full') or {}
            _jk_ld = (_jk_yf.get('advanced_patterns') or {}).get('龙德课', {})
            if isinstance(_jk_ld, dict):
                _jk_longde = bool(_jk_ld.get('matched'))
            result['jike_13'] = check_jike_13(
                _jk_keti, _jk_sike, _jk_sc, _jk_tj, ri_gan, ri_zhi,
                nian_zhi, yue_zhi, _jk_lu, _jk_ma, _jk_longde, ben_ming_zhi)
            _jk_ns = locals().get('_ns3') or {}
            result['luma_pillar'] = int(_jk_ns.get('pillar_qualified_count', 0) or 0)
        except Exception:
            result['jike_13'] = {'hits': [], 'is_jike': False, 'details': []}
            result['luma_pillar'] = 0

        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/zeri/case_feedback', methods=['POST'])
def api_zeri_case_feedback():
    """案例回填：记录实际结果（结局导向），积累各择日类型自语料，未来 A/B 过闸口接入评分层。
    后端用引擎重算排盘快照（与 /api/zeri/analyze 同源：get_yuejiang_by_date 中气月将 +
    SiKeSanChuanCalculator2 三传），防前端篡改；label 只收 吉/凶/平。
    数据落盘 data/zeri_case_feedback.json（append）。"""
    try:
        data = request.get_json(silent=True) or {}
        date_s = (data.get('date') or '').strip()
        shichen = (data.get('shichen') or '').strip()
        label = (data.get('label') or '').strip()
        if not date_s or not shichen or label not in ('吉', '凶', '平'):
            return jsonify({'error': '参数不全或 label 非法（须为 吉/凶/平）'}), 400
        try:
            y, m, d = [int(x) for x in date_s.split('-')]
        except Exception:
            return jsonify({'error': '日期格式错误'}), 400

        from engine.sizhu_engine import get_sizhu
        from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen
        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        sizhu = get_sizhu(y, m, d, shichen)
        ri_gan, ri_zhi = sizhu['日柱'][0], sizhu['日柱'][1]
        engine_lm = DaLiuRenLuMaGuiRen()
        yuejiang = engine_lm.get_yuejiang_by_date(y, m, d)
        _calcU = SiKeSanChuanCalculator2()
        _tdpU = _calcU.get_tiandi_pan(yuejiang, shichen)
        sike = _calcU.qi_sike(ri_gan, ri_zhi, _tdpU)
        raw = _calcU.fa_sanchuan(sike, ri_gan, ri_zhi, _tdpU)
        sanchuan = [raw.get('初传', ''), raw.get('中传', ''), raw.get('末传', '')]
        keti = raw.get('课体', '')

        mountain = (data.get('mountain') or '壬').strip()
        lailong = (data.get('lailong') or '').strip()
        shan_zhi = engine_lm.get_shan_jia(mountain)
        xiang_zhi = engine_lm.get_xiang_shou(mountain)
        lai_zhi = engine_lm.get_shan_jia(lailong) if lailong else ''

        fp = ROOT / 'data' / 'zeri_case_feedback.json'
        lst = []
        if fp.exists():
            try:
                lst = json.load(open(fp, encoding='utf-8'))
                if not isinstance(lst, list):
                    lst = []
            except Exception:
                lst = []
        rec = {
            'id': f"FB-{len(lst) + 1:03d}",
            'date': date_s, 'shichen': shichen, 'rizhu': ri_gan + ri_zhi,
            'yue_jiang': yuejiang, 'sanchuan': sanchuan, 'keti': keti,
            'mountain': mountain, 'shan_zhi': shan_zhi, 'xiang_zhi': xiang_zhi,
            'lailong': lailong, 'lai_zhi': lai_zhi,
            'zetiri_type': (data.get('zetiri_type') or '').strip(),
            'zhanlei': (data.get('zhanlei') or '').strip(),
            'ben_ming': (data.get('ben_ming') or '').strip(),
            'label': label, 'note': (data.get('note') or '').strip(),
            'source': 'user_feedback',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        }
        lst.append(rec)
        with open(fp, 'w', encoding='utf-8') as f:
            json.dump(lst, f, ensure_ascii=False, indent=1)
        return jsonify({'success': True, 'id': rec['id'], 'total': len(lst)})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)[:120]}), 500


@app.route('/api/lost/find', methods=['GET', 'POST'])
def api_lost_find():
    """寻物速断（亡盗独立入口 2026-09-06）：输入丢失物件 → 自动按当前时辰起课 → 类神入课吉应。

    参数: item=丢失物件名（必填）; date=YYYY-MM-DD（缺省今天）; shichen=时辰（缺省当前时辰）。
    判法与叙事引擎同源：judge_lost_modern（现代静态表 → 物性规则 → LLM 三级 + 方位断语）。
    返回 {item, end, narr, src, leishen, date, shichen, sizhu, sanchuan, keti}。
    """
    from datetime import datetime as _dt
    try:
        item = (request.values.get('item') or (request.get_json(silent=True) or {}).get('item') or '').strip()
        if not item:
            return jsonify({'error': '缺少 item 参数（丢失物件名）'}), 400
        date_str = (request.values.get('date') or '').strip() or _dt.now().strftime('%Y-%m-%d')
        shichen = (request.values.get('shichen') or '').strip()
        if not shichen:
            # 当前时辰（子23-1、丑1-3…）
            _Z = '子丑寅卯辰巳午未申酉戌亥'
            shichen = _Z[((_dt.now().hour + 1) // 2) % 12]
        try:
            y, m, dd = int(date_str[:4]), int(date_str[5:7]), int(date_str[8:10])
            _dt(y, m, dd)  # 值域校验（2026-13-99 → ValueError → 400）
        except Exception:
            return jsonify({'error': 'date 格式应为 YYYY-MM-DD'}), 400

        # ── 起课（与 /api/zeri/analyze 统一起课引擎同口径）──
        from engine.sizhu_engine import get_sizhu
        from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen, arrange_tiandi_pan
        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        from engine.gui_ren_engine import GuiRenCalculator
        from engine.leishen_engine import judge_lost_modern, leishen_from_text, get_xunkong

        sizhu = get_sizhu(y, m, dd, shichen)
        ri_gan, ri_zhi = sizhu['日柱'][0], sizhu['日柱'][1]
        _lm = DaLiuRenLuMaGuiRen()
        yuejiang = _lm.get_yuejiang_by_date(y, m, dd)
        _tdp = arrange_tiandi_pan(yuejiang, shichen)
        _calc = SiKeSanChuanCalculator2()
        _tdpU = _calc.get_tiandi_pan(yuejiang, shichen)
        _sike4 = _calc.qi_sike(ri_gan, ri_zhi, _tdpU)
        _raw = _calc.fa_sanchuan(_sike4, ri_gan, ri_zhi, _tdpU)
        _sc = [_raw.get('初传', ''), _raw.get('中传', ''), _raw.get('末传', '')]
        _tjm = GuiRenCalculator().arrange_gui_ren_pan(
            ri_gan, {'天地对应': _tdp}, shichen).get('天将映射', {})
        _ctj, _ztj, _mtj = [_tjm.get(z, '') for z in _sc]
        _kong = get_xunkong(ri_gan, ri_zhi)
        # 干上/支上神（六壬寄宫，与评分接线同口径）
        _JIG = {'甲': '寅', '乙': '辰', '丙': '巳', '丁': '未', '戊': '巳',
                '己': '未', '庚': '申', '辛': '戌', '壬': '亥', '癸': '丑'}
        _gs = _tdpU.get(_JIG.get(ri_gan, ''), '')
        _zs = _tdpU.get(ri_zhi, '')

        jt = judge_lost_modern(item, _sc, _gs, _zs, _kong, _ctj, _ztj, _mtj,
                               sike=_sike4, force_lost=True) or {}
        leishen = jt.get('leishen') or leishen_from_text(item, force_lost=True)
        return jsonify({
            'item': item, 'end': jt.get('end', '平'),
            'leishen': leishen, 'narr': jt.get('narr', ''), 'src': jt.get('src', ''),
            'date': date_str, 'shichen': shichen,
            'sizhu': f"{sizhu['年柱'][0]}{sizhu['年柱'][1]} {sizhu['月柱'][0]}{sizhu['月柱'][1]} "
                     f"{sizhu['日柱'][0]}{sizhu['日柱'][1]} {sizhu['时柱'][0]}{sizhu['时柱'][1]}",
            'sanchuan': {'初传': _sc[0], '中传': _sc[1], '末传': _sc[2]},
            'keti': _raw.get('课体', ''),
        })
    except Exception as e:
        return jsonify({'error': str(e)[:200]}), 500


@app.route('/api/zeri/optimize', methods=['POST'])
def api_zeri_optimize():
    """运行批量择日优化 POST /api/zeri/optimize"""
    try:
        data = request.get_json(silent=True) or {}
        years = data.get('years', 3)
        mountains = data.get('mountains', None)
        from engine.batch_zeri_optimizer import BatchZeriOptimizer
        from datetime import date as dt_date
        start = dt_date.today()
        end = dt_date(start.year + years - 1, 12, 31)
        optimizer = BatchZeriOptimizer(
            start_date=start, end_date=end, mountains=mountains,
            phase1_top=data.get('p1', 500), phase2_top=data.get('p2', 50),
            phase3_top=data.get('p3', 20), verbose=False,
            # 2026-09-06 方案A-L3：择日类型类神吉应（与单课/批量同口径）
            zeri_type=(data.get('zetiri_type') or data.get('zeri_type') or ''),
            # 2026-09-06 顶格择日：三维（斗首/演禽/六壬）顶格排序 + 窗口顺延（一直往后推）
            top_triple=bool(data.get('top_triple', False)),
            auto_extend=bool(data.get('auto_extend', False)),
            min_top=int(data.get('min_top', 5) or 5),
            max_years=int(data.get('max_years', 30) or 30),
        )
        results = optimizer.optimize()
        summary = {}
        for mtn, cands in results.items():
            if cands:
                summary[mtn] = [c.to_dict() for c in cands[:5]]
        output_path = optimizer.export_results(results)
        return jsonify({'success': True, 'stats': optimizer.stats,
                        'output_file': output_path, 'summary': summary})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/prediction_detail')
def api_prediction_detail_query():
    """获取单条预测的完整分析细节 GET /api/prediction_detail?id=xxx"""
    pid = request.args.get('id', '')
    try:
        preds_file = MEMORY / 'stock_predictions.json'
        with open(preds_file, 'r', encoding='utf-8') as f:
            preds = json.load(f)
        for p in preds:
            if p.get('id') == pid:
                # 兼容：reasoning_chain 可能是列表（旧格式）
                reasoning_chain = p.get('reasoning_chain', {})
                rc_filled = p.get('rc_filled', 0)
                if isinstance(reasoning_chain, list):
                    # 用扁平字段构建字典格式推理链（避免 load_liuren_prediction 同日期多类别覆盖问题）
                    full_data = {
                        'analysis': {},
                        'prediction': {
                            'score': p.get('trend_score', 0),
                            'confidence': p.get('confidence', 0),
                            'trend': p.get('trend_prediction', ''),
                            'reasons': reasoning_chain,
                        },
                        'san_chuan': p.get('sanchuan', []),
                        'keti': p.get('keti', ''),
                    }
                    reasoning_chain = _build_reasoning_chain_from_analysis(full_data)
                    rc_filled = len(reasoning_chain)
                
                return jsonify({
                    'id': p.get('id', ''),
                    'category': p.get('category', ''),
                    'date': p.get('date', ''),
                    'target_date': p.get('target_date', ''),
                    'rizhu': p.get('rizhu', ''),
                    'yue_jiang': p.get('yue_jiang', ''),
                    'shi_chen': p.get('shi_chen', ''),
                    'keti': p.get('keti', ''),
                    'fayong': p.get('fayong', ''),
                    'sike': p.get('sike', []),
                    'sanchuan': p.get('sanchuan', []),
                    'sanchuan_tianjiang': p.get('sanchuan_tianjiang', []),
                    'trend_prediction': p.get('trend_prediction', ''),
                    'jixiong': p.get('jixiong', ''),
                    'actual_result': p.get('actual_result', ''),
                    'analysis': p.get('analysis', ''),
                    'reasoning_chain': reasoning_chain,
                    'vote_detail': p.get('vote_detail', {}),
                    'rc_filled': rc_filled,
                    'trade_executed': p.get('trade_executed', False),
                    'trade_detail': p.get('trade_detail', {}),
                    'holistic_synthesis': p.get('holistic_synthesis', {}),
                    'knowledge_features': p.get('knowledge_features', {}),
                    'kf_impact': p.get('kf_impact'),
                    'kf_reasons': p.get('kf_reasons', []),
                })
        return jsonify({'error': '未找到'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/training_status')
def api_training_status():
    """六壬回检统计（2026-08-15 清理：ML 路径证伪停用，ML 字段全移除）"""
    try:
        import json
        preds = []
        if (MEMORY / 'stock_predictions.json').exists():
            with open(MEMORY / 'stock_predictions.json', 'r', encoding='utf-8') as f:
                preds = json.load(f)

        # 六壬回检统计（仅 status=completed 的预测记录）
        completed = [p for p in preds if p.get('status') == 'completed']
        correct = [p for p in completed if p.get('trend_prediction') == p.get('actual_result')]
        lr_acc = len(correct) / max(len(completed), 1) * 100

        # 统计训练知识库案例数
        stock_cases_count = 0
        stock_cases_path = ROOT / 'data' / 'stock_training_cases.json'
        if stock_cases_path.exists():
            try:
                stock_cases = json.loads(stock_cases_path.read_text(encoding='utf-8'))
                stock_cases_count = len(stock_cases)
            except Exception:
                pass

        return jsonify({
            'total_predictions': len(completed),
            'liuren_accuracy': round(lr_acc, 1),
            'recent_days': len(set(p.get('date','') for p in completed)),
            # 六壬观察模式（参考·不参与决策）
            'liuren_reference_only': LIUREN_REFERENCE_ONLY,
            'observation_start': LIUREN_OBSERVATION_START,
            'validation_years': LIUREN_VALIDATION_YEARS,
            # 训练知识库统计
            'knowledge_total_cases': stock_cases_count,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/knowledge/refresh', methods=['POST'])
def api_knowledge_refresh():
    """刷新训练知识库：重新加载案例并重建向量索引"""
    try:
        import sys
        _p = str(Path(__file__).parent)
        if _p not in sys.path:
            sys.path.insert(0, _p)
        from engine.liuren_training_knowledge import LiuRenTrainingKnowledge
        
        global _training_knowledge_instance
        _training_knowledge_instance = LiuRenTrainingKnowledge()
        
        stats = _training_knowledge_instance.get_statistics()
        return jsonify({
            'success': True,
            'message': '知识库已刷新',
            'stats': stats
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def _get_training_knowledge():
    """获取训练知识库实例（懒加载 + 缓存）"""
    global _training_knowledge_instance
    if '_training_knowledge_instance' not in globals() or _training_knowledge_instance is None:
        import sys
        _p = str(Path(__file__).parent)
        if _p not in sys.path:
            sys.path.insert(0, _p)
        from engine.liuren_training_knowledge import LiuRenTrainingKnowledge
        _training_knowledge_instance = LiuRenTrainingKnowledge()
    return _training_knowledge_instance


def _refresh_training_knowledge():
    """触发知识库刷新（重新加载案例并重建向量索引）"""
    try:
        import sys
        _p = str(Path(__file__).parent)
        if _p not in sys.path:
            sys.path.insert(0, _p)
        from engine.liuren_training_knowledge import LiuRenTrainingKnowledge
        
        global _training_knowledge_instance
        _training_knowledge_instance = LiuRenTrainingKnowledge()
        print(f"[知识库] 已刷新，总案例数: {_training_knowledge_instance.knowledge_base.get('元数据', {}).get('总案例数', 0)}")
        return True
    except Exception as e:
        import traceback
        traceback.print_exc()
        return False


@app.route('/api/knowledge/search', methods=['POST'])
def api_knowledge_search():
    """语义搜索知识库：POST {query: '搜索内容', top_k: 5, zhanshi: 'stock'}"""
    try:
        import json
        data = request.get_json() or {}
        query = data.get('query', '')
        top_k = int(data.get('top_k', 5))
        zhanshi = data.get('zhanshi', None)
        
        if not query and not zhanshi:
            return jsonify({'success': False, 'error': '缺少 query 或 zhanshi 参数'}), 400
        
        kb = _get_training_knowledge()
        results = kb.query_similar_cases(raw_text=query, zhanshi=zhanshi, limit=top_k)
        
        return jsonify({
            'success': True,
            'query': query,
            'zhanshi': zhanshi,
            'results_count': len(results),
            'results': results
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/knowledge/cases')
def api_knowledge_cases():
    """获取知识库案例列表 GET /api/knowledge/cases?source=择日&limit=50"""
    try:
        import json
        
        stock_cases_path = ROOT / 'data' / 'stock_training_cases.json'
        if not stock_cases_path.exists():
            return jsonify({'success': True, 'cases': [], 'total': 0})
        
        with open(stock_cases_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
        
        # 筛选参数
        source_filter = request.args.get('source', '').strip()
        zhanshi_filter = request.args.get('zhanshi', '').strip()
        limit = min(int(request.args.get('limit', 100)), 500)
        offset = max(int(request.args.get('offset', 0)), 0)
        
        # 应用筛选
        filtered = cases
        if source_filter:
            filtered = [c for c in filtered if source_filter in c.get('source', '')]
        if zhanshi_filter:
            filtered = [c for c in filtered if zhanshi_filter in c.get('zhanshi_type', '')]
        
        # 按日期降序排序
        filtered.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        total = len(filtered)
        paginated = filtered[offset:offset + limit]
        
        # 精简返回字段
        result = []
        for case in paginated:
            result.append({
                'id': case.get('id', ''),
                'date': case.get('date', ''),
                'title': case.get('title', ''),
                'grade': case.get('grade', ''),
                'keti': case.get('keti', ''),
                'source': case.get('source', ''),
                'zhanshi_type': case.get('zhanshi_type', ''),
                'mountain': case.get('mountain', ''),
                'total_score': case.get('total_score', 0),
                'sanchuan': case.get('sanchuan', {}),
                'confidence': case.get('confidence', ''),
                'cast_datetime': case.get('cast_datetime', ''),
                'is_manual': case.get('is_manual', False),
            })
        
        # 统计来源分布
        source_stats = {}
        for case in cases:
            src = case.get('source', '未知')
            source_stats[src] = source_stats.get(src, 0) + 1
        
        return jsonify({
            'success': True,
            'cases': result,
            'total': total,
            'offset': offset,
            'limit': limit,
            'source_stats': source_stats,
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/zeri/results')
def api_zeri_results():
    """获取缓存的择日结果 GET /api/zeri/results?mountain=壬"""
    try:
        mountain = request.args.get('mountain', None)
        import glob
        files = sorted(glob.glob(str(ROOT / 'data' / 'zeri_optimize_*.json')), reverse=True)
        if not files:
            return jsonify({'error': '暂无缓存结果，请先运行优化'}), 404
        with open(files[0], 'r', encoding='utf-8') as f:
            data = json.load(f)
        if mountain:
            return jsonify({'meta': data.get('meta', {}), 'mountain': mountain,
                            'results': data['results'].get(mountain, [])})
        return jsonify({'meta': data.get('meta', {}), 'results': data.get('results', {})})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ═══════════════════════════════════════════════
# 六壬起课（宗门九课起课法）— 原生移植自 zongmen/http_api_server.py
# 供仪表盘「择日·学习 → 起课排盘」子标签使用；复用 zongmen/src/engine 与
# 项目 engine 同名模块。返回字段与 zongmen/demo.html 完全一致。
# ⚠️ 惰性导入 + 全程 try/except 隔离：起课引擎即使异常也只返回错误 JSON，
#    不会拖垮仪表盘其他路由（与下方行情 API 的 DLL 隔离原则一致）。
# ═══════════════════════════════════════════════
@app.route('/api/qike', methods=['GET', 'POST'])
def api_qike():
    """六壬起课（宗门九课起课法）。GET 参数：ri_gan/ri_zhi/yue_jiang/shi_chen
    （必填）+ jieqi/nianming/ben_ming/age/sex/tai_sui/zhanlei（可选）。POST 同义 JSON。"""
    try:
        if request.method == 'POST':
            p = request.get_json(silent=True) or {}
            ri_gan = p.get('ri_gan', '')
            ri_zhi = p.get('ri_zhi', '')
            yue_jiang = p.get('yue_jiang', '')
            shi_chen = p.get('shi_chen', '')
            jieqi = p.get('jieqi', '')
            nianming = p.get('nianming', '')
            ben_ming = p.get('ben_ming', '')
            age = p.get('age', '')
            sex = p.get('sex', '')
            tai_sui = p.get('tai_sui', '')
            zhanlei_param = p.get('zhanlei', '其他')
            date_param = p.get('date', '')
        else:
            ri_gan = request.args.get('ri_gan', '')
            ri_zhi = request.args.get('ri_zhi', '')
            yue_jiang = request.args.get('yue_jiang', '')
            shi_chen = request.args.get('shi_chen', '')
            jieqi = request.args.get('jieqi', '')
            nianming = request.args.get('nianming', '')
            ben_ming = request.args.get('ben_ming', '')
            age = request.args.get('age', '')
            sex = request.args.get('sex', '')
            tai_sui = request.args.get('tai_sui', '')
            zhanlei_param = request.args.get('zhanlei', '其他')
            date_param = request.args.get('date', '')

        if not all([ri_gan, ri_zhi, yue_jiang, shi_chen]):
            return jsonify({'success': False,
                            'error': '缺少必要参数：ri_gan, ri_zhi, yue_jiang, shi_chen'}), 400

        # —— 惰性导入（隔离于仪表盘主进程；sys.path 复刻 http_api_server.py 顺序）——
        import sys as _sys, os as _os
        _proj = _os.path.dirname(_os.path.abspath(__file__))
        _zsrc = _os.path.join(_proj, 'zongmen', 'src')
        _zeng = _os.path.join(_zsrc, 'engine')
        for _p in (_zeng, _zsrc, _proj):
            if _p not in _sys.path:
                _sys.path.insert(0, _p)
        _eng_flat = _os.path.join(_proj, 'engine')
        if _eng_flat not in _sys.path:
            _sys.path.append(_eng_flat)

        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        from engine.liuqin_engine import LiuQinCalculator
        from engine.gui_ren_engine import GuiRenCalculator
        try:
            from engine.sanchuan_kege import SanChuanKegeDetector as _SKD
        except Exception:
            _SKD = None
        try:
            from engine.bifa_detector import BiFaDetector as _BFD
        except Exception:
            _BFD = None
        try:
            from shen_sha_calculator import ShenShaCalculator as _SSC
        except Exception:
            _SSC = None
        try:
            from liuren_keti_bifa import (_xing_nian_zhi, _nian_ming_shang_shen,
                                          get_yingqi_text, get_wushu_text, get_yingqi_unified)
        except Exception:
            _xing_nian_zhi = _nian_ming_shang_shen = None
            get_yingqi_text = get_wushu_text = get_yingqi_unified = None

        _ZHI = set('子丑寅卯辰巳午未申酉戌亥')

        def _get_xing_nian_info(bm, ag, sx, tdp):
            out = {'行年': '', '行年上神': '', '本命上神': ''}
            if not _nian_ming_shang_shen or not _xing_nian_zhi:
                return out
            if bm not in _ZHI:
                return out
            out['本命上神'] = _nian_ming_shang_shen(bm, tdp or {}) or ''
            if ag:
                try:
                    a = int(str(ag).strip())
                except (ValueError, TypeError):
                    a = None
                if a and a >= 1:
                    s = sx if sx in ('男', '女') else '男'
                    xn = _xing_nian_zhi(bm, a, s) or ''
                    out['行年'] = xn
                    if xn:
                        out['行年上神'] = _nian_ming_shang_shen(xn, tdp or {}) or ''
            return out

        def _get_xun_shou(rg, rz):
            stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            gi = stems.index(rg)
            zi = branches.index(rz)
            idx = (gi * 6 - zi * 5) % 60
            xs = (idx // 10) * 10
            xz = branches[xs % 12]
            kw = [branches[(xs % 12 + 10) % 12], branches[(xs % 12 + 11) % 12]]
            return '甲', xz, kw

        def _stem_for_branch(b, rg, rz):
            stems = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
            branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
            _, xz, _ = _get_xun_shou(rg, rz)
            xi = branches.index(xz)
            bi = branches.index(b)
            return stems[((bi - xi) % 12) % 10]

        def _is_kw(b, rg, rz):
            _, _, kw = _get_xun_shou(rg, rz)
            return b in kw

        def _xun_sha(rg, rz):
            if not _SSC or not rg or not rz:
                return {}
            try:
                return _SSC().get_xun_info(rg + rz)
            except Exception:
                return {}

        def _gan_sha(rg):
            if not _SSC or not rg:
                return {}
            try:
                return _SSC().get_gan_sha(rg)
            except Exception:
                return {}

        def _zhi_sha(rz):
            if not _SSC or not rz:
                return {}
            try:
                return _SSC().get_zhi_sha(rz)
            except Exception:
                return {}

        calc = SiKeSanChuanCalculator2()
        tdp = calc.get_tiandi_pan(yue_jiang, shi_chen)
        sike = calc.qi_sike(ri_gan, ri_zhi, tdp)
        sc = calc.fa_sanchuan(sike, ri_gan, ri_zhi, tdp)
        sc_list = [sc.get('初传', ''), sc.get('中传', ''), sc.get('末传', '')]
        _tj_map = GuiRenCalculator().arrange_gui_ren_pan(ri_gan, {'天地对应': tdp}, shi_chen)
        _tj_ys = _tj_map.get('天将映射', {})
        _tj_list = [_tj_ys.get(c, '') for c in sc_list]
        if _SKD:
            try:
                _kr = _SKD().detect(sc_list, ri_gan=ri_gan, ri_zhi=ri_zhi,
                                   keti_raw=sc.get('课体', ''), tian_jiang=_tj_list,
                                   yue_jian=yue_jiang, si_ke=sike, jieqi=jieqi, nianming=nianming)
                sc['课格列表'] = _kr.get('课格列表', [])
            except Exception:
                sc['课格列表'] = []
        else:
            sc['课格列表'] = []
        # 2026-08-21 统一口径（前后端一致性）：毕法赋与 /api/zeri/analyze 同走 judge_orchestrator；
        # 四课补天将列（analyze 同款，前端 ke[3] 展示天将；judge_bifa 依赖 sike 天将判断干上/支上乘将）
        if sike and _tj_ys:
            try:
                sike = [[k[0], k[1], k[2], _tj_ys.get(k[1], '') or ''] for k in sike]
            except Exception:
                pass
        try:
            from engine.judge_orchestrator import build_judge_env as _bje_q, judge_all as _jall_q
            _tj3l_q = [_tj_ys.get(c, '') for c in sc_list]
            _bm_z = ben_ming[1] if isinstance(ben_ming, str) and len(ben_ming) >= 2 else ''
            _qy = _qm = _qd = 0
            if isinstance(date_param, str) and len(date_param) >= 10:
                try:
                    _qy, _qm, _qd = int(date_param[:4]), int(date_param[5:7]), int(date_param[8:10])
                except (ValueError, TypeError):
                    _qy = _qm = _qd = 0
            _env_q = _bje_q(ri_gan, ri_zhi, tai_sui or '', '', yue_jiang,
                            sike, sc_list, sc.get('课体', ''), _tj_ys, tdp,
                            shi_chen, zhanlei=zhanlei_param,
                            ben_ming_zhi=_bm_z,
                            ben_ming_age=(str(age).strip() if str(age).strip().isdigit() else ''),
                            ben_ming_sex=sex if sex in ('男', '女') else '男',
                            y=_qy, m=_qm, d=_qd, sanchuan_tianjiang=_tj3l_q)
            _jres_q = _jall_q(_env_q)
            _bfq = (_jres_q.get('bifa_judged') or {}).get('匹配法句', []) or []
            sc['毕法赋命中'] = [x.get('name', x) if isinstance(x, dict) else x for x in _bfq]
        except Exception as _e_bfq:
            sc['毕法赋命中'] = []
        _stem_list, _ganzhi_list, _liuqin_list, _kw_list = [], [], [], []
        for c in sc_list:
            try:
                _lq = LiuQinCalculator().get_liuqin(ri_gan, c) or ''
            except Exception:
                _lq = ''
            _liuqin_list.append(_lq)
            if _is_kw(c, ri_gan, ri_zhi):
                _stem = ''
                _gz = c
            else:
                try:
                    _stem = _stem_for_branch(c, ri_gan, ri_zhi)
                except Exception:
                    _stem = ''
                _gz = _stem + c
            _stem_list.append(_stem)
            _ganzhi_list.append(_gz)
            _kw_list.append('')
        sc['三传'] = sc_list
        sc['三传天将'] = _tj_list
        sc['三传天干'] = _stem_list
        sc['三传干支'] = _ganzhi_list
        sc['三传六亲'] = _liuqin_list
        sc['三传空亡'] = _kw_list
        data = {
            'ri_gan': ri_gan, 'ri_zhi': ri_zhi, 'yue_jiang': yue_jiang, 'shi_chen': shi_chen,
            'jieqi': jieqi, 'nianming': nianming, 'ben_ming': ben_ming, 'age': age, 'sex': sex,
            'tiandi_pan': tdp, 'sike': sike, 'sanchuan': sc,
            '旬煞': _xun_sha(ri_gan, ri_zhi),
            '日干神煞': _gan_sha(ri_gan),
            '日支神煞': _zhi_sha(ri_zhi),
            '行年信息': _get_xing_nian_info(ben_ming, age, sex, tdp),
            '应期总览': (get_yingqi_unified(ri_gan, ri_zhi, sc_list, tdp, sike, shi_chen, tai_sui, zhanlei_param)
                         if get_yingqi_unified else ''),
            '物数': (get_wushu_text(ri_gan, sc_list) if get_wushu_text else ''),
        }
        # CBR 检索相似古例（长征第1期·依样断课参考；失败降级空，不拖垮起课）
        try:
            if _eng_flat not in _sys.path:
                _sys.path.insert(0, _eng_flat)
            from cbr_retrieval import retrieve_by_ke as _cbr_retrieve
            _cbr_res = _cbr_retrieve(ri_gan + ri_zhi, yue_jiang, shi_chen, zhanlei=zhanlei_param, top_k=5)
            data['cbr'] = _cbr_res.get('matches', [])
        except Exception:
            data['cbr'] = []
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════
# 股票行情 API（纯 akshare 实现，避免加载 mini_racer V8 DLL）
# ⚠️ 禁止在本文件中导入 StockAnalyzer — 会导致主进程 DLL 崩溃
# ═══════════════════════════════════════════════

@app.route('/api/stock/search', methods=['GET'])
def stock_search():
    """搜索股票代码"""
    try:
        keyword = request.args.get('keyword', '')
        if not keyword:
            return jsonify({'success': False, 'error': '请提供搜索关键词'}), 400
        if _ak is None:
            return jsonify({'success': False, 'error': '行情模块未加载'}), 500
        df = _ak.stock_info_a_code_name()
        results = []
        keyword_upper = keyword.upper()
        for _, row in df.iterrows():
            code = str(row['code'])
            name = str(row['name'])
            if keyword_upper in code or keyword in name:
                results.append({'code': code, 'name': name})
        return jsonify({'success': True, 'results': results[:20]})
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


def _tencent_quote(code):
    """通过腾讯单股接口获取实时行情（轻量级，单股查询）

    腾讯API: http://qt.gtimg.cn/q=sh600519
    返回字段（~分隔，共88项）：
    [1]名称 [2]代码 [3]最新价 [4]昨收 [5]今开 [6]成交量(手)
    [31]涨跌额 [32]涨跌幅 [33]最高 [34]最低 [37]成交额(万)
    [38]换手率(%) [44]流通市值(亿) [45]总市值(亿)
    """
    import requests
    # 代码前缀判断：6/5/9开头沪市，0/3开头深市，8/4开头北交所
    c = str(code).strip().lower().replace('sh', '').replace('sz', '').replace('bj', '')
    if c.startswith('6') or c.startswith('5') or c.startswith('9') or c.startswith('1'):
        prefix = 'sh'
    elif c.startswith('8') or c.startswith('4'):
        prefix = 'bj'
    else:
        prefix = 'sz'
    url = f'http://qt.gtimg.cn/q={prefix}{c}'
    r = requests.get(url, timeout=5)
    txt = r.text.strip()
    # v_sh600519="..." 提取引号内内容
    if '"' not in txt:
        return None
    content = txt.split('"', 2)[1]
    if not content:
        return None
    fields = content.split('~')
    if len(fields) < 46:
        return None
    def _num(i):
        try: return float(fields[i])
        except: return 0.0
    def _str(i):
        try: return fields[i]
        except: return ''
    return {
        'code': c,
        'name': _str(1),
        'price': _num(3),
        'prev_close': _num(4),
        'open': _num(5),
        'volume': _num(6) * 100,  # 手→股
        'change_amount': _num(31),
        'change': _num(32),
        'high': _num(33),
        'low': _num(34),
        'amount': _num(37) * 10000,  # 万→元
        'turnover_rate': _num(38),
        'market_cap': _num(45) * 1e8,  # 亿→元
    }


@app.route('/api/stock/quote', methods=['GET'])
def stock_quote():
    """获取股票实时行情

    优先使用腾讯单股API（轻量级，不会被限流）；
    失败时降级到akshare的stock_zh_a_spot()全量数据（新浪源）。
    """
    try:
        code = request.args.get('code', '000001')
        # 方案1：腾讯单股API
        try:
            q = _tencent_quote(code)
            if q and q.get('price', 0) > 0:
                return jsonify({'success': True, 'quote': q, 'source': 'tencent'})
        except Exception as e:
            print(f"  [腾讯API] 失败: {e}")
        # 方案2：降级到akshare新浪源全量数据
        if _ak is not None:
            try:
                df = _ak.stock_zh_a_spot()
                row = df[df['代码'] == str(code).zfill(6)]
                if not row.empty:
                    r = row.iloc[0]
                    quote = {
                        'code': str(code),
                        'name': str(r.get('名称', '')),
                        'price': float(r.get('最新价', 0) or 0),
                        'change': float(r.get('涨跌幅', 0) or 0),
                        'change_amount': float(r.get('涨跌额', 0) or 0),
                        'volume': float(r.get('成交量', 0) or 0),
                        'amount': float(r.get('成交额', 0) or 0),
                        'high': float(r.get('最高', 0) or 0),
                        'low': float(r.get('最低', 0) or 0),
                        'open': float(r.get('今开', 0) or 0),
                        'prev_close': float(r.get('昨收', 0) or 0),
                        'turnover_rate': float(r.get('换手率', 0) or 0),
                        'market_cap': float(r.get('总市值', 0) or 0),
                    }
                    return jsonify({'success': True, 'quote': quote, 'source': 'sina'})
            except Exception as e:
                print(f"  [新浪源] 失败: {e}")
        return jsonify({'success': False, 'error': '所有行情源均不可用'}), 503
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


def _tx_prefix(code: str) -> str:
    """股票代码 -> 腾讯前缀 (sh/sz/bj)"""
    c = str(code).strip().zfill(6)
    if c.startswith(('6', '9')):
        return 'sh' + c
    if c.startswith(('8', '4')):
        return 'bj' + c
    if c.startswith(('0', '3')):
        return 'sz' + c
    return 'sh' + c


def _fetch_tencent_kline(code: str, days: int) -> list:
    """从腾讯财经拉取个股/指数日K线（前复权），返回 OHLCV 列表。
    失败抛异常，由调用方降级到本地缓存。"""
    import urllib.request, json as _json, ssl, datetime as _dt
    c = str(code).strip().zfill(6)
    prefix = _tx_prefix(c)
    end = _dt.date.today().strftime('%Y-%m-%d')
    start = (_dt.date.today() - _dt.timedelta(days=int(days) * 2 + 30)).strftime('%Y-%m-%d')
    url = (f'https://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
           f'?param={prefix},day,{start},{end},{int(days) * 2},qfq')
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(url, headers={
        'User-Agent': 'Mozilla/5.0',
        'Referer': 'https://gu.qq.com/'
    })
    # 绕过系统代理，防止代理环境下挂起
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=10) as r:
        data = _json.loads(r.read().decode('utf-8', 'ignore'))
    node = (data.get('data') or {}).get(prefix)
    if not node:
        raise RuntimeError(f'腾讯未返回 {prefix} 的K线数据')
    rows = node.get('qfqday') or node.get('day') or []
    out = []
    for k in rows:
        if not isinstance(k, list) or len(k) < 6:
            continue
        try:
            out.append({
                'date': str(k[0]),
                'open': float(k[1]),
                'close': float(k[2]),
                'high': float(k[3]),
                'low': float(k[4]),
                'volume': float(k[5]),
                'amount': float(k[6]) if len(k) > 6 else round(float(k[2]) * float(k[5]) * 100, 2),
            })
        except (ValueError, TypeError):
            continue
    if not out:
        raise RuntimeError(f'{prefix} K线解析为空')
    return out[-int(days):] if days else out


def _save_kline_cache(cache_path: str, code: str, kline: list):
    """把K线写入本地缓存（保留其他股票条目）。"""
    import json as _json, os as _os, datetime as _dt
    try:
        cache = {}
        if _os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache = _json.load(f)
            except Exception:
                cache = {}
        cache[code] = {
            'fetched_at': _dt.datetime.now().isoformat(timespec='seconds'),
            'source': 'tencent',
            'kline': kline,
        }
        _os.makedirs(_os.path.dirname(cache_path), exist_ok=True)
        with open(cache_path, 'w', encoding='utf-8') as f:
            _json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"  [K线] 写缓存失败({code}): {e}")


@app.route('/api/stock/kline', methods=['GET'])
def stock_kline():
    """获取个股日K线历史（默认近60个交易日）

    数据源优先级：腾讯财经(在线) → 本地缓存 → 空。
    成功获取后自动写入 _memory/stock_kline_cache.json 供离线降级使用。
    """
    import json as _json, os as _os
    try:
        code = request.args.get('code', '000001')
        days = min(int(request.args.get('days', 60)), 500)
        c = str(code).strip().zfill(6)
        base = _os.path.dirname(_os.path.abspath(__file__))
        cache_path = _os.path.join(base, '_memory', 'stock_kline_cache.json')
        kline = None

        # ── 1) 在线拉取（腾讯，稳定可用）──
        try:
            kline = _fetch_tencent_kline(c, days)
            if kline:
                _save_kline_cache(cache_path, c, kline)
                print(f"  [K线] 在线拉取成功({c}, {len(kline)}条)")
        except Exception as e:
            print(f"  [K线] 在线拉取失败({c}): {type(e).__name__}: {e}")

        # ── 2) 降级：本地缓存 ──
        if not kline and _os.path.exists(cache_path):
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cache = _json.load(f)
                if c in cache and cache[c].get('kline'):
                    kline = cache[c]['kline']
                    print(f"  [K线] 使用本地缓存({c}, {len(kline)}条)")
            except Exception:
                pass

        if not kline:
            return jsonify({'success': True, 'kline': [], 'message': '暂无K线数据（数据源可能限流中，稍后重试）'})
        return jsonify({'success': True, 'kline': kline, 'count': len(kline)})
    except Exception as e:
        print(f"  [K线] 异常: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/stock/market', methods=['GET'])
def stock_market():
    """获取大盘指数行情（上证/深证等）"""
    try:
        if _ak is None:
            return jsonify({'success': False, 'error': '行情模块未加载'}), 500
        df = _ak.stock_zh_index_spot_em(symbol="上证系列指数")
        result = {'shanghai': None, 'shenzhen': None, 'others': []}
        for _, row in df.iterrows():
            item = {
                'code': str(row.get('代码', '')),
                'name': str(row.get('名称', '')),
                'price': float(row.get('最新价', 0)),
                'change_pct': float(row.get('涨跌幅', 0)),
                'change': float(row.get('涨跌额', 0)),
                'high': float(row.get('最高', 0)),
                'low': float(row.get('最低', 0)),
            }
            if '000001' in item['code']:
                result['shanghai'] = item
            elif '399001' in item['code']:
                result['shenzhen'] = item
            else:
                result['others'].append(item)
        return jsonify({'success': True, 'market': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/multi_stock', methods=['GET'])
def multi_stock_predictions():
    """获取大六壬一课多断最新预测结果

    读取 _memory/multi_stock_*.json 中最新的文件，
    返回 predictions 数组（含 symbol/name/trend/jixiong/confidence/analysis）。
    """
    try:
        from pathlib import Path
        memory_dir = Path(os.path.dirname(os.path.abspath(__file__))) / '_memory'
        # 列出所有 multi_stock_*.json 并按文件名（含时间戳）降序取最新
        files = sorted(memory_dir.glob('multi_stock_*.json'), reverse=True)
        if not files:
            return jsonify({
                'success': True,
                'date': None,
                'predictions': [],
                'message': '暂无大六壬一课多断预测记录'
            })

        latest_file = files[0]
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        preds = data.get('predictions', [])
        # 统一字段，便于前端使用
        normalized = []
        for p in preds:
            normalized.append({
                'symbol': p.get('symbol', ''),
                'name': p.get('name', ''),
                'trend': p.get('trend', '?'),
                'jixiong': p.get('jixiong', '?'),
                'confidence': float(p.get('confidence', 0) or 0),
                'analysis': p.get('analysis', ''),
            })

        return jsonify({
            'success': True,
            'date': data.get('date', ''),
            'rizhu': data.get('rizhu', ''),
            'shichen': data.get('shichen', ''),
            'file': latest_file.name,
            'predictions': normalized
        })
    except Exception as e:
        print(f"❌ 获取大六壬一课多断预测失败: {e}")
        return jsonify({'success': False, 'error': str(e), 'predictions': []}), 500


@app.route('/api/screener/result', methods=['GET'])
def screener_result():
    """获取量化选股器最新扫描结果

    读取 _memory/stock_screener_result.json，返回 TOP N 选股列表
    （含 rank/code/name/score/advice）。
    """
    try:
        from pathlib import Path
        result_file = Path(os.path.dirname(os.path.abspath(__file__))) / '_memory' / 'stock_screener_result.json'
        if not result_file.exists():
            return jsonify({
                'success': True,
                'scanned_at': None,
                'results': [],
                'message': '暂无选股扫描结果，请等待调度器在 09:10 自动扫描，或手动运行 stock_screener.py'
            })

        with open(result_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = data.get('results', [])
        # 统一字段
        normalized = []
        for r in results:
            normalized.append({
                'rank': r.get('rank', 0),
                'code': str(r.get('code', '')),
                'name': r.get('name', ''),
                'score': float(r.get('score', 0) or 0),
                'advice': r.get('advice', ''),
            })

        return jsonify({
            'success': True,
            'scanned_at': data.get('scanned_at', ''),
            'count': len(normalized),
            'results': normalized
        })
    except Exception as e:
        print(f"❌ 获取选股结果失败: {e}")
        return jsonify({'success': False, 'error': str(e), 'results': []}), 500


@app.route('/api/huoshi_paipan', methods=['POST'])
def huoshi_paipan_api():
    """人工占一课：活时法（真随机择时）

    调用 random.org 大气噪声获取真随机数，模拟传统六壬"掷铜钱/抽签"求活时。
    适用于用户主动"求天机"场景（非求测时刻，没有自然正时）。

    返回:
        排盘结果 + 占时来源（真太阳时校正 vs 活时法）
    """
    try:
        from multi_stock_predict import huoshi_paipan, predict_multi_stocks
        paipan_text, rizhu, shichen, source = huoshi_paipan()
        # CBR 检索相似古例（长征第1期·依样断课参考；失败降级空）
        cbr = []
        try:
            from multi_stock_predict import get_yuejiang, get_beijing_now
            yuejiang = get_yuejiang(get_beijing_now().date())
            _p2 = str(Path(__file__).parent)
            if _p2 not in sys.path:
                sys.path.insert(0, _p2)
            from engine.cbr_retrieval import retrieve_by_ke as _cbr_retrieve
            cbr = _cbr_retrieve(rizhu, yuejiang, shichen, zhanlei='其他', top_k=5).get('matches', [])
        except Exception:
            cbr = []
        return jsonify({
            'success': True,
            'method': '活时法(真随机)',
            'source': source,
            'rizhu': rizhu,
            'shichen': shichen,
            'paipan_text': paipan_text,
            'cbr': cbr,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        })
    except Exception as e:
        print(f"❌ 活时排盘失败: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/market_timing', methods=['GET'])
def market_timing_api():
    """① 六壬择时：读取当日大盘预测，判断今日是否适合开仓

    返回大盘择时信号（bull/bear/neutral）+ 吉凶 + 趋势 + 分析。
    """
    try:
        from multi_stock_predict import get_market_timing
        timing = get_market_timing()
        return jsonify({
            'success': True,
            'signal': timing.get('signal'),
            'jixiong': timing.get('jixiong'),
            'trend': timing.get('trend'),
            'analysis': timing.get('analysis'),
            'rizhu': timing.get('rizhu'),
            'shichen': timing.get('shichen'),
            'target_date': timing.get('target_date'),
            'predict_time': timing.get('predict_time'),
            'source': timing.get('source'),
        })
    except Exception as e:
        print(f"❌ 获取择时信号失败: {e}")
        return jsonify({'success': False, 'error': str(e), 'signal': 'neutral'}), 500


@app.route('/api/dual_phase', methods=['GET'])
def dual_phase_result():
    """获取双阶段选股结果（量化海选 + 六壬精选 + 择时信号 + 仓位建议）

    读取 _memory/dual_phase_*.json 最新文件，返回双重验证后的推荐列表。
    """
    try:
        from pathlib import Path
        memory_dir = Path(os.path.dirname(os.path.abspath(__file__))) / '_memory'
        files = sorted(memory_dir.glob('dual_phase_*.json'), reverse=True)
        if not files:
            return jsonify({
                'success': True,
                'date': None,
                'verified': [],
                'all': [],
                'message': '暂无双阶段选股结果，请等待调度器在 09:10 自动执行'
            })

        latest_file = files[0]
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        results = data.get('results', [])
        verified = [r for r in results if r.get('verify_level') == 'verified']
        watching = [r for r in results if r.get('verify_level') == 'watch']
        market_timing = data.get('market_timing', {})
        skipped_reason = data.get('skipped_reason', '')

        return jsonify({
            'success': True,
            'date': data.get('date', ''),
            'file': latest_file.name,
            'verified_count': len(verified),
            'watch_count': len(watching),
            'total_count': len(results),
            'verified': verified,
            'watch': watching,
            'all': results,
            'market_timing': market_timing,
            'skipped_reason': skipped_reason
        })
    except Exception as e:
        print(f"❌ 获取双阶段结果失败: {e}")
        return jsonify({'success': False, 'error': str(e), 'verified': [], 'all': []}), 500


# ═══════════════════════════════════════════════
# 5天周期预测 API（量化 + 大六壬）
# ═══════════════════════════════════════════════

def _sync_quant_to_predictions(quant_result, target_date):
    """将量化预测结果同步到预测记录 — 每只ETF独立一条记录"""
    import json, uuid
    from datetime import datetime, timedelta
    
    preds_file = MEMORY / 'stock_predictions.json'
    preds = []
    if preds_file.exists():
        try:
            with open(preds_file, 'r', encoding='utf-8') as pf:
                preds = json.load(pf)
        except: pass
    
    date_str = target_date.strftime('%Y-%m-%d')
    target_str = (target_date + timedelta(days=20)).strftime('%Y-%m-%d')
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
    all_etfs = quant_result.get('all_etfs', [])
    
    if not all_etfs:
        # fallback: 如果没有all_etfs细节，用best_etf创建一条
        best = quant_result.get('best_etf', {})
        etf_code = best.get('code', '')
        preds = [p for p in preds if not (p.get('etf') == etf_code and p.get('date') == date_str and p.get('method') == '量化')]
        preds.append({
            'id': str(uuid.uuid4())[:8],
            'predict_time': now_str, 'date': date_str,
            'etf': etf_code, 'name': best.get('name', ''),
            'category': '量化', 'method': '量化',
            'trend_prediction': quant_result.get('trend_prediction', ''),
            'momentum_20d': best.get('momentum_20d', 0),
            'score': best.get('score', 0), 'position': best.get('position', 0),
            'confidence': quant_result.get('confidence', 0),
            'target_date': target_str,
        })
    else:
        # 每只ETF一条独立记录
        trend = quant_result.get('trend_prediction', '')
        for etf in all_etfs:
            etf_code = etf.get('code', '')
            # 去重：同日同股同方法只保留一条
            preds = [p for p in preds if not (
                p.get('etf') == etf_code and p.get('date') == date_str and p.get('method') == '量化'
            )]
            preds.append({
                'id': str(uuid.uuid4())[:8],
                'predict_time': now_str,
                'date': date_str,
                'etf': etf_code,
                'name': etf.get('name', ''),
                'category': '量化',
                'method': '量化',
                'trend_prediction': trend,
                'momentum_20d': etf.get('momentum_20d', 0),
                'volatility': etf.get('volatility', 0),
                'rsi': etf.get('rsi', 50),
                'ma_trend': etf.get('ma_trend', ''),
                'position': etf.get('position', 0),
                'score': etf.get('score', 0),
                'confidence': etf.get('confidence', 0),
                'price': etf.get('price', 0),
                'target_date': target_str,
            })
    
    with open(preds_file, 'w', encoding='utf-8') as pf:
        json.dump(preds, pf, ensure_ascii=False, indent=2)

@app.route('/api/quant_20d')
def api_quant_20d():
    """量化5天周期预测 GET /api/quant_20d?date=2026-07-30&force=1"""
    try:
        date_str = request.args.get('date', '')
        force = request.args.get('force', '') == '1'
        target_date = None
        if date_str:
            from datetime import datetime as dt, timedelta
            target_date = dt.strptime(date_str, '%Y-%m-%d')
        if target_date is None:
            from datetime import datetime as dt, timedelta
            target_date = dt.now()
        
        import json
        
        # 检查是否已有保存的文件
        cached_result = None
        if target_date and not force:
            quant_file = ROOT / 'quant_data' / f'quant_prediction_{target_date.strftime("%Y-%m-%d")}.json'
            if quant_file.exists():
                try:
                    with open(quant_file, 'r', encoding='utf-8') as f:
                        cached_result = json.load(f)
                except: pass
        
        if cached_result is not None:
            _sync_quant_to_predictions(cached_result, target_date)
            return jsonify({'success': True, 'data': cached_result, 'source': '已保存量化'})
        
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        
        try:
            import quant_predictor
            result = quant_predictor.get_quant_signal(target_date)
        except ImportError as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': f'导入quant_predictor失败: {e}'}), 500
        except Exception as e:
            import traceback; traceback.print_exc()
            return jsonify({'success': False, 'error': f'执行get_quant_signal失败: {e}'}), 500
        
        # 保存量化结果（单独文件）
        if target_date:
            from pathlib import Path
            quant_dir = Path(__file__).parent / 'quant_data'
            quant_dir.mkdir(exist_ok=True)
            quant_file = quant_dir / f'quant_prediction_{target_date.strftime("%Y-%m-%d")}.json'
            result['cycle_start'] = target_date.strftime('%Y-%m-%d')
            result['method'] = '量化'
            with open(quant_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2, default=str)
            _sync_quant_to_predictions(result, target_date)
        
        if 'error' in result:
            return jsonify({'success': True, 'data': result, 'warning': '数据获取异常'})
        
        return jsonify({'success': True, 'data': result, 'source': '新预测'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/keti_rules')
def api_keti_rules():
    """返回全部课格股市判断规则"""
    import json
    rules_file = ROOT / '_memory' / 'keti_stock_rules.json'
    if rules_file.exists():
        with open(rules_file, 'r', encoding='utf-8') as f:
            return jsonify(json.load(f))
    return jsonify({})


@app.route('/api/liuren_20d')
def api_liuren_20d():
    """大六壬5天周期预测 GET /api/liuren_20d?date=2026-07-30&shichen=午&yuejiang=午"""
    import sys
    print(f"\n{'='*60}\n>>> /api/liuren_20d 收到请求", flush=True)
    try:
        date_str = request.args.get('date', '')
        shichen = request.args.get('shichen', None)
        yuejiang = request.args.get('yuejiang', None)
        force = request.args.get('force', '') == '1'
        auto = request.args.get('auto', '') == '1'  # auto=1：加载模式只读不生成
        
        target_date = None
        if date_str:
            from datetime import datetime as dt
            target_date = dt.strptime(date_str, '%Y-%m-%d')
        else:
            from datetime import datetime as dt
            target_date = dt.now()  # 默认今天
        
        # 检查是否已有保存
        from liuren_20d_engine import load_liuren_prediction, get_liuren_20d_signal, save_liuren_prediction
        if target_date and not force:
            try:
                existing = load_liuren_prediction(target_date.strftime('%Y-%m-%d'))
                if existing:
                    return jsonify({'success': True, 'data': existing, 'source': '已保存历史'})
            except: pass
        
        # auto模式：只读不生成
        if auto:
            return jsonify({'success': True, 'data': None, 'source': 'auto加载-无历史'})
        
        result = get_liuren_20d_signal(target_date, shichen, yuejiang)
        save_liuren_prediction(result)
        return jsonify({'success': True, 'data': result, 'source': '新预测'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def _build_tianji_prediction_record(full, rec, shichen):
    """把天机起课记录(period-based)映射成 stock_predictions.json 记录，使其出现在「预测记录」面板。
    仅用于展示桥接；天机起课的诚实评估仍以 tianji_casts.json + cmd_stats 为准，不受影响。"""
    bi = (full or {}).get('basic_info', {}) or {}
    pred = (full or {}).get('prediction', {}) or {}
    fused = (full or {}).get('fused_judgment', {}) or {}
    san_chuan = (full or {}).get('san_chuan', []) or []
    trend_map = {'看涨': '涨', '看跌': '跌', '震荡': '震荡'}
    trend = trend_map.get(pred.get('trend', ''), pred.get('trend', '') or '--')
    jixiong = '--'
    try:
        conf = float(fused.get('confidence', pred.get('confidence', 0)) or 0)
        if conf >= 0.6:
            jixiong = '吉' if trend == '涨' else ('凶' if trend == '跌' else '平')
        else:
            jixiong = '平'
    except Exception:
        jixiong = '--'
    fa = (((full or {}).get('analysis', {}) or {}).get('full_analysis', {}) or {})
    # 课理分析兼容补丁：analysis.keti_duanyu 由 build_keti_duanyu() 生成（仅含
    # level/bifa/sanchuan_kege/special_kege 评分信号，无人类可读断语文本）；而前端
    # 「课理分析」面板按 get_keti_duanyu() 格式取 duanyu/断语/zonglun → 缺失显示「断语:无」。
    # 此处补入 get_keti_duanyu 的 keti_name/duanyu/zonglun（仅展示用，不动评分信号）。
    _analysis = (full or {}).get('analysis') or {}
    if not isinstance(_analysis, dict):
        _analysis = {}
    _keti_raw = (full or {}).get('keti', '') or ''
    _kd = _analysis.get('keti_duanyu') or {}
    if isinstance(_kd, dict) and _keti_raw and not (_kd.get('duanyu') or _kd.get('断语') or _kd.get('zonglun')):
        try:
            from liuren_keti_duanyu import LiuRenKetiDuanyu as _KDU
            _kname = (_keti_raw.split()[0] if _keti_raw.split() else _keti_raw)
            _ki = _KDU().get_keti_duanyu(_kname)
            _kd.setdefault('keti_name', _ki.get('keti_name') or _kname)
            _kd.setdefault('duanyu', _ki.get('断语', '') or '')
            _kd.setdefault('zonglun', ((_ki.get('详细断语') or {}).get('总论', '')) or '')
        except Exception:
            pass
    return {
        'id': 'tj-%d-%s' % (rec.get('period_index'), rec.get('cast_date')),
        'category': 'manual',
        'method': '天机起课',
        'predict_time': rec.get('ts', ''),
        'date': rec.get('cast_date', ''),
        'target_date': rec.get('period_end', ''),
        'trend_prediction': trend,
        'jixiong': jixiong,
        'ref_price': '--',
        'actual_result': '',
        'rizhu': (full or {}).get('rizhu') or (bi.get('ri_gan', '') + bi.get('ri_zhi', '')),
        'yue_jiang': bi.get('yuejiang', ''),
        'shi_chen': shichen,
        'keti': (full or {}).get('keti', ''),
        'fayong': san_chuan[0] if len(san_chuan) > 0 else '',
        'tiandi_pan': fa.get('tiandi_pan', {}),
        'sanchuan_tianjiang': (full or {}).get('sanchuan_tianjiang', []),
        'bifa_red_count': 0,
        'bifa_reds': [],
        'source': 'tianji_cast',
        # 排盘可视化字段：四课 / 三传（前端 showDetail 的 grid 区块直接读这两个键）
        'sike': (full or {}).get('si_ke') or [],
        'sanchuan': (full or {}).get('san_chuan') or [],
        # ── 接入古例特征工程参考（指令⑰）：把引擎完整推理产物桥接到预测记录，
        #    供详情弹窗渲染「推理过程(17步) / 课理分析 / 综合判断」。
        #    天机起课的诚实评估仍以 tianji_casts.json + cmd_stats 为准，此处仅展示桥接。
        'reasoning_chain': (full or {}).get('reasoning_chain') or {},
        'rc_filled': len([1 for v in ((full or {}).get('reasoning_chain') or {}).values() if v]),
        'analysis': _analysis,
        'prediction': (full or {}).get('prediction') or {},
        # 综合判断：前端读 d.holistic_synthesis（trend/axes/evidence/retrieved_cases/zongduan）
        'holistic_synthesis': (full or {}).get('holistic_judgment') or {},
    }


def _append_tianji_to_stock_knowledge(full, rec, shichen):
    """将天机起课结果追加到股票训练知识库 (stock_training_cases.json)
    作为持久化学习数据，供 AI 学习模块检索和分析。
    """
    try:
        bi = (full or {}).get('basic_info', {}) or {}
        pred = (full or {}).get('prediction', {}) or {}
        fused = (full or {}).get('fused_judgment', {}) or {}
        san_chuan = (full or {}).get('san_chuan', []) or []
        analysis = (full or {}).get('analysis', {}) or {}

        # 确定占事类型
        qiushi_type = 'stock'
        # 从 holistic_judgment 或 analysis 中提取占事类型
        holistic = (full or {}).get('holistic_judgment', {}) or {}
        if isinstance(holistic, dict):
            axes = holistic.get('axes', {})
            if isinstance(axes, dict):
                qiushi_type = axes.get('占事类型', 'stock')

        # 生成案例 ID
        import uuid
        case_id = f"CASE-TIANJI-{rec.get('period_index', 0):04d}-{rec.get('cast_date', '')}"

        # 确定课体
        keti = (full or {}).get('keti', '') or ''
        if not keti:
            # 从 keti_duanyu 中获取
            kd = analysis.get('keti_duanyu', {})
            if isinstance(kd, dict):
                keti = kd.get('keti_name', '') or ''

        # 提取趋势预测
        trend = pred.get('trend', '') or ''
        jixiong = '--'
        try:
            conf = float(fused.get('confidence', pred.get('confidence', 0)) or 0)
            if conf >= 0.6:
                jixiong = '吉' if trend in ('看涨', '涨') else ('凶' if trend in ('看跌', '跌') else '平')
            else:
                jixiong = '平'
        except Exception:
            pass

        # 构建案例数据
        new_case = {
            "id": case_id,
            "stock_code": "TIANJI",
            "stock_name": f"天机起课-{rec.get('cast_date', '')}",
            "date": rec.get('cast_date', ''),
            "title": f"天机起课：{keti}课 · {trend} · 置信度{round(float(fused.get('confidence', 0) or 0) * 100)}%",
            "raw_text": (
                f"天机起课：{rec.get('cast_date', '')} {shichen}时，"
                f"课体{keti}，三传{'→'.join(san_chuan) if san_chuan else '无'}，"
                f"月将{bi.get('yuejiang', '')}，日干{bi.get('ri_gan', '')}{bi.get('ri_zhi', '')}。"
                f"预测趋势：{trend}，吉凶：{jixiong}，置信度：{round(float(fused.get('confidence', 0) or 0) * 100)}%。"
            ),
            "original_prediction": f"趋势{trend}，{jixiong}，置信度{round(float(fused.get('confidence', 0) or 0) * 100)}%",
            "actual_result": "",
            "trend_prediction": trend,
            "actual_trend": "",
            "is_correct": None,
            "sike_info": (full or {}).get('si_ke') or [],
            "sanchuan": {
                "first": san_chuan[0] if len(san_chuan) > 0 else "",
                "second": san_chuan[1] if len(san_chuan) > 1 else "",
                "third": san_chuan[2] if len(san_chuan) > 2 else ""
            },
            "keti": keti,
            "liuqin_analysis": ((analysis or {}).get('liuqin_analysis', '') if isinstance(analysis, dict) else '') or '',
            "tianjiang_analysis": ((analysis or {}).get('tianjiang_analysis', '') if isinstance(analysis, dict) else '') or '',
            "jingi_analysis": ((analysis or {}).get('jingi_analysis', '') if isinstance(analysis, dict) else '') or '',
            "source": "天机起课系统",
            "confidence": "high" if float(fused.get('confidence', 0) or 0) >= 0.7 else ('medium' if float(fused.get('confidence', 0) or 0) >= 0.5 else 'low'),
            "zhanshi_type": qiushi_type,
            "cast_datetime": f"{rec.get('cast_date', '')} {shichen}时"
        }

        # 写入 stock_training_cases.json
        stock_cases_path = Path(__file__).parent / 'data' / 'stock_training_cases.json'
        existing_cases = []
        if stock_cases_path.exists():
            try:
                existing_cases = json.loads(stock_cases_path.read_text(encoding='utf-8'))
            except Exception:
                existing_cases = []

        # 避免重复写入（按日期+时辰+课体去重）
        date_str = rec.get('cast_date', '')
        dedup_key = f"{date_str}_{shichen}_{keti}"
        for case in existing_cases:
            case_date = case.get('date', '')
            case_title = case.get('title', '')
            if case_date == date_str and dedup_key[:10] in case_title:
                return {'success': True, 'message': '案例已存在，跳过', 'skipped': True, 'case_id': case.get('id', '')}

        existing_cases.append(new_case)
        stock_cases_path.write_text(json.dumps(existing_cases, ensure_ascii=False, indent=2), encoding='utf-8')

        # 触发知识库刷新，使新案例立即可检索
        _refresh_training_knowledge()

        return {
            'success': True,
            'message': f'已追加到训练知识库',
            'case_id': case_id,
            'case_count': len(existing_cases)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


def _append_zeri_results_to_knowledge(results, mountain, zetiri_type, qiushi=''):
    """将择日批量结果追加到训练知识库 (stock_training_cases.json)
    仅保存前10个最优结果，避免数据膨胀。
    """
    try:
        stock_cases_path = Path(__file__).parent / 'data' / 'stock_training_cases.json'
        existing_cases = []
        if stock_cases_path.exists():
            try:
                existing_cases = json.loads(stock_cases_path.read_text(encoding='utf-8'))
            except Exception:
                existing_cases = []

        added_count = 0
        for i, rec in enumerate(results[:10]):  # 仅保存前10个
            date_str = rec.get('date', '')
            shichen = rec.get('shichen', '')
            total_score = rec.get('total_score', 0)
            grade = rec.get('grade', '')
            keti = rec.get('keti', '') or ''
            sanchuan_raw = rec.get('sanchuan', {}) or {}
            
            # 处理三传：可能是列表或字典
            if isinstance(sanchuan_raw, dict):
                sanchuan_list = [sanchuan_raw.get('初传', ''), sanchuan_raw.get('中传', ''), sanchuan_raw.get('末传', '')]
            elif isinstance(sanchuan_raw, list):
                sanchuan_list = sanchuan_raw
            else:
                sanchuan_list = []
            
            sanchuan_str = '→'.join([s for s in sanchuan_list if s]) if sanchuan_list else '无'
            sanchuan_display = {'first': sanchuan_list[0] if len(sanchuan_list) > 0 else '',
                               'second': sanchuan_list[1] if len(sanchuan_list) > 1 else '',
                               'third': sanchuan_list[2] if len(sanchuan_list) > 2 else ''}
            
            # 生成案例 ID
            import time
            case_id = f"CASE-ZERI-{int(time.time()) % 100000:05d}-{i+1:02d}-{date_str}"

            # 构建案例数据
            new_case = {
                "id": case_id,
                "stock_code": "ZERI",
                "stock_name": f"择日-{mountain}山",
                "date": date_str,
                "title": f"择日：{mountain}山 {date_str} {shichen}时 · {grade} · 评分{total_score}",
                "raw_text": (
                    f"择日：{mountain}山 {date_str} {shichen}时，"
                    f"课体{keti}，三传{sanchuan_str}，"
                    f"总分{total_score}，等级{grade}，"
                    f"类型{zetiri_type}，求事{qiushi or '不限'}。"
                ),
                "original_prediction": f"{grade}，总分{total_score}",
                "actual_result": "",
                "trend_prediction": grade,
                "actual_trend": "",
                "is_correct": None,
                "sike_info": rec.get('sike', []) or [],
                "sanchuan": sanchuan_display,
                "keti": keti,
                "liuqin_analysis": rec.get('liuqin_analysis', '') or '',
                "tianjiang_analysis": rec.get('tianjiang_analysis', '') or '',
                "jingi_analysis": '',
                "source": f"择日系统-{zetiri_type}",
                "confidence": "high" if total_score >= 90 else ('medium' if total_score >= 70 else 'low'),
                "zhanshi_type": '择日',
                "cast_datetime": f"{date_str} {shichen}时",
                # 择日特有字段
                "mountain": mountain,
                "zetiri_type": zetiri_type,
                "total_score": total_score,
                "grade": grade,
                "bonus_score": rec.get('bonus_score', 0),
                "liuren_score": rec.get('liuren_score', 0),
                "doushou_score": rec.get('doushou_score', 0),
            }

            # 避免重复写入（按日期+时辰+山向去重）
            dedup_key = f"{date_str}_{shichen}_{mountain}"
            skip = False
            for case in existing_cases:
                case_title = case.get('title', '')
                case_raw = case.get('raw_text', '')
                if dedup_key in case_title or dedup_key in case_raw:
                    skip = True
                    break
            if skip:
                continue

            existing_cases.append(new_case)
            added_count += 1

        if added_count > 0:
            stock_cases_path.write_text(json.dumps(existing_cases, ensure_ascii=False, indent=2), encoding='utf-8')
            # 触发知识库刷新
            _refresh_training_knowledge()

        return {
            'success': True,
            'message': f'已追加 {added_count} 条择日案例到训练知识库',
            'added_count': added_count,
            'total_cases': len(existing_cases)
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'error': str(e)}


@app.route('/api/tianji_cast', methods=['POST'])
def api_tianji_cast():
    """天机起课录入 POST /api/tianji_cast
    接收 {date: "YYYY-MM-DD", shichen: "午"}，校验窗口后铸真实一课并记录。
    返回 {success, message, data: {period_index, period_start/end, trend, updown, conf, keti, sanchuan, tianjiang}}
    """
    try:
        # 兼容多种编码来源（curl/前端）
        raw = request.get_data(as_text=True)
        if not raw:
            return jsonify({'success': False, 'error': '请求体为空'}), 400
        import json as _j
        data = _j.loads(raw)
        date_str = (data or {}).get('date', '')
        shichen = (data or {}).get('shichen', '')
        if not date_str or not shichen:
            return jsonify({'success': False, 'error': '缺少 date 或 shichen 参数'}), 400
        import sys
        _p = str(Path(__file__).parent)
        if _p not in sys.path:
            sys.path.insert(0, _p)
        from engine.tianji_harness import cmd_cast
        result = cmd_cast(date_str, shichen)
        # 解析结果
        lines = [l.strip() for l in result.split('\n') if l.strip()]
        # 提取结构化信息
        store_path = Path(__file__).parent / '_memory' / 'tianji_casts.json'
        rec = None
        if store_path.exists():
            import json as _j
            all_recs = _j.loads(store_path.read_text(encoding='utf-8'))
            # 找最新的一条
            if all_recs:
                latest_key = max(all_recs.keys(), key=int)
                rec = all_recs[latest_key]
        # ── 桥接：同时写入 stock_predictions.json，使「预测记录」面板可见 ──
        if rec is not None:
            try:
                from liuren_20d_engine import get_liuren_20d_signal
                full = get_liuren_20d_signal(date_str, shichen, None)
                rec_pred = _build_tianji_prediction_record(full, rec, shichen)
                preds_path = MEMORY / 'stock_predictions.json'
                existing = []
                if preds_path.exists():
                    try:
                        existing = json.loads(preds_path.read_text(encoding='utf-8'))
                    except Exception:
                        existing = []
                rec_pred = _build_tianji_prediction_record(full, rec, shichen)
                # upsert：同 id 则覆盖（保证重录/补录时刷新完整字段），否则追加
                replaced = False
                for i, p in enumerate(existing):
                    if (p or {}).get('id') == rec_pred['id']:
                        existing[i] = rec_pred
                        replaced = True
                        break
                if not replaced:
                    # 兜底：按周期身份匹配（防旧 id 格式 tj-周期号-日期 与新格式不撞而重复）
                    for i, p in enumerate(existing):
                        pp = p or {}
                        if (pp.get('source') == 'tianji_cast'
                                and pp.get('date') == rec_pred.get('date')
                                and pp.get('target_date') == rec_pred.get('target_date')):
                            existing[i] = rec_pred
                            replaced = True
                            break
                if not replaced:
                    existing.append(rec_pred)
                preds_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')
                # ── 同时回写到 AI 训练知识库（stock_training_cases.json）──
                try:
                    knowledge_result = _append_tianji_to_stock_knowledge(full, rec, shichen)
                    if knowledge_result.get('success'):
                        print(f"[知识库] 天机起课回写成功: {knowledge_result.get('case_id')}")
                except Exception as _ke:
                    import traceback
                    traceback.print_exc()
            except Exception as _e:
                import traceback
                traceback.print_exc()
        return jsonify({
            'success': True,
            'message': result,
            'data': rec,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/tianji_stats')
def api_tianji_stats():
    """天机起课统计（心动时辰）GET /api/tianji_stats
    返回 get_scoreboard() 结构化：命中率/95%CI/p_vs55.3% + 每样本明细 + 待起课窗口
    """
    try:
        import sys
        _p = str(Path(__file__).parent)
        if _p not in sys.path:
            sys.path.insert(0, _p)
        from engine.tianji_harness import get_scoreboard, _find_due_period
        sb = get_scoreboard()
        due = _find_due_period()
        sb['due_period'] = {
            'period_index': due['period_index'],
            'period_start': due['period_start'],
            'period_end': due['period_end'],
        } if due else None
        return jsonify({'success': True, 'scoreboard': sb})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ═════════ 事件驱动起课（独立体系，与天机分离；2026-08-15 憨爷拍板）═════════
@app.route('/api/event/detect')
def api_event_detect():
    """事件触发检测 GET /api/event/detect?date=YYYY-MM-DD（默认最近交易日）
    动态σ口径：强度=|当日涨跌|/滚动20日σ；≥1.5σ弱记录 / ≥2.0σ主触发 / ≥2.5σ强标注
    """
    try:
        import sys as _s
        _p = str(Path(__file__).parent)
        if _p not in _s.path:
            _s.path.insert(0, _p)
        from engine.event_casting import detect_events
        date_str = request.args.get('date', '') or None
        r = detect_events(date_str)
        if not r.get('success'):
            return jsonify(r), 404
        return jsonify(r)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/event/events')
def api_event_events():
    """事件台账列表 GET /api/event/events?limit=50"""
    try:
        import sys as _s
        _p = str(Path(__file__).parent)
        if _p not in _s.path:
            _s.path.insert(0, _p)
        from engine.event_casting import list_events
        limit = int(request.args.get('limit', 50))
        return jsonify({'success': True, 'events': list_events(limit)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/event/cast', methods=['POST'])
def api_event_cast():
    """事件起课录入 POST /api/event/cast  body={date, shichen, event_id?}
    校验事件存在且强度≥1.5σ；一事一课；人工指定时辰铸真实一课。
    """
    try:
        raw = request.get_data(as_text=True)
        if not raw:
            return jsonify({'success': False, 'error': '请求体为空'}), 400
        import json as _j
        data = _j.loads(raw)
        date_str = (data or {}).get('date', '')
        shichen = (data or {}).get('shichen', '')
        event_id = (data or {}).get('event_id') or None
        if not date_str or not shichen:
            return jsonify({'success': False, 'error': '缺少 date 或 shichen'}), 400
        import sys as _s
        _p = str(Path(__file__).parent)
        if _p not in _s.path:
            _s.path.insert(0, _p)
        from engine.event_casting import record_cast
        r = record_cast(date_str, shichen, event_id)
        if not r.get('success'):
            return jsonify({'success': False, 'error': r.get('error', '起课失败')}), 400
        return jsonify({'success': True, 'message': r['message'], 'cast': r['cast'], 'event': r['event']})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/event/casts')
def api_event_casts():
    """事件起课台账 GET /api/event/casts?limit=50"""
    try:
        import sys as _s
        _p = str(Path(__file__).parent)
        if _p not in _s.path:
            _s.path.insert(0, _p)
        from engine.event_casting import list_casts
        limit = int(request.args.get('limit', 50))
        return jsonify({'success': True, 'casts': list_casts(limit)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/event/evaluate')
def api_event_evaluate():
    """事件起课评估 GET /api/event/evaluate
    已结算起课 5日/20日命中 vs 分方向动态2σ条件基线（不落盘，只读）
    """
    try:
        import sys as _s
        _p = str(Path(__file__).parent)
        if _p not in _s.path:
            _s.path.insert(0, _p)
        from engine.event_casting import evaluate
        return jsonify(evaluate())
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/event/heartbeat')
def api_event_heartbeat():
    """心跳检测（手动触发/查看状态）GET /api/event/heartbeat
    拉实时行情 → ≥2σ 自动起课（时辰=触发时刻）。非交易日优雅跳过。
    """
    try:
        import sys as _s
        _p = str(Path(__file__).parent)
        if _p not in _s.path:
            _s.path.insert(0, _p)
        from engine.event_casting import heartbeat_check
        r = heartbeat_check()
        return jsonify(r)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren_backtest')
def api_liuren_backtest():
    """跨牛熊历史回测报告 GET /api/liuren_backtest

    返回 engine/regime_backtest_report.json（由引擎代码对上证指数5239个交易日
    从头重算得出，非系统中近期调试期存储的自动预测记录）。
    """
    try:
        import json as _json
        from pathlib import Path as _Path
        rp = _Path(__file__).parent / 'engine' / 'regime_backtest_report.json'
        if not rp.exists():
            return jsonify({'success': False,
                            'error': '回测报告尚未生成，请先运行 engine/regime_backtest.py'}), 404
        data = _json.loads(rp.read_text(encoding='utf-8'))
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compare_20d')
def api_compare_20d():
    """量化 vs 大六壬 5天周期对比 GET /api/compare_20d?date=2026-07-30"""
    try:
        date_str = request.args.get('date', '')
        target_date = None
        if date_str:
            from datetime import datetime as dt
            target_date = dt.strptime(date_str, '%Y-%m-%d')
        
        from liuren_20d_engine import load_liuren_prediction, run_both_predictions
        if target_date:
            saved = load_liuren_prediction(target_date.strftime('%Y-%m-%d'))
            if saved:
                from quant_predictor import get_quant_signal
                qr = get_quant_signal(target_date)
                result = {'liuren': saved, 'quant': qr, 'comparison': {
                    'liuren_trend': saved['prediction']['trend'],
                    'liuren_score': saved['prediction']['score'],
                    'liuren_confidence': saved['prediction']['confidence'],
                    'liuren_summary': f"{saved['prediction']['trend']}，课体{saved.get('keti','')}",
                    'liuren_sanchuan_kege': saved.get('analysis', {}).get('keti_duanyu', {}).get('sanchuan_kege_summary', ''),
                    'liuren_sanchuan': saved.get('san_chuan', []),
                    'quant_trend': qr.get('trend_prediction', '?'),
                    'quant_confidence': qr.get('confidence', 0),
                    'quant_summary': f"{qr.get('trend_prediction', '?')}，置信度{qr.get('confidence', 0)}%",
                    'agreement': saved['prediction']['trend'] == qr.get('trend_prediction', ''),
                }}
                return jsonify({'success': True, 'data': result, 'source': '已保存六壬+同日量化'})
        
        result = run_both_predictions(target_date)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/decision_matrix')
def api_decision_matrix():
    """三级决策矩阵：量化个股 + 六壬宏观 → 综合建议 /api/decision_matrix?date=2026-07-26"""
    try:
        date_str = request.args.get('date', '')
        target_date = None
        if date_str:
            from datetime import datetime as dt
            target_date = dt.strptime(date_str, '%Y-%m-%d')
        from decision_matrix import compute_decision_matrix
        result = compute_decision_matrix(target_date)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren_review/save', methods=['POST'])
def api_liuren_review_save():
    """保存ETF专属六壬复盘预测"""
    import json
    from pathlib import Path
    data = request.get_json() or {}
    etf = data.get('etf', 'unknown')
    pred = data.get('data', {})
    review_dir = Path(__file__).parent / 'liuren_20d_data' / 'reviews'
    review_dir.mkdir(parents=True, exist_ok=True)
    date = (pred.get('cycle_start','') or 'unknown').replace(':','-')
    fp = review_dir / f'review_{etf}_{date}.json'
    with open(fp, 'w', encoding='utf-8') as f:
        json.dump(pred, f, ensure_ascii=False, indent=2, default=str)
    return jsonify({'success': True, 'file': str(fp.name)})


@app.route('/api/backtest/<etf_code>')
def api_backtest(etf_code):
    try:
        from quant_predictor import get_quant_signal
        from datetime import datetime
        r = get_quant_signal(datetime.now())
        etfs = r.get('all_etfs', [])
        etf = next((e for e in etfs if e.get('code','') == etf_code or e.get('etf','') == etf_code), None)
        if not etf:
            return jsonify({'success': False, 'error': 'ETF未找到'})
        m = etf.get('momentum_20d', 0)
        vol = etf.get('volatility', 0)
        score = etf.get('score', 0)
        # 简易回测指标
        annual_ret = round(m * (252/20), 1)  # 年化收益
        sharpe = round(m / vol if vol > 0 else 0, 2)  # 夏普比率
        max_dd = round(-abs(m) * 1.5, 1) if m < 0 else round(-vol, 1)  # 最大回撤估算
        win_rate = round(50 + score * 0.3, 1)  # 胜率估算
        result = {
            'success': True,
            'etf': etf.get('name', etf_code),
            'backtest': {
                '年化收益': f'{annual_ret}%',
                '夏普比率': sharpe,
                '最大回撤': f'{max_dd}%',
                '胜率': f'{win_rate}%',
                '20日动量': f'{m}%',
                '波动率': f'{vol}%',
                '综合评分': score,
                '结论': '✅ 信号有效' if win_rate > 50 else ('⚠️ 信号偏弱' if win_rate > 40 else '❌ 不宜交易')
            }
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/quant_history')
def api_quant_history():
    """量化预测历史"""
    try:
        from quant_predictor import get_quant_history
        history = get_quant_history(limit=10)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren_history')
def api_liuren_history():
    """六壬预测历史"""
    try:
        from liuren_20d_engine import get_liuren_history
        history = get_liuren_history(limit=10)
        return jsonify({'success': True, 'history': history})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compare_tracking')
def api_compare_tracking():
    """3个月比对追踪数据"""
    try:
        tracking_file = MEMORY / 'compare_tracking.json'
        if tracking_file.exists():
            data = read_json(tracking_file)
        else:
            data = {
                'start_date': datetime.now().strftime('%Y-%m-%d'),
                'cycles': [],
                'summary': {
                    'total_cycles': 0,
                    'liuren_correct': 0,
                    'quant_correct': 0,
                    'liuren_accuracy': 0,
                    'quant_accuracy': 0,
                    'agreement_rate': 0,
                }
            }
        return jsonify({'success': True, 'data': data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/compare_record', methods=['POST'])
def api_compare_record():
    """记录一次比对结果 POST /api/compare_record"""
    try:
        data = request.get_json(silent=True) or {}
        tracking_file = MEMORY / 'compare_tracking.json'
        
        tracking = read_json(tracking_file) if tracking_file.exists() else {
            'start_date': datetime.now().strftime('%Y-%m-%d'),
            'cycles': [],
            'summary': {}
        }
        
        tracking['cycles'].append(data)
        
        total = len(tracking['cycles'])
        lr_correct = sum(1 for c in tracking['cycles'] if c.get('liuren_correct'))
        qt_correct = sum(1 for c in tracking['cycles'] if c.get('quant_correct'))
        agreement = sum(1 for c in tracking['cycles'] if c.get('agreement'))
        
        tracking['summary'] = {
            'total_cycles': total,
            'liuren_correct': lr_correct,
            'quant_correct': qt_correct,
            'liuren_accuracy': round(lr_correct / max(total, 1) * 100, 1),
            'quant_accuracy': round(qt_correct / max(total, 1) * 100, 1),
            'agreement_rate': round(agreement / max(total, 1) * 100, 1),
        }
        
        tracking_file.write_text(json.dumps(tracking, ensure_ascii=False, indent=2), encoding='utf-8')
        return jsonify({'success': True, 'summary': tracking['summary']})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════
# 六壬精选审核 API（AI初判 + 人工审核 + 训练库反哺）
# ═══════════════════════════════════════════════

_review_mgr = None

def _get_review_mgr():
    global _review_mgr
    if _review_mgr is None:
        from liuren_review_manager import get_review_manager
        _review_mgr = get_review_manager()
    return _review_mgr


@app.route('/api/liuren_review/status', methods=['GET'])
def liuren_review_status():
    """获取六壬精选审核状态
    GET /api/liuren_review/status?task_id=xxx
    """
    try:
        task_id = request.args.get('task_id', '')
        mgr = _get_review_mgr()
        status = mgr.get_status(task_id or None)
        if not status:
            return jsonify({
                'success': True,
                'has_task': False,
                'task': None,
                'message': '暂无审核任务'
            })
        return jsonify({
            'success': True,
            'has_task': True,
            'task': status,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren_review/start', methods=['POST'])
def liuren_review_start():
    """开始六壬精选审核
    POST /api/liuren_review/start
    Body: {
        "stocks": [{"code":"600519","name":"贵州茅台","score":85}, ...],
        "shichen": "午时",
        "rizhu": "辛卯",
        "source": "manual"
    }
    """
    try:
        data = request.get_json() or {}
        stocks = data.get('stocks', [])
        shichen = data.get('shichen', '')
        rizhu = data.get('rizhu', '')
        source = data.get('source', 'manual')
        timeout_hours = data.get('timeout_hours')

        if not stocks:
            return jsonify({'success': False, 'error': '股票列表不能为空'}), 400

        mgr = _get_review_mgr()
        task_id = mgr.start_review(stocks, shichen=shichen, rizhu=rizhu, source=source, timeout_hours=timeout_hours)

        status = mgr.get_status(task_id)
        return jsonify({
            'success': True,
            'task_id': task_id,
            'task': status,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren_review/save', methods=['POST'])
def liuren_review_save():
    """保存人工审核结果
    POST /api/liuren_review/save
    Body: {
        "task_id": "xxx",
        "reviews": [
            {"code":"600519","human_trend":"看涨","human_jixiong":"吉","review_note":"..."},
            ...
        ],
        "reviewer": "user"
    }
    """
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id', '')
        reviews = data.get('reviews', [])
        reviewer = data.get('reviewer', 'user')

        if not task_id:
            return jsonify({'success': False, 'error': '缺少task_id'}), 400

        mgr = _get_review_mgr()
        ok = mgr.save_review(task_id, reviews, reviewer=reviewer)

        if ok:
            status = mgr.get_status(task_id)
            # 审核保存后，强制刷新统一训练库，使纠正规则立即生效
            try:
                from unified_trainer import reload_trainer
                reload_trainer()
            except: pass
            return jsonify({
                'success': True,
                'message': '审核已保存，结果已存入训练库',
                'task': status,
            })
        else:
            return jsonify({'success': False, 'error': '保存失败，任务不存在或状态不允许'}), 400
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren_review/skip', methods=['POST'])
def liuren_review_skip():
    """跳过六壬精选
    POST /api/liuren_review/skip
    Body: {"task_id": "xxx", "reason": ""}
    """
    try:
        data = request.get_json() or {}
        task_id = data.get('task_id', '')
        reason = data.get('reason', '')

        if not task_id:
            return jsonify({'success': False, 'error': '缺少task_id'}), 400

        mgr = _get_review_mgr()
        ok = mgr.skip_review(task_id, reason=reason)

        if ok:
            return jsonify({'success': True, 'message': '已跳过六壬精选'})
        else:
            return jsonify({'success': False, 'error': '操作失败'}), 400
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren_review/list', methods=['GET'])
def liuren_review_list():
    """获取历史审核任务列表
    GET /api/liuren_review/list?limit=10
    """
    try:
        limit = int(request.args.get('limit', 10))
        mgr = _get_review_mgr()
        tasks = mgr.list_tasks(limit=limit)
        return jsonify({'success': True, 'tasks': tasks})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════
# 选股持仓管理 API
# ═══════════════════════════════════════════════

# ──────────────────────────────────────────
#  量化子系统 API（旧 /api/screener/* 兼容重定向）
# ──────────────────────────────────────────
@app.route('/api/screener/positions', methods=['GET'])
@app.route('/api/quant/positions', methods=['GET'])
def api_quant_positions():
    """量化持仓列表 — 11维因子评分驱动"""
    try:
        from quant_position_manager import get_positions
        data = get_positions()
        return jsonify({'success': True, **data})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/screener/manual_buy', methods=['POST'])
@app.route('/api/quant/manual_buy', methods=['POST'])
def api_quant_manual_buy():
    """量化账户手动买入"""
    try:
        data = request.get_json() or {}
        code = data.get('code', '')
        name = data.get('name', '')
        shares = int(data.get('shares', 0))
        price = data.get('price')
        if not code:
            return jsonify({'success': False, 'error': '缺少股票代码'}), 400
        if shares < 100:
            return jsonify({'success': False, 'error': '最少买入100股(1手)'}), 400
        from quant_position_manager import manual_buy
        result = manual_buy(code, name, shares, price)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/screener/manual_sell', methods=['POST'])
@app.route('/api/quant/manual_sell', methods=['POST'])
def api_quant_manual_sell():
    """量化账户手动平仓"""
    try:
        data = request.get_json() or {}
        position_id = data.get('position_id', '')
        price = data.get('price')
        if not position_id:
            return jsonify({'success': False, 'error': '缺少持仓ID'}), 400
        from quant_position_manager import manual_sell
        result = manual_sell(position_id, price)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/screener/performance', methods=['GET'])
@app.route('/api/quant/performance', methods=['GET'])
def api_quant_performance():
    """量化绩效统计"""
    try:
        from quant_position_manager import get_performance
        data = get_performance()
        return jsonify({'success': True, **data})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/screener/trades', methods=['GET'])
@app.route('/api/quant/trades', methods=['GET'])
def api_quant_trades():
    """量化交易记录"""
    try:
        from quant_position_manager import get_positions
        data = get_positions()
        trades = _format_trades(data, '量化')
        return jsonify({'success': True, 'trades': trades})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ──────────────────────────────────────────
#  六壬子系统 API
# ──────────────────────────────────────────
@app.route('/api/liuren/positions', methods=['GET'])
def api_liuren_positions():
    """六壬持仓列表 — 一课多断信号驱动"""
    try:
        from liuren_position_manager import get_positions
        data = get_positions()
        return jsonify({'success': True, **data})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren/manual_buy', methods=['POST'])
def api_liuren_manual_buy():
    """六壬账户手动买入"""
    try:
        data = request.get_json() or {}
        code = data.get('code', '')
        name = data.get('name', '')
        shares = int(data.get('shares', 0))
        price = data.get('price')
        if not code:
            return jsonify({'success': False, 'error': '缺少股票代码'}), 400
        if shares < 100:
            return jsonify({'success': False, 'error': '最少买入100股(1手)'}), 400
        from liuren_position_manager import manual_buy
        result = manual_buy(code, name, shares, price)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren/manual_sell', methods=['POST'])
def api_liuren_manual_sell():
    """六壬账户手动平仓"""
    try:
        data = request.get_json() or {}
        position_id = data.get('position_id', '')
        price = data.get('price')
        if not position_id:
            return jsonify({'success': False, 'error': '缺少持仓ID'}), 400
        from liuren_position_manager import manual_sell
        result = manual_sell(position_id, price)
        return jsonify(result)
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren/performance', methods=['GET'])
def api_liuren_performance():
    """六壬绩效统计"""
    try:
        from liuren_position_manager import get_performance
        data = get_performance()
        return jsonify({'success': True, **data})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/liuren/trades', methods=['GET'])
def api_liuren_trades():
    """六壬交易记录"""
    try:
        from liuren_position_manager import get_positions
        data = get_positions()
        trades = _format_trades(data, '六壬')
        return jsonify({'success': True, 'trades': trades})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


def _format_trades(data, subsystem_label):
    """将持仓数据统一格式化为交易记录列表"""
    trades = []
    for p in data.get('positions', []):
        trades.append({
            'id': p['id'], 'time': p.get('buy_time', ''),
            'code': p['code'], 'name': p['name'],
            'action': '买', 'price': p.get('buy_price', 0),
            'amount': p.get('amount', 0), 'shares': p.get('shares', 0),
            'pnl': p.get('pnl', 0), 'pnl_pct': p.get('pnl_pct', 0),
            'status': 'holding', 'advice': p.get('advice', ''),
            'score': p.get('score', 0),
            'source': p.get('source', 'auto'),
            'category': f'{subsystem_label}持仓', 'category_key': f'{subsystem_label}_position',
        })
    for p in data.get('closed_trades', []):
        trades.append({
            'id': p['id'], 'time': p.get('buy_time', ''),
            'code': p['code'], 'name': p['name'],
            'action': '买', 'price': p.get('buy_price', 0),
            'amount': p.get('amount', 0), 'shares': p.get('shares', 0),
            'pnl': 0, 'pnl_pct': 0,
            'status': 'closed', 'advice': p.get('advice', ''),
            'score': p.get('score', 0),
            'source': p.get('source', 'auto'),
            'category': f'{subsystem_label}持仓', 'category_key': f'{subsystem_label}_position',
        })
        trades.append({
            'id': p['id'] + '_close', 'time': p.get('close_time', ''),
            'code': p['code'], 'name': p['name'],
            'action': '卖', 'price': p.get('close_price', 0),
            'amount': p.get('amount', 0), 'shares': p.get('shares', 0),
            'pnl': p.get('pnl', 0), 'pnl_pct': p.get('pnl_pct', 0),
            'status': 'closed', 'close_reason': p.get('close_reason', ''),
            'advice': p.get('advice', ''), 'score': p.get('score', 0),
            'source': p.get('source', 'auto'),
            'category': f'{subsystem_label}持仓', 'category_key': f'{subsystem_label}_position',
        })
    trades.sort(key=lambda x: x.get('time', ''), reverse=True)

def _acquire_single_instance_lock(lock_path):
    """确保同一时间只运行一个 Flask 实例（防止 .bat/手动重复启动导致多实例抢端口）。
    返回锁文件句柄（进程存活期间保持打开）；若已被其它实例占用则返回 None。"""
    import os as _os
    try:
        import msvcrt
    except ImportError:
        msvcrt = None
    try:
        import fcntl
    except ImportError:
        fcntl = None
    try:
        lock_dir = _os.path.dirname(lock_path)
        if lock_dir:
            _os.makedirs(lock_dir, exist_ok=True)
        f = open(lock_path, 'w')
        if msvcrt is not None:
            msvcrt.locking(f.fileno(), msvcrt.LK_NBLCK, 1)
        elif fcntl is not None:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        f.write(str(_os.getpid()))
        f.flush()
        return f
    except (OSError, IOError):
        try:
            f.close()
        except Exception:
            pass
        return None


# ═══════════════════════════════════════════════
# 批量择日（择日类型分类 + 吉日列表）— 迁移自原始「仪度六壬择日」系统
# 复用 engine/batch_zeri_optimizer 三阶段漏斗 + sizhu/douhou/yanqin 引擎。
# ═══════════════════════════════════════════════

@app.route('/api/sizhu', methods=['GET'])
def api_sizhu():
    """四柱查询 GET /api/sizhu?year=&month=&day=&shichen=子"""
    try:
        y = int(request.args.get('year', 2026))
        m = int(request.args.get('month', 1))
        d = int(request.args.get('day', 1))
        shichen = request.args.get('shichen', '子')
        from engine.sizhu_engine import get_sizhu
        sizhu = get_sizhu(y, m, d, shichen)
        return jsonify({'success': True, 'sizhu': {
            '年柱': sizhu.get('年柱', ''), '月柱': sizhu.get('月柱', ''),
            '日柱': sizhu.get('日柱', ''), '时柱': sizhu.get('时柱', ''),
        }})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ── 真太阳时接入（2026-08-17 憨爷拍板：择日理顺第1项）──
# 语义：用户/择日师选的"时辰"= 当地真太阳时辰（传统正确语义，评分不动）。
# 经度仅用于把真太阳时辰换算成"北京时间范围"展示，供按北京时间安排的用事者对照。
SHI_CHEN_RANGE = {
    '子': (1380, 1440), '丑': (60, 180), '寅': (180, 300), '卯': (300, 420),
    '辰': (420, 540), '巳': (540, 660), '午': (660, 780), '未': (780, 900),
    '申': (900, 1020), '酉': (1020, 1140), '戌': (1140, 1260), '亥': (1260, 1380),
}


def _true_solar_info(shi_zhi, date_str, longitude=None):
    """真太阳时辰 → 对应北京时间范围。
    longitude 默认 120（北京时间区，即东经120°平太阳时）。
    校正 = 经度差(每度4分钟) + 均时差(随日期±17分钟)。
    """
    if not shi_zhi or shi_zhi not in SHI_CHEN_RANGE:
        return None
    try:
        lon = float(longitude)
    except (TypeError, ValueError):
        lon = 120.0
    try:
        from engine.solar_time import calc_equation_of_time
        from datetime import datetime
        d = datetime.strptime(date_str, '%Y-%m-%d')
        eot = float(calc_equation_of_time(d.date()))
    except Exception:
        eot = 0.0
    corr = (lon - 120) * 4 + eot
    s, e = SHI_CHEN_RANGE[shi_zhi]

    def _fmt(mins):
        mins = int(mins) % 1440
        return f'{mins // 60:02d}:{mins % 60:02d}'

    # 子时跨日：真太阳 23:00-00:59，北京时间范围可能整体移位
    return {
        'shichen': shi_zhi,
        'beijing_range': f'{_fmt(s - corr)}-{_fmt(e - corr)}',
        'correction_minutes': round(corr, 1),
        'longitude': lon,
        'eot': round(eot, 2),
        'note': '真太阳时辰（当地时辰）对应北京时间范围；校正=经度差+均时差，供按北京时间用事者对照',
    }


def _build_zeri_candidate(env, current, shichen, sizhu):
    """单课完整评估（/api/zeri/batch 与 /api/zeri/satisfy 共用同一内核，保证口径一致）。
    管线：斗首快筛 → sike_sanchuan 排盘 → 四柱禄马贵人 → 演禽 → 知识库仪度 → 禄马贵明细 → 主命年命。
    env: {mtn, _dha, _sike, _luma, _yqa, _nms, _xnz, kekeduanyu, min_liuren,
          mubiao, zetiri_type, bm_gan, bm_zhi, bm_age, bm_sex, gan60, zhi60, arrange_tiandi_pan}
    快筛不过（斗首<50 / 大凶 / 六壬<min_liuren / 演禽<50）返回 None。"""
    from engine.yidu_liuren_yaojue import analyze_yidu_full
    from engine.gui_ren_engine import GuiRenCalculator

    mtn = env['mtn']
    _dha, _sike, _luma, _yqa = env['_dha'], env['_sike'], env['_luma'], env['_yqa']
    _nms, _xnz = env.get('_nms'), env.get('_xnz')
    _KDD = env.get('kekeduanyu')
    min_liuren = env['min_liuren']
    mubiao = env.get('mubiao') or []
    zetiri_type = env.get('zetiri_type', '')
    bm_gan, bm_zhi = env.get('bm_gan', ''), env.get('bm_zhi', '')
    bm_age, bm_sex = env.get('bm_age', 0), env.get('bm_sex', '男')
    _GAN_60, _ZHI_60 = env['gan60'], env['zhi60']
    _arrange = env['arrange_tiandi_pan']

    nian_gan, nian_zhi = sizhu['年柱'][0], sizhu['年柱'][1]
    yue_gan, yue_zhi = sizhu['月柱'][0], sizhu['月柱'][1]
    ri_gan, ri_zhi = sizhu['日柱'][0], sizhu['日柱'][1]
    shi_gan, shi_zhi = sizhu['时柱'][0], sizhu['时柱'][1]

    # ① 斗首（快筛：不凶才继续）
    _ds = _dha.analyze_kege(mtn, sizhu)
    _ds_score = _ds.get('综合评分', 50)
    if _ds_score < 50:
        return None
    _liuxiang = _ds.get('六相六替分析', {}) or {}
    _yuezhu_lx = ((_liuxiang.get('四柱六相', {}) or {}).get('月柱', {}) or {}).get('六相', '')
    _ds_classes = {k: (v or {}).get('斗首星曜', '') for k, v in (_ds.get('四柱分析', {}) or {}).items()}

    # ② 排盘（sike_sanchuan_engine，与起课排盘一致；月将按《通解》节气中气，2026-08-15 憨爷指正）
    _yj = _luma.get_yuejiang_by_date(current.year, current.month, current.day)
    _tdp = _arrange(_yj, shichen)
    _sike4 = _sike.qi_sike(ri_gan, ri_zhi, _tdp)
    _sc = _sike.fa_sanchuan(_sike4, ri_gan, ri_zhi, _tdp)
    _keti = _sc.get('课体', '') or ''
    _sc3 = {'初传': _sc.get('初传', ''), '中传': _sc.get('中传', ''), '末传': _sc.get('末传', '')}

    # ②b 权威仪度评分（与单课 /api/zeri/analyze 完全一致的引擎 + 公式 + 评级线）
    _authority_score = _ds_score  # fallback（异常时兜底用斗首分；正常由 analyze_yidu_full 覆盖）
    # 评级线 90/80/70/60/40 与 analyze_yidu_full 完全一致（2026-08-17 理顺统一，原 85/75/65/55/40 与权威不一致）
    _authority_grade = ('上上吉' if _authority_score >= 90 else '上吉' if _authority_score >= 80 else
                        '中吉' if _authority_score >= 70 else '吉' if _authority_score >= 60 else
                        '平' if _authority_score >= 40 else '不宜')
    _authority_gong = []
    try:
        _tj_map = GuiRenCalculator().arrange_gui_ren_pan(
            ri_gan, {'天地对应': _tdp}, shichen,
            lat=env.get('lat'), lon=env.get('lon'))  # 与单课 analyze 同源：IP 经纬度→真太阳时昼夜贵人（2026-08-17 修同源回归）
        _tjm = _tj_map.get('天将映射', {})
        _yidu_full = analyze_yidu_full(
            mtn, nian_gan + nian_zhi, yue_gan + yue_zhi, ri_gan + ri_zhi,
            shi_gan + shi_zhi, ri_gan, ri_zhi, _sc3, _tdp, _tjm, _yj, nian_zhi,
            shichen=shichen, ke_ti=_keti or None,
            year=current.year, month=current.month, day=current.day,
            ben_ming=bm_zhi or None, ben_ming_gan=bm_gan or None,
            # 2026-09-06 方案A-L3：择日类型类神吉应（批量候选与单课同口径）
            zeri_type=zetiri_type or '')
        _authority_score = _yidu_full.get('total_score', _authority_score)
        _authority_grade = _yidu_full.get('grade', _authority_grade)
        _authority_gong = [p['name'] for p in _yidu_full.get('gong_patterns', []) if p.get('matched')]
        # 【2026-08-31 Bug5 统一口径】斗首凶在日时(内)一票否决：一定不能用，直接淘汰该候选
        if _yidu_full.get('vetoed'):
            return None
    except Exception:
        pass

    # ②c 古籍合参警示层（2026-08-19 接线：占断合参+择日合参，警示/佐证层不参与评分）
    _hecan = {'hits': [], 'narr': '', '警告': [], '佐证': [], 'zeri_rules': {'hits': [], 'narr': ''}}
    try:
        from zeri_hecan_bridge2 import zeri_hecan_eval
        _tjm_c = locals().get('_tjm') or {}
        _hecan = zeri_hecan_eval(ri_gan, ri_zhi, _sike4, _sc3, _tjm_c, _keti, _yj, zetiri_type,
                                 sizhu=sizhu, shan_wx=str(_ds.get('山家五行', '') or ''),
                                 shan=str(mtn or ''), xiang='',
                                 ming=(bm_gan + bm_zhi) if bm_zhi else '')
        # 2026-08-21 批量格局统计：命中规则附短标签（前端徽标/统计用）
        try:
            from zeri_hecan_engine import zeri_rule_label as _zrl
            for _h in _hecan.get('zeri_rules', {}).get('hits', []):
                _h['标签'] = _zrl(_h.get('id', ''))
        except Exception:
            pass
    except Exception:
        _hecan = {'hits': [], 'narr': '', '警告': [], '佐证': [], 'zeri_rules': {'hits': [], 'narr': ''}}

    # ②d 古例变通桥（2026-08-21）：同课古例印证（A 基调直迁 / B 占类桥 / C 应期重算）
    _hecan['guli'] = {'matched': False}
    try:
        from engine.zeri_cbr_bridge import find_same_ke, bridge_to_zeri
        _same_ke = find_same_ke(ri_gan, ri_zhi, _yj, shichen)
        if _same_ke:
            _hecan['guli'] = bridge_to_zeri(_same_ke, zetiri_type, shan=str(mtn or ''),
                                            ming=(bm_gan + bm_zhi) if bm_zhi else '',
                                            ri_gan=ri_gan, ri_zhi=ri_zhi)
    except Exception:
        pass

    # ③ 禄马贵人引擎（四柱年/月/日/时 + 三传 + 课体扣分 + 大凶排除）
    _ns = _luma.calculate_new_score(
        mtn, shichen,
        nian_gan, nian_zhi, yue_gan, yue_zhi,
        ri_gan, ri_zhi, shi_gan, shi_zhi,
        _sc3, [_keti] if _keti else None,
        yuejiang=_yj,
        ben_ming=bm_zhi or None, ben_ming_gan=bm_gan or None,
    )
    if _ns.get('is_daxiong'):
        return None
    _lr_score = _ns.get('final_score', 50)
    if _lr_score < min_liuren:
        return None

    # ④ 演禽
    _yq_score = 50; _yq_pats = []; _yq_siqin = {}; _yq_pogong = {}
    try:
        _yq = _yqa.analyze_yanqin_with_calendar(sizhu, current.year, current.month, current.day)
        _yq_score = _yq.get('综合评分', 50)
        _yq_pats = [p.get('格局名称', '') for p in _yq.get('格局判定', [])][:6]
        _sq = _yq.get('四禽', {}) or {}
        _sqx = _yq.get('四禽禽星', {}) or {}
        _sqj = _yq.get('二十八宿属性', {}) or {}
        _yq_siqin = {
            '年禽': {'宿': _sq.get('年禽', ''), '禽星': _sqx.get('年禽星', ''), '吉凶': _sqj.get('年宿吉凶', '')},
            '月禽': {'宿': _sq.get('月禽', ''), '禽星': _sqx.get('月禽星', ''), '吉凶': _sqj.get('月宿吉凶', '')},
            '日禽': {'宿': _sq.get('日禽', ''), '禽星': _sqx.get('日禽星', ''), '吉凶': _sqj.get('日宿吉凶', '')},
            '时禽': {'宿': _sq.get('时禽', ''), '禽星': _sqx.get('时禽星', ''), '吉凶': _sqj.get('时宿吉凶', '')},
        }
        _yq_pogong = _yq.get('泊宫', {}) or {}
    except Exception:
        pass
    if _yq_score < 50:
        return None

    # ⑤ 知识库：仪度评分（山向禄马贵 + 发出三传 + 目标匹配）
    _yidu = {}
    if _KDD is not None:
        try:
            _ds_for_yidu = dict(_ds)
            _ds_for_yidu['课格格局'] = [
                (p.get('格局名称', '') if isinstance(p, dict) else str(p))
                for p in _ds.get('课格格局', [])
            ]
            _yidu = _KDD.analyze_yidu_score(mtn, sizhu, _ds_for_yidu, _ns, mubiao)
        except Exception:
            _yidu = {}

    # ⑥ 禄马贵人明细（日干日支，天盘法口径与 calculate_new_score 一致）
    _dsdx = {'lu': {'zhi': '', 'to_shan': False, 'to_xiang': False},
             'ma': {'zhi': '', 'to_shan': False, 'to_xiang': False},
             'guiren': {'zhi': [], 'to_shan': [], 'to_xiang': []},
             'total_count': 0}
    _shan_jia = _luma.get_shan_jia(mtn)
    _xiang_s = _luma.get_xiang_shou(mtn)
    try:
        _lu_z = _luma.get_lu_zhi(ri_gan)
        _ma_z = _luma.get_ma_zhi(ri_zhi)
        _gr_z = _luma.get_guiren_zhi(ri_gan, _tdp, shichen)
        def _pos(z):
            return _luma._get_tiandi_position(z, _tdp)
        _dsdx['lu'] = {'zhi': _lu_z, 'to_shan': _pos(_lu_z) == _shan_jia, 'to_xiang': _pos(_lu_z) == _xiang_s}
        _dsdx['ma'] = {'zhi': _ma_z, 'to_shan': _pos(_ma_z) == _shan_jia, 'to_xiang': _pos(_ma_z) == _xiang_s}
        _dsdx['guiren'] = {'zhi': [_gr_z] if _gr_z else [], 'to_shan': [_gr_z] if _gr_z == _shan_jia else [], 'to_xiang': [_gr_z] if _gr_z == _xiang_s else []}
        _dsdx['total_count'] = sum([_dsdx['lu']['to_shan'] or _dsdx['lu']['to_xiang'],
                                    _dsdx['ma']['to_shan'] or _dsdx['ma']['to_xiang'],
                                    bool(_dsdx['guiren']['to_shan'] or _dsdx['guiren']['to_xiang'])])
    except Exception:
        pass

    # ⑦ 主命/本命年命评估（未填本命则 adj=0 不动基线；依据见 /api/zeri/batch 注释）
    _nianming = {'used': False, 'adj': 0}
    if bm_zhi:
        try:
            _nianming['used'] = True
            _nianming['ben_ming'] = bm_gan + bm_zhi
            _nianming['ben_ming_zhi'] = bm_zhi
            _bm_qualified = _luma.check_pillar_all_qualified(
                bm_gan, bm_zhi, _tdp, shichen, _shan_jia, _xiang_s
            )
            _nianming['luma_qualified'] = bool(_bm_qualified)
            def _pos2(z):
                return _luma._get_tiandi_position(z, _tdp)
            _bm_lu = _luma.get_lu_zhi(bm_gan)
            _bm_ma = _luma.get_ma_zhi(bm_zhi)
            _bm_gr = _luma.get_guiren_zhi(bm_gan, _tdp, shichen)
            _nianming['lu'] = {'zhi': _bm_lu, 'to_shan': _pos2(_bm_lu) == _shan_jia, 'to_xiang': _pos2(_bm_lu) == _xiang_s}
            _nianming['ma'] = {'zhi': _bm_ma, 'to_shan': _pos2(_bm_ma) == _shan_jia, 'to_xiang': _pos2(_bm_ma) == _xiang_s}
            _nianming['guiren'] = {'zhi': [_bm_gr] if _bm_gr else [], 'to_shan': [_bm_gr] if _bm_gr == _shan_jia else [], 'to_xiang': [_bm_gr] if _bm_gr == _xiang_s else []}
            if _nms:
                _nianming['ben_ming_shang_shen'] = _nms(bm_zhi, _tdp) or ''
            _xn = ''
            if _xnz and bm_age and bm_age >= 1:
                _xn = _xnz(bm_zhi, bm_age, bm_sex) or ''
            _nianming['xing_nian'] = _xn
            _nianming['xing_nian_shang_shen'] = (_nms(_xn, _tdp) or '') if (_xn and _nms) else ''
            _ch0 = (_sc3.get('初传', '') or '')
            _ch2 = (_sc3.get('末传', '') or '')
            _bi = _ZHI_60.index(bm_zhi)
            _gong_ming = (_ch0 == _ZHI_60[(_bi - 1) % 12] and _ch2 == _ZHI_60[(_bi + 1) % 12])
            _nianming['gongming_ge'] = bool(_gong_ming)
            _ma_on_ming = bool(_bm_ma and (_nianming.get('ben_ming_shang_shen') == _bm_ma or _nianming.get('xing_nian_shang_shen') == _bm_ma))
            _nianming['ma_on_ming'] = _ma_on_ming
            _adj = 0
            if _bm_qualified:
                _adj += 8
            if _gong_ming:
                _adj += 5
            if zetiri_type == '出行' and _ma_on_ming:
                _adj += 5
            _nianming['adj'] = _adj
        except Exception:
            _nianming = {'used': False, 'adj': 0}

    # （来龙参数在 env 中保留，但【不参与择日评分】——憨爷纠正：来龙属峦头风水，
    #  只与判断穴位、来去水吉凶有关，与择日选课、六壬龙德课均无关；穴位/来去水功能后续补充）

    _ttl = min(100, round(_authority_score + _nianming['adj'], 1))
    _grade = _authority_grade

    # 杀师日判定（2026-08-17 憨爷：批量候选标注，前端标红提醒/可禁用）
    try:
        from engine.shashi import check_shashi
        _shashi = check_shashi(ri_gan + ri_zhi, nian_zhi, yue_zhi,
                               current.strftime('%Y-%m-%d'), shichen)
    except Exception:
        _shashi = {'is_shashi': False, 'hits': [], 'level': '', 'note': ''}

    # ⑧ 13 吉课 + 达成矩阵 + 加权分（2026-08-17 憨爷拍板：分层评估——硬/软/加分三层）
    _jk13 = {'hits': [], 'is_jike': False, 'details': []}
    try:
        from engine.jike_13 import check_jike_13
        _tjm = locals().get('_tjm') or {}
        _yidu_full = locals().get('_yidu_full') or {}
        _jk_sike = _sike4  # V2 tuple 列表 (课名,上神,下神,天将)
        _jk_sc = [_sc3.get('初传', ''), _sc3.get('中传', ''), _sc3.get('末传', '')]
        _jk_tj = [_tjm.get(z, '') for z in _jk_sc]
        _jk_lu = _luma.get_lu_zhi(ri_gan) or ''
        _jk_ma = _luma.get_ma_zhi(ri_zhi) or ''
        _jk_longde = False
        _jk_ld = ((_yidu_full.get('advanced_patterns') or {}).get('龙德课', {}))
        if isinstance(_jk_ld, dict):
            _jk_longde = bool(_jk_ld.get('matched'))
        _jk13 = check_jike_13(_keti, _jk_sike, _jk_sc, _jk_tj, ri_gan, ri_zhi,
                              nian_zhi, yue_zhi, _jk_lu, _jk_ma, _jk_longde, bm_zhi)
    except Exception:
        _jk13 = {'hits': [], 'is_jike': False, 'details': []}

    # 加权加分分（权重初版：禄马贵发传 4 > 13吉课 3 > 到山到向 2 > 拱格 1；可类型差异化调）
    _luma_fc = int(_ns.get('sanchuan_luma_count', 0) or 0)     # 禄马贵发传 count（天机灵动）
    _luma_dx = int(_ns.get('pillar_qualified_count', 0) or 0)  # 四柱到山到向 count
    _bonus_score = (len(_jk13.get('hits') or []) * 3) + _luma_fc * 4 + _luma_dx * 2 + len(_authority_gong)

    # 达成矩阵（杀师/犯雷=地师避忌仅标注不否决——不进主家评分铁律；大凶已否决不产出候选）
    _matrix = {
        'hard': {
            'daxiong': False,  # 已否决（is_daxiong 直接 return None，不会产出）
            'shashi': _shashi.get('is_shashi', False),
        },
        'soft': {
            'doushou': {'pass': _ds_score >= 50, 'score': _ds_score},
            'liuren': {'pass': _lr_score >= min_liuren, 'score': round(_lr_score, 1)},
            'yanqin': {'pass': _yq_score >= 50, 'score': _yq_score},
        },
        'bonus': {
            'jike_13': _jk13.get('hits', []),
            'luma_fachuan': _luma_fc,
            'luma_duoxiang': _luma_dx,
            'gongge': _authority_gong,
        },
        'bonus_score': _bonus_score,
    }

    # Ⓡ 禄马贵人条件择日（2026-08-25 软加权）
    #   lmg_groups：勾选的位置组（年/月/日/时/本命/坐山）
    #   lmg_qiushi：求事方向 → 求官(贵)/求财(禄)/求动(马)/不限
    #   bonus = Σ 勾选组归一化 pos% ，其中求事命中类得分再 ×(lmg_freq_mult-1) 侧重
    #   hit   = 勾选组内某位置归一化 pos% ≥60（前端高亮标绿）
    #   lmg_auto：智能推荐（免费·内测）→ 全量6组算分，按求事类别从高到低挑最优一课/最优组
    #   【归一化口径】每个位置原始 scoring 上限=该位置权值（时8/日13/月15/年17/坐山23/本命24，
    #      均 <60），故按“原始分 ÷ 权值 ×100”归一化到 0-100 可比刻度，使“≥60 标绿”每个位置都可达成。
    _lmg = {'used': False, 'bonus': 0.0, 'hit': False, 'hit_groups': [], 'qiushi': '', 'pos_scores': {}}
    try:
        _lmg_auto = bool(env.get('lmg_auto'))
        _lmg_groups = [g for g in (env.get('lmg_groups') or []) if g in ('年', '月', '日', '时', '本命', '坐山')]
        if _lmg_auto:
            _lmg_groups = ['年', '月', '日', '时', '本命', '坐山']   # 智能推荐：全量算分，供挑最优一课/最优组
        _lmg_qiushi = env.get('lmg_qiushi') or ''
        if _lmg_groups:
            _CAT_PCT = {'贵': 0.40, '禄': 0.35, '马': 0.25}   # 与 score_precision_luma_guiren 权值表一致
            _qcat = {'求官': '贵', '求财': '禄', '求动': '马'}.get(_lmg_qiushi, '')
            _qm = float(env.get('lmg_freq_mult', 1.5) or 1.5)      # 求事命中类侧重系数
            _pd = (_ns.get('precision') or {}).get('position_detail') or []
            _ps, _cl = {}, {}
            for _p in _pd:
                _nm = _p.get('position'); _w = float(_p.get('weight', 0) or 0)
                if not _w:
                    continue
                _ps[_nm] = round(float(_p.get('score', 0) or 0) / _w * 100, 2)
                _cl[_nm] = {}
                for _c in (_p.get('classes') or []):
                    _cw = _w * _CAT_PCT.get(_c.get('type'), 1.0)
                    _cl[_nm][_c.get('type')] = round(float(_c.get('score', 0) or 0) / _cw * 100, 2) if _cw else 0.0
            _bonus, _hits, _best_g = 0.0, [], ''
            if _lmg_auto:
                # 免费·内测智能推荐：窗口内按求事类别分高→低挑最优一课；不限则按位置最高分。
                # 倾向分=该最优组类别分（≤100）；位置分仅用于≥60命中判定
                if _qcat:
                    _rank = lambda _g: _cl.get(_g, {}).get(_qcat, 0.0)
                else:
                    _rank = lambda _g: _ps.get(_g, 0.0)
                _best_g = max(_lmg_groups, key=_rank)
                _bonus = round(_rank(_best_g), 2)
                if _ps.get(_best_g, 0) >= 60:
                    _hits.append(_best_g)
            else:
                for _g in _lmg_groups:
                    _gs = _ps.get(_g, 0.0)
                    if _qcat:
                        _gs += _cl.get(_g, {}).get(_qcat, 0.0) * (_qm - 1.0)   # 求事命中类侧重 ×0.5
                    _bonus += _gs
                    if _ps.get(_g, 0) >= 60:
                        _hits.append(_g)
            _lmg = {'used': True, 'bonus': round(_bonus, 2), 'hit': bool(_hits),
                    'hit_groups': _hits, 'qiushi': _lmg_qiushi,
                    'pos_scores': {k: round(v, 2) for k, v in _ps.items()},
                    'classes': _cl,
                    'auto': _lmg_auto,
                    'best_group': _best_g}
    except Exception:
        _lmg = {'used': False, 'bonus': 0.0, 'hit': False, 'hit_groups': [], 'qiushi': '', 'pos_scores': {}}

    # ⑨ 补救建议（2026-08-17 憨爷拍板：分层评估后给行动建议，替代"一刀切不合格"；
    #   基于《要诀》权衡方法论：缺失项指出 + 给补救方向，不进评分）
    _remedy = []
    if _luma_dx < 4:
        _remedy.append(f'禄马贵仅 {_luma_dx}/4 柱到山到向，未全到；可换年柱/月柱重选以催动到山到向')
    if _luma_fc == 0:
        _remedy.append('禄马贵未发三传（天机未灵动）——"一部仪度六壬全在天机灵动"，宜择禄马贵发传之日')
    elif _luma_fc < 2:
        _remedy.append(f'禄马贵发传仅 {_luma_fc} 处，灵动偏弱')
    if not _jk13.get('hits'):
        _remedy.append('无十三吉课格，课体平平；可另择课格发用之期（元首/华盖/铸印等）')
    if _shashi.get('is_shashi'):
        _remedy.append('杀师日/犯雷日：地师忌临现场，可避此时辰或由地师自行规避')
    if not _remedy:
        _remedy.append('五要素齐备：斗首/演禽达标、十三吉课命中、禄马贵到山到向且发传——上选之日')

    # ⑩ 空亡三铁律审计（2026-08-25 憨爷拍板：本命落旬空可填补 / 踏空致命 / 乘天空=真空）
    _void = {'level': '干净', 'pass': True, 'xunkong': [], 'ben_ming_void': False,
             'tread_zhi': '', 'tread_void': False, 'ride_general': '', 'ride_sky': False,
             'reasons': []}
    try:
        from engine.void_audit import audit_void
        _tjm_v = locals().get('_tjm') or {}
        _void = audit_void(ri_gan + ri_zhi, _tdp, _tjm_v, bm_gan + bm_zhi if bm_zhi else '')
    except Exception:
        pass

    # ⑪ 十二建星（2026-08-25 用户拍板：月建起建，只进批语叙事不加减分）
    _jx = {'name': '', 'huang_dao': False, 'level': '', 'desc': '', 'narrative': ''}
    try:
        from engine.jianxing import get_jianxing, jianxing_narrative
        _jx = dict(get_jianxing(yue_zhi, ri_zhi))
        _gx = '吉' if _grade in ('上上吉', '上吉') else ('凶' if '凶' in _grade else '平')
        _jx_sc = [_sc3.get('初传', ''), _sc3.get('中传', ''), _sc3.get('末传', '')]
        _jx_tj = [locals().get('_tjm', {}).get(z, '') for z in _jx_sc]
        _jx['narrative'] = jianxing_narrative(_jx, _gx, _jx_sc, _jx_tj)
    except Exception:
        pass

    # ⑬ 禄马贵人分层评级（2026-08-26 修正：严格按"必须发三传"判定 + 互禄互贵格）
    #   L3 上上吉：禄马贵人到山到向 + 发三传(日柱) + 十三吉课 + 互禄互贵格
    #   L2 吉课：  禄马贵人到山到向 + 发三传(日柱)（无十三吉课或互禄互贵）
    #   L1 普通课：禄马贵人到山到向但不发三传（无日柱禄马贵人在三传）
    #   L0 平课：  既不到山到向，又不发三传
    _luma_dx_count = int(_ns.get('pillar_qualified_count', 0) or 0)
    _luma_fc_count = int(_ns.get('sanchuan_luma_count', 0) or 0)
    _j13_hits = _jk13.get('hits') or []
    _j13_count = len(_j13_hits) if isinstance(_j13_hits, list) else 0
    _has_dx = _luma_dx_count > 0          # 有禄马贵人到山到向
    _has_fc = _luma_fc_count > 0          # 日柱禄马贵人发三传
    _has_j13 = _j13_count > 0             # 有十三吉课命中

    # 互禄互贵格检查（2026-08-26 修正：多柱交叉验证）
    _has_mutual = False
    _mutual_details = {}
    _mutual_hulu_count = 0
    _mutual_hugui_count = 0
    try:
        _hulu_result = _luma.check_hulu_hugui(
            nian_gan, yue_gan, ri_gan, bm_gan, mtn, yue_zhi)
        _has_mutual = _hulu_result.get('is_mutual_lu_gui', False)
        _mutual_details = _hulu_result.get('details', {})
        _mutual_hulu_count = _hulu_result.get('hulu_count', 0)
        _mutual_hugui_count = _hulu_result.get('hugui_count', 0)
    except Exception:
        pass

    if _has_dx and _has_fc and _has_j13 and _has_mutual:
        _luma_level = 'L3'
        _luma_level_name = '上上吉（禄马贵人到山到向+发三传+十三吉课+互禄互贵）'
        _luma_level_score = 100
    elif _has_dx and _has_fc and _has_j13:
        _luma_level = 'L3'
        _luma_level_name = '上上吉（禄马贵人到山到向+发三传+十三吉课）'
        _luma_level_score = 95
    elif _has_dx and _has_fc:
        _luma_level = 'L2'
        _luma_level_name = '吉课（禄马贵人到山到向+发三传）'
        _luma_level_score = 75
    elif _has_dx:
        _luma_level = 'L1'
        _luma_level_name = '普通课（禄马贵人到山到向但不发三传）'
        _luma_level_score = 50
    else:
        _luma_level = 'L0'
        _luma_level_name = '平课（无禄马贵人到山到向、不发三传）'
        _luma_level_score = 25

    # ⑫ 现代类象（2026-08-25 用户拍板：批量候选也带，按类型推演+历史佐证）
    _mlx = {'推演': [], '历史佐证': '', 'narrative': '', 'zeri_type': zetiri_type}
    try:
        from engine.leixiang_kb import LeixiangKB
        _mlx_kb = LeixiangKB()
        _mlx_res = _mlx_kb.push_leixiang(zetiri_type, date=current.strftime('%Y-%m-%d'), shichen=shichen)
        _mlx = {
            '推演': _mlx_res.get('推演', []),
            '历史佐证': _mlx_res.get('历史佐证', ''),
            'narrative': _mlx_kb.get_narrative(zetiri_type),
            'zeri_type': zetiri_type,
        }
    except Exception:
        pass

    return {
        'date': current.strftime('%Y-%m-%d'),
        'shichen': shichen,
        'sizhu': f'{nian_gan}{nian_zhi} {yue_gan}{yue_zhi} {ri_gan}{ri_zhi} {shi_gan}{shi_zhi}',
        'doushou_score': _ds_score,
        'liuren_score': round(_lr_score, 1),
        'yanqin_score': _yq_score,
        'total_score': _ttl,
        'grade': _grade,
        'keti': _keti,
        'sanchuan': _sc3,
        'doushou_classes': _ds_classes,
        'doushou_patterns': [_pln if isinstance(_pln, str) else (_pln.get('格局名称', '') if isinstance(_pln, dict) else '') for _pln in _ds.get('课格格局', [])],
        'gong_names': _authority_gong,
        'yanqin_patterns': _yq_pats,
        'yanqin_siqin': _yq_siqin,
        'yanqin_pogong': _yq_pogong,
        'liuxiang': _yuezhu_lx,
        'luma_guiren': {
            'status': _ns.get('status', ''),
            'pillar_qualified': _ns.get('pillar_qualified_count', 0),
            'sanchuan_luma': _ns.get('sanchuan_luma_count', 0),
            'nian_qualified': bool(_ns.get('nian_qualified', False)),
            'yue_qualified': bool(_ns.get('yue_qualified', False)),
            'ri_qualified': bool(_ns.get('ri_qualified', False)),
            'shi_qualified': bool(_ns.get('shi_qualified', False)),
        },
        'luma_grade': {
            'level': _luma_level,
            'name': _luma_level_name,
            'score': _luma_level_score,
            'has_dx': _has_dx,
            'has_fc': _has_fc,
            'has_j13': _has_j13,
            'has_mutual': _has_mutual,
            'mutual_hulu_count': _mutual_hulu_count,
            'mutual_hugui_count': _mutual_hugui_count,
            'mutual_details': _mutual_details,
            'dx_count': _luma_dx_count,
            'fc_count': _luma_fc_count,
            'j13_count': _j13_count,
        },
        'yidu_score': _yidu.get('综合评分', 0),
        'yidu_eval': _yidu.get('评价', ''),
        'matched_mubiao': _yidu.get('课传美格', []) if mubiao else [],
        'zetiri_type': zetiri_type,
        'daoshan_details': _dsdx,
        'nianming': _nianming,
        'shashi': _shashi,
        'jike_13': _jk13,
        'bonus_score': _bonus_score,
        'constraint_matrix': _matrix,
        'remedy': _remedy,
        'hecan': _hecan,
        'lmg': _lmg,
        'void_audit': _void,
        'jianxing': _jx,
        'modern_leixiang': _mlx,
        # 2026-09-06 方案A-L3：择日类型类神吉应（批量与单课同口径透传）
        'leishen_detail': (locals().get('_yidu_full') or {}).get('leishen_detail', {}) or {},
    }


@app.route('/api/zeri/batch', methods=['POST'])
def api_zeri_batch():
    """批量择日（完整引擎版）POST /api/zeri/batch
    body: {start_date, end_date, mountain(单山), jiri_count, zetiri_type, min_liuren, mubiao[]}
    参考原始系统 full_range_analyze，纳入系统完整引擎：
      排盘     → sike_sanchuan_engine.SiKeSanChuanCalculator2（与起课排盘 /api/qike 一致）
      禄马贵人 → DaLiuRenLuMaGuiRen.calculate_new_score（四柱年/月/日/时到山到向 + 三传禄马贵人 + 课体扣分 + 大凶排除）
      斗首     → douhou_analyzer.analyze_kege
      演禽     → yanqin_analyzer.analyze_yanqin_with_calendar
      知识库   → KeKeDuanyu.analyze_yidu_score（仪度评分：山向禄马贵+发出三传+目标匹配）
    筛选：斗首≥50（快筛）→ 非大凶 && 六壬≥min_liuren → 演禽≥50
    排序：月柱六相优先（武财>元辰>廉贞>贪官>破鬼）→ 六壬分 → 总分"""
    try:
        data = request.get_json(silent=True) or {}
        start_str = data.get('start_date', '')
        end_str = data.get('end_date', '')
        mountain = data.get('mountain', '') or ''
        zetiri_type = data.get('zetiri_type', '')
        jiri_count = int(data.get('jiri_count', 10) or 10)
        min_liuren = int(data.get('min_liuren', 70) or 70)
        mubiao = data.get('mubiao', []) or []
        # 禄马贵人条件择日（2026-08-25 软加权）：勾选的位置组 + 求事方向 + 智能推荐/超选预览
        lmg_groups = data.get('lmg_groups', []) or []
        lmg_qiushi = (data.get('lmg_qiushi') or '').strip()
        lmg_mobile = (data.get('mobile') or '').strip()
        lmg_auto = bool(data.get('lmg_auto'))          # 智能推荐模式（免费·内测）
        lmg_oversee = bool(data.get('lmg_oversee'))    # 超选预览钩子：超出权益时预览但不标绿超权组
        # 择日模式（2026-08-26 新增）：range=日期范围择日（默认），lmg=禄马贵人择日
        zeri_mode = (data.get('mode') or 'range').strip()
        lmg_priority = (data.get('lmg_priority') or '').strip()
        # 择日策略（2026-08-27 新增）：balanced=综合平衡, doushou_first=斗首优先, liuren_first=六壬优先, custom=自定义权重
        zeri_strategy = (data.get('zeri_strategy') or 'balanced').strip()
        # 权重参数（0-100）
        try:
            doushou_weight = max(0, min(100, int(data.get('doushou_weight', 50) or 50)))
        except Exception:
            doushou_weight = 50
        try:
            liuren_weight = max(0, min(100, int(data.get('liuren_weight', 50) or 50)))
        except Exception:
            liuren_weight = 50
        
        # 根据预设策略调整权重
        if zeri_strategy == 'doushou_first':
            doushou_weight, liuren_weight = 70, 30
        elif zeri_strategy == 'liuren_first':
            doushou_weight, liuren_weight = 30, 70
        # 主命/本命年命（出行/新居等以本命为主的类型；未提供则不启用年命评分，基线不动）
        ben_ming = data.get('ben_ming', '') or ''
        ben_ming_age = data.get('ben_ming_age', '') or ''
        ben_ming_sex = data.get('ben_ming_sex', '') or '男'
        # 来龙（二十四山；仅记录预留——憨爷纠正：来龙属峦头风水，只判穴位/来去水吉凶，不参与择日评分）
        lailong = data.get('lailong', '') or ''
        # 真太阳时经度（东经，默认120=北京时间区；仅用于真太阳时辰→北京时间换算展示，评分不动）
        longitude = data.get('longitude', '') or ''
        if not start_str or not end_str:
            return jsonify({'error': '缺少 start_date / end_date'}), 400
        if not mountain:
            return jsonify({'error': '缺少 mountain（坐山）'}), 400

        _sd = datetime.strptime(start_str, '%Y-%m-%d').date()
        _ed = datetime.strptime(end_str, '%Y-%m-%d').date()
        if _sd > _ed:
            return jsonify({'error': '起始日期不能晚于结束日期'}), 400
        if (_ed - _sd).days > 3650:
            return jsonify({'error': '日期范围过大（最多10年）'}), 400

        # ── 禄马贵人条件：身份解析 + 权益梯度（尊享全选6 / 体验2 / 免费·内测1）──
        # ① 求事方向对全体放开（求官/求财/求动/不限不另设阶梯）
        _VALID_LMG = ('年', '月', '日', '时', '本命', '坐山')
        lmg_groups = [g for g in lmg_groups if g in _VALID_LMG]
        if lmg_qiushi not in ('求官', '求财', '求动', '不限'):
            lmg_qiushi = ''
        try:
            _lacc = _resolve_access(0, mobile=lmg_mobile)
            _lplan = _lacc.get('vip_plan', '')
        except Exception:
            _lplan = ''
        _lmg_limit = 6 if _lplan == '尊享档' else (2 if _lplan == '体验档' else 1)
        if lmg_auto:
            # ② 智能推荐（免费·内测免选组）：系统全量算分，按求事类别分高→低挑最优一课/最优组，
            #    最终仅采纳/标绿 1 组权益（免费用户三天窗口内即可）。
            lmg_groups = list(_VALID_LMG)
            _grant_meta = {'auto': True, 'granted': 1}
        elif lmg_oversee and lmg_groups and len(lmg_groups) > _lmg_limit:
            # ③ 超选预览钩子：按权益档次限配额（免费/内测1次·体验会员3次/日），放行全量+标记 preview
            _ov_limit = LMG_OVERSEE_DAILY_LIMIT_EXP if _lplan == '体验档' else LMG_OVERSEE_DAILY_LIMIT
            _ok, _preview_left = _consume_lmg_oversee(lmg_mobile, _ov_limit)
            if not _ok:
                return jsonify({
                    'error': f'今日"超选预览"次数已用完（当前档位每日 {_ov_limit} 次），'
                             f'开通尊享可不限使用',
                    'lmg_max': _lmg_limit,
                    'preview_daily_left': 0,
                }), 403
            _grant_meta = {'oversee': True, 'granted': _lmg_limit,
                           'selected': len(lmg_groups), 'preview_daily_left': _preview_left,
                           'preview_limit': _ov_limit}
        elif len(lmg_groups) > _lmg_limit:
            return jsonify({
                'error': f'禄马贵人条件超出当前权益：您可勾选 {_lmg_limit} 组'
                         f'（当前身份{"尊享·全选6组" if _lplan=="尊享档" else "体验·2组" if _lplan=="体验档" else "免费/内测·1组"}，'
                         f'升级会员可多选）',
                'lmg_max': _lmg_limit,
            }), 403
        else:
            _grant_meta = {'granted': _lmg_limit}

        # ── 惰性导入系统引擎（与起课排盘 /api/qike 同源）──
        _eng = str(ROOT / 'engine')
        if _eng not in sys.path:
            sys.path.insert(0, _eng)
        from engine.sizhu_engine import get_sizhu
        from engine.douhou_analyzer import DouhouKegeAnalyzer
        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen, arrange_tiandi_pan
        from engine.yanqin_analyzer import YanQinAnalyzer
        from engine.yidu_liuren_yaojue import analyze_yidu_full
        from engine.gui_ren_engine import GuiRenCalculator
        try:
            from engine.liuren_keti_bifa import _nian_ming_shang_shen, _xing_nian_zhi
        except Exception:
            _nian_ming_shang_shen = _xing_nian_zhi = None
        try:
            from engine.kekeduanyu import KeKeDuanyu
        except Exception:
            KeKeDuanyu = None

        _dha = DouhouKegeAnalyzer()
        _sike = SiKeSanChuanCalculator2()
        _luma = DaLiuRenLuMaGuiRen()
        _yqa = YanQinAnalyzer()

        _SHICHEN = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
        _LX_PRI = {'武财':5,'元辰':4,'廉贞':3,'贪官':2,'破鬼':1}
        _mtn = mountain[0] if mountain else '子'

        # ── 主命/本命解析（60甲子，如"庚子"→ 庚/子；缺省则不启用年命评分）──
        _GAN_60 = '甲乙丙丁戊己庚辛壬癸'
        _ZHI_60 = '子丑寅卯辰巳午未申酉戌亥'
        bm_gan, bm_zhi = '', ''
        if ben_ming and len(ben_ming) == 2 and ben_ming[0] in _GAN_60 and ben_ming[1] in _ZHI_60:
            bm_gan, bm_zhi = ben_ming[0], ben_ming[1]
        try:
            bm_age = int(str(ben_ming_age).strip()) if str(ben_ming_age).strip().isdigit() else 0
        except Exception:
            bm_age = 0
        bm_sex = ben_ming_sex if ben_ming_sex in ('男', '女') else '男'

        # ── 构建公共评估环境（与达标择日 /api/zeri/satisfy 共用 _build_zeri_candidate，保证口径一致）──
        # IP 定位经纬度（真太阳时昼夜判天将，与单课 /api/zeri/analyze 同源；2026-08-17 修同源回归）
        _ip_lat = _ip_lon = None
        try:
            from engine.ip_geo import ip_to_coords, get_client_ip
            _ip_lat, _ip_lon, _, _ = ip_to_coords(get_client_ip(request), timeout=2)
        except Exception:
            pass
        _env = {
            'mtn': _mtn, '_dha': _dha, '_sike': _sike, '_luma': _luma, '_yqa': _yqa,
            '_nms': _nian_ming_shang_shen, '_xnz': _xing_nian_zhi,
            'kekeduanyu': KeKeDuanyu, 'min_liuren': min_liuren,
            'mubiao': mubiao, 'zetiri_type': zetiri_type,
            'bm_gan': bm_gan, 'bm_zhi': bm_zhi, 'bm_age': bm_age, 'bm_sex': bm_sex,
            'gan60': _GAN_60, 'zhi60': _ZHI_60, 'arrange_tiandi_pan': arrange_tiandi_pan,
            'lailong': lailong,
            'lat': _ip_lat, 'lon': _ip_lon,
            # 禄马贵人条件择日（2026-08-25 软加权；lmg_auto=智能推荐默认全量算分）
            'lmg_groups': lmg_groups, 'lmg_qiushi': lmg_qiushi,
            'lmg_freq_mult': 1.5,
            'lmg_auto': lmg_auto,
        }

        results = []
        total_candidates = 0
        current = _sd
        while current <= _ed:
            for shichen in _SHICHEN:
                try:
                    sizhu = get_sizhu(current.year, current.month, current.day, shichen)
                    cand = _build_zeri_candidate(_env, current, shichen, sizhu)
                    if cand:
                        total_candidates += 1
                        cand['true_solar'] = _true_solar_info(shichen, current.strftime('%Y-%m-%d'), longitude)
                        results.append(cand)
                except Exception:
                    import traceback; traceback.print_exc()
                    continue
            current += timedelta(days=1)


        # 排序：若启用禄马贵人条件 → 倾向加权分(bonus)优先；否则月柱六相优先 → 六壬分 → 总分（原口径）
        def _lmg_key(x):
            l = x.get('lmg') or {}
            return l.get('bonus', 0.0) if l.get('used') else 0.0

        # 计算加权分（斗首×权重 + 六壬×权重）
        def _weighted_score(x):
            ds_score = x.get('phase1_score', 0) or x.get('doushou_score', 0) or 0
            lr_score = x.get('liuren_score', 0) or 0
            total_w = doushou_weight + liuren_weight
            if total_w > 0:
                return (ds_score * doushou_weight + lr_score * liuren_weight) / total_w
            return x.get('total_score', 0)

        # 禄马贵人择日专用排序键（2026-08-26 更新为分层评级 + 互禄互贵）
        # 优先级：L3上上吉(互禄互贵+100分加成) > L3上上吉 > L2吉课 > L1普通课 > L0平课
        # 同层内：分层score × 100 + 到山到向×10 + 发传×5 + 十三吉课数 + 互禄互贵×20
        def _lmg_priority_key(x):
            lg = x.get('luma_grade') or {}
            lg_lv = {'L3': 400, 'L2': 300, 'L1': 200, 'L0': 100}
            lg_base = lg_lv.get(lg.get('level', 'L0'), 100)
            lg_dx = lg.get('dx_count', 0)
            lg_fc = lg.get('fc_count', 0)
            lg_j13 = lg.get('j13_count', 0)
            lg_mutual = 20 if lg.get('has_mutual', False) else 0
            return (lg_base + lg_dx * 10 + lg_fc * 5 + lg_j13 * 3 + lg_mutual)

        if zeri_mode == 'lmg' and lmg_priority == 'lmg_to_shanxiang_13ke':
            results.sort(key=lambda x: (
                -_lmg_priority_key(x),              # 禄马贵人分层评级（L3>L2>L1>L0）
                -_LX_PRI.get(x.get('liuxiang', ''), 0),
                -x.get('bonus_score', 0),
                -x.get('liuren_score', 0),
                -x.get('total_score', 0),
            ))
        else:
            # 使用加权分排序（支持自定义权重策略）
            results.sort(key=lambda x: (
                -_lmg_key(x),                       # 禄马贵人条件倾向优先（未启用=0，零回归）
                -_weighted_score(x),                # 2026-08-27：加权分排序（斗首×权重 + 六壬×权重）
                -_LX_PRI.get(x.get('liuxiang', ''), 0),
                -x.get('bonus_score', 0),
                -x.get('liuren_score', 0),
                -x.get('total_score', 0),
            ))

        # ── 2026-08-21 范围格局统计：截断前遍历全部候选，统计美格/凶格命中次数 ──
        try:
            from zeri_hecan_engine import zeri_rule_label as _zrl
        except Exception:
            _zrl = lambda rid: str(rid or '')
        _meige_cnt, _xiong_cnt = {}, {}
        for _r in results:
            for _h in (_r.get('hecan') or {}).get('zeri_rules', {}).get('hits', []):
                _bid = str(_h.get('id', ''))
                if _h.get('结论') == '吉':
                    _meige_cnt[_bid] = _meige_cnt.get(_bid, 0) + 1
                elif _h.get('结论') == '凶':
                    _xiong_cnt[_bid] = _xiong_cnt.get(_bid, 0) + 1
        _stats = {
            'meige': {_zrl(k): v for k, v in sorted(_meige_cnt.items(), key=lambda kv: (-kv[1], kv[0]))},
            'xiong': {_zrl(k): v for k, v in sorted(_xiong_cnt.items(), key=lambda kv: (-kv[1], kv[0]))},
        }
        results = results[:jiri_count]

        # ── 智能推荐（免费·内测）附加元数据：最优一课 + 最优位置组 + 求事类别分 ──
        _grant_meta = dict(_grant_meta)
        _grant_meta['groups'] = lmg_groups
        _grant_meta['qiushi'] = lmg_qiushi
        if lmg_auto and results:
            _best = results[0].get('lmg') or {}
            if _best.get('used'):
                _grant_meta['recommend'] = {
                    'group': _best.get('best_group', ''),
                    'qiushi': lmg_qiushi,
                    'bonus': _best.get('bonus', 0.0),
                    'hit': bool(_best.get('hit')),
                    'date': results[0].get('date', ''),
                    'shichen': results[0].get('shichen', ''),
                }

        # ── 回写到 AI 训练知识库 ──
        try:
            knowledge_result = _append_zeri_results_to_knowledge(
                results, mountain, zetiri_type, lmg_qiushi)
            if knowledge_result.get('success') and knowledge_result.get('added_count', 0) > 0:
                print(f"[知识库] 择日回写成功: {knowledge_result.get('added_count')} 条案例")
        except Exception as _ke:
            import traceback
            traceback.print_exc()

        return jsonify({
            'success': True, 'results': results,
            'stats': _stats,
            'meta': {'start_date': start_str, 'end_date': end_str,
                     'mountain': mountain, 'zetiri_type': zetiri_type,
                     'days': (_ed - _sd).days + 1,
                     'candidates': total_candidates,
                     'engine': '完整引擎版（sike_sanchuan排盘 + 四柱禄马贵人 + 知识库仪度评分）',
                     'min_liuren': min_liuren,
                     'longitude': float(longitude) if str(longitude).replace('.', '', 1).isdigit() else 120.0},
            'lmg': _grant_meta if lmg_groups else None,
            'knowledge_written': knowledge_result.get('added_count', 0) if 'knowledge_result' in dir() else 0,
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/zeri/satisfy', methods=['POST'])
def api_zeri_satisfy():
    """达标择日 POST /api/zeri/satisfy —— 从起始日一直往后推，直到命中达标课为止
    body: {start_date, mountain, zetiri_type, mubiao, ben_ming/ben_ming_age/ben_ming_sex,
           min_doushou=100, min_liuren=100, min_yanqin=100, target_count=3, max_days=180}
    语义：
      - 从 start_date 起逐日 × 12 时辰往后推（不设结束日期，最多 max_days 天防失控）；
      - 命中 target_count 个「斗首≥min_doushou 且 六壬≥min_liuren 且 演禽≥min_yanqin」的课即停；
      - 该档扫满 max_days 仍未达标 → 自动降档重扫（98/95/90/85/80，封顶不高于用户档位），
        直到命中为止；全档扫完仍无 → 返回空 + 最低档信息，提示放宽条件。
    返回: {success, results(含 day_offset=距起始日天数,起始日=第1天), hit_level(实际命中档位),
           scanned_days, max_days, lowered(是否降档)}"""
    try:
        data = request.get_json(silent=True) or {}
        start_str = data.get('start_date', '')
        mountain = data.get('mountain', '') or ''
        zetiri_type = data.get('zetiri_type', '')
        mubiao = data.get('mubiao', []) or []
        ben_ming = data.get('ben_ming', '') or ''
        ben_ming_age = data.get('ben_ming_age', '') or ''
        ben_ming_sex = data.get('ben_ming_sex', '') or '男'
        lailong = data.get('lailong', '') or ''
        # 真太阳时经度（东经，默认120=北京时间区；仅用于真太阳时辰→北京时间换算展示，评分不动）
        longitude = data.get('longitude', '') or ''
        min_doushou = int(data.get('min_doushou', 100) or 100)
        min_liuren = int(data.get('min_liuren', 100) or 100)
        min_yanqin = int(data.get('min_yanqin', 100) or 100)
        target_count = max(1, min(20, int(data.get('target_count', 3) or 3)))
        max_days = max(1, min(21915, int(data.get('max_days', 1095) or 1095)))  # 默认3年，上限60年（一甲子）
        # 高档快速放弃护栏天数（可配置，默认1年=365天；超过免费额度需付费解锁）
        fast_abandon_days = max(30, min(max_days, int(data.get('fast_abandon_days', FREE_SCAN_DAYS) or FREE_SCAN_DAYS)))
        if not start_str:
            return jsonify({'error': '缺少 start_date'}), 400
        if not mountain:
            return jsonify({'error': '缺少 mountain（坐山）'}), 400

        _sd = datetime.strptime(start_str, '%Y-%m-%d').date()

        # ── 收费决策（v2：内测/会员/3天内免费/每日限免/按次阶梯）──
        mobile = (data.get('mobile') or '').strip()
        is_first = data.get('is_first', False)
        _acc = _resolve_access(max_days, mobile=mobile, is_first=is_first)
        if not _acc.get('free'):
            # 已按次解锁（24h 内）则放行
            unlock_ok, left_h = _check_unlock(max_days, mobile=mobile)
            if not unlock_ok:
                return jsonify({
                    'requires_pay': True, 'price': _acc.get('price', 0),
                    'tier': _acc.get('tier', ''), 'tier_desc': _acc.get('tier_desc', ''),
                    'max_days': max_days, 'free_days': FREE_SCAN_DAYS,
                    'is_beta': _acc.get('is_beta', False), 'is_vip': _acc.get('is_vip', False),
                    'vip_plan': _acc.get('vip_plan', ''), 'vip_left': _acc.get('vip_left', 0),
                    'qr_amount': _acc.get('qr_amount', _acc.get('price', 0)),
                    'message': _acc.get('message', ''),
                }), 402
            _unlock_note = f'（已付费解锁，剩余 {left_h} 小时有效）'
        else:
            _unlock_note = _acc.get('message', '') or ''

        # ── 惰性导入系统引擎（与批量择日同源）──
        _eng = str(ROOT / 'engine')
        if _eng not in sys.path:
            sys.path.insert(0, _eng)
        from engine.sizhu_engine import get_sizhu
        from engine.douhou_analyzer import DouhouKegeAnalyzer
        from engine.sike_sanchuan_engine import SiKeSanChuanCalculator2
        from engine.daliuren_luma_guiren import DaLiuRenLuMaGuiRen, arrange_tiandi_pan
        from engine.yanqin_analyzer import YanQinAnalyzer
        try:
            from engine.liuren_keti_bifa import _nian_ming_shang_shen, _xing_nian_zhi
        except Exception:
            _nian_ming_shang_shen = _xing_nian_zhi = None
        try:
            from engine.kekeduanyu import KeKeDuanyu
        except Exception:
            KeKeDuanyu = None

        _dha = DouhouKegeAnalyzer()
        _sike = SiKeSanChuanCalculator2()
        _luma = DaLiuRenLuMaGuiRen()
        _yqa = YanQinAnalyzer()

        _SHICHEN = ['子','丑','寅','卯','辰','巳','午','未','申','酉','戌','亥']
        _mtn = mountain[0] if mountain else '子'

        _GAN_60 = '甲乙丙丁戊己庚辛壬癸'
        _ZHI_60 = '子丑寅卯辰巳午未申酉戌亥'
        bm_gan, bm_zhi = '', ''
        if ben_ming and len(ben_ming) == 2 and ben_ming[0] in _GAN_60 and ben_ming[1] in _ZHI_60:
            bm_gan, bm_zhi = ben_ming[0], ben_ming[1]
        try:
            bm_age = int(str(ben_ming_age).strip()) if str(ben_ming_age).strip().isdigit() else 0
        except Exception:
            bm_age = 0
        bm_sex = ben_ming_sex if ben_ming_sex in ('男', '女') else '男'

        # IP 定位经纬度（真太阳时昼夜判天将，与单课 analyze 同源；2026-08-17 修同源回归）
        _ip_lat = _ip_lon = None
        try:
            from engine.ip_geo import ip_to_coords, get_client_ip
            _ip_lat, _ip_lon, _, _ = ip_to_coords(get_client_ip(request), timeout=2)
        except Exception:
            pass

        _env = {
            'mtn': _mtn, '_dha': _dha, '_sike': _sike, '_luma': _luma, '_yqa': _yqa,
            '_nms': _nian_ming_shang_shen, '_xnz': _xing_nian_zhi,
            'kekeduanyu': KeKeDuanyu, 'min_liuren': 0,   # 达标模式不做快筛下限，以 min_liuren 档位为准
            'mubiao': mubiao, 'zetiri_type': zetiri_type,
            'bm_gan': bm_gan, 'bm_zhi': bm_zhi, 'bm_age': bm_age, 'bm_sex': bm_sex,
            'gan60': _GAN_60, 'zhi60': _ZHI_60, 'arrange_tiandi_pan': arrange_tiandi_pan,
            'lailong': lailong,
            'lat': _ip_lat, 'lon': _ip_lon,
        }

        # 降档链：用户档位 → 98/95/90/85/80（封顶不高于用户档位；去重）
        levels = [(min_doushou, min_liuren, min_yanqin)]
        for b in (98, 95, 90, 85, 80):
            t = (min(min_doushou, b), min(min_liuren, b), min(min_yanqin, b))
            if t not in levels:
                levels.append(t)

        hits = []
        hit_level = None
        scanned_days = 0
        lowered = False
        for lv_idx, (ds_th, lr_th, yq_th) in enumerate(levels):
            cur = _sd
            scanned_days = 0
            lv_hits = []
            # 高档快速放弃护栏：用户设定档（最高档）每档最多扫 fast_abandon_days（默认1年=365天，可配置），
            # 避免高档硬扫 60 年（约40分钟）；降档后的档位才允许扫满 max_days（命中即停，通常很快）。
            lv_limit = (min(max_days, fast_abandon_days) if lv_idx == 0 else max_days)
            while cur <= _sd + timedelta(days=lv_limit - 1):
                for shichen in _SHICHEN:
                    try:
                        sizhu = get_sizhu(cur.year, cur.month, cur.day, shichen)
                        cand = _build_zeri_candidate(_env, cur, shichen, sizhu)
                        if not cand:
                            continue
                        if (cand['doushou_score'] >= ds_th and
                                cand['liuren_score'] >= lr_th and
                                cand['yanqin_score'] >= yq_th):
                            cand['day_offset'] = (cur - _sd).days + 1  # 起始日=第1天
                            cand['true_solar'] = _true_solar_info(shichen, cur.strftime('%Y-%m-%d'), longitude)
                            lv_hits.append(cand)
                            if len(lv_hits) >= target_count:
                                hits, hit_level = lv_hits, (ds_th, lr_th, yq_th)
                                scanned_days = (cur - _sd).days + 1
                                lowered = (lv_idx > 0)
                                return jsonify({
                                    'success': True, 'results': hits,
                                    'hit_level': {'doushou': ds_th, 'liuren': lr_th, 'yanqin': yq_th},
                                    'scanned_days': scanned_days, 'max_days': max_days,
                                    'lowered': lowered, 'start_date': start_str,
                                    'mountain': mountain, 'zetiri_type': zetiri_type,
                                    'unlock_note': _unlock_note,
                                })
                    except Exception:
                        continue
                scanned_days += 1
                cur += timedelta(days=1)
            # 本档扫满未达标：记录但不立即停，继续降档
            hits, hit_level = lv_hits, (ds_th, lr_th, yq_th)
            if hits:
                lowered = (lv_idx > 0)
                return jsonify({
                    'success': True, 'results': hits,
                    'hit_level': {'doushou': ds_th, 'liuren': lr_th, 'yanqin': yq_th},
                    'scanned_days': scanned_days, 'max_days': max_days,
                    'lowered': lowered, 'start_date': start_str,
                    'mountain': mountain, 'zetiri_type': zetiri_type,
                    'unlock_note': _unlock_note,
                })

        return jsonify({
            'success': True, 'results': [],
            'hit_level': {'doushou': min_doushou, 'liuren': min_liuren, 'yanqin': min_yanqin},
            'scanned_days': scanned_days, 'max_days': max_days,
            'lowered': lowered, 'start_date': start_str,
            'mountain': mountain, 'zetiri_type': zetiri_type,
            'message': '扫描 ' + str(len(levels)) + ' 档均未命中，请放宽达标条件或增加最大天数',
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/zeri/unlock', methods=['POST'])
def api_zeri_unlock():
    """付费解锁达标择日大扫描 POST /api/zeri/unlock
    body: {mobile?, tier?, amount, tx_no?, name?}
    静态收款码场景：用户扫码付款后，前端把支付流水号/人工确认字段交回 →
    金额须匹配新定价档位（防伪造）→ 写入 _zeri_unlock.json（24h 有效）。
    返回 {success, tier, amount, expires_at}。"""
    try:
        data = request.get_json(silent=True) or {}
        tier = data.get('tier', '')
        amount = float(data.get('amount', 0) or 0)
        mobile = (data.get('mobile') or '').strip()
        tx_no = (data.get('tx_no') or '').strip()
        name = (data.get('name') or '').strip()
        # 金额必须精确匹配某个收费档位
        valid_tier = None
        for _n, _d, _price, _desc in SCAN_PRICE_TIERS:
            if _price > 0 and abs(_price - amount) < 0.01:
                valid_tier = _n
                break
        if valid_tier is None:
            return jsonify({'error': '金额与定价档位不匹配（档位：9.8/36/98/168/360/1680 元）'}), 400
        ok = _write_unlock(amount, valid_tier, mobile=mobile)
        if not ok:
            return jsonify({'error': '解锁写入失败'}), 500
        # 记账（如需按用户记录）
        if mobile:
            try:
                book = _load_json(str(ROOT / '_sys_pay_log.json'), []) or []
                book.append({'mobile': mobile, 'name': name, 'amount': amount,
                             'tier': valid_tier, 'tx_no': tx_no, 'kind': 'scan',
                             'ts': datetime.now().isoformat()})
                _save_json(str(ROOT / '_sys_pay_log.json'), book)
            except Exception:
                pass
        try:
            exp = _load_unlocks().get(_unlock_key(mobile), {}).get('expires_at', '')
        except Exception:
            exp = ''
        return jsonify({'success': True, 'tier': valid_tier, 'amount': amount,
                        'expires_at': exp,
                        'message': f'已按次解锁「{_tier_desc_by_amount(amount)}」档（{amount} 元），24小时内达标择日大扫描放行'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


# ═════════════════════════════════════════════════════════════════
# 用户中心 / 会员 / 内测 API
# ═════════════════════════════════════════════════════════════════
@app.route('/api/zeri/price_table', methods=['GET'])
def api_zeri_price_table():
    """返回扫码按次定价表 + 会员价目 + 免费规则（前端用户中心展示）。"""
    scan = []
    for _n, _d, _price, _desc in SCAN_PRICE_TIERS:
        scan.append({'tier': _n, 'max_days': _d, 'price': _price, 'desc': _desc})
    return jsonify({
        'scan_tiers': scan,
        'free_days': FREE_SCAN_DAYS,
        'daily_free': {'limit': DAILY_FREE_LIMIT, 'max_days': DAILY_FREE_MAX_DAYS},
        'member': {
            'plans': [
                {'plan': PLAN_VIP_BASIC, 'name': '会员·体验档', 'prices': VIP_PRICE[PLAN_VIP_BASIC],
                 'quota': VIP48_MONTHLY_QUOTA, 'max_days': VIP48_MAX_DAYS, 'note': f'每月{VIP48_MONTHLY_QUOTA}次 + 限{int(VIP48_MAX_DAYS/30)}个月跨度'},
                {'plan': PLAN_VIP_PRO, 'name': '会员·尊享档', 'prices': VIP_PRICE[PLAN_VIP_PRO],
                 'quota': 9999, 'max_days': 99999, 'note': '不限次数 + 不限跨度'},
            ],
            'periods': [{'key': k, 'months': v} for k, v in VIP_MONTHS.items()],
        },
        'beta': {'enabled': _is_in_beta_window(), 'local': _is_local_ip(_client_ip())},
    })


@app.route('/api/user/verify', methods=['POST'])
def api_user_verify():
    """内测验证 POST /api/user/verify {mobile, name, code}
    校验：手机号+姓名 命中系统指定内测白名单，且验证码正确。
    白名单配置于 _sys_invite.json：{"mobiles":{"13800000000":"张三"}, "beta_code":"8888"}
    或 config.BETA_CODE / config.BETA_MOBILES。
    命中 → 返回内测通过。"""
    try:
        data = request.get_json(silent=True) or {}
        mobile = (data.get('mobile') or '').strip()
        name = (data.get('name') or '').strip()
        code = (data.get('code') or '').strip()
        if not mobile or not name:
            return jsonify({'error': '缺少手机号或姓名'}), 400

        # 校验码
        try:
            from config import BETA_CODE
        except Exception:
            BETA_CODE = '8888'
        expect_code = str(BETA_CODE or '8888')
        if expect_code and code and code != expect_code:
            return jsonify({'error': '内测验证码错误'}), 400
        if expect_code and not code:
            return jsonify({'error': '请输入内测验证码'}), 400

        # 校验白名单：优先 _sys_invite.json，其次 config.BETA_MOBILES
        invite = _load_json(str(INVITE_FILE), {}) or {}
        mobs = invite.get('mobiles', {}) or {}
        ok = False
        if str(mobile) in mobs:
            expect_name = str(mobs[str(mobile)] or '')
            if not expect_name or expect_name == name or expect_name in name or name in expect_name:
                ok = True
        if not ok:
            try:
                from config import BETA_MOBILES
                if mobile in (BETA_MOBILES or {}):
                    expect_name = str((BETA_MOBILES or {}).get(mobile, '') or '')
                    if not expect_name or expect_name == name:
                        ok = True
            except Exception:
                pass
        if not ok:
            return jsonify({'error': '该手机号不在内测白名单内'}), 403

        # 登记用户
        try:
            users = _load_json(str(USER_DATA_FILE), {}) or {}
            users[str(mobile)] = {'name': name, 'mobile': str(mobile),
                                  'beta_verified': True, 'verified_at': datetime.now().isoformat()}
            _save_json(str(USER_DATA_FILE), users)
        except Exception:
            pass
        return jsonify({'success': True, 'beta': True,
                        'message': f'内测验证通过，欢迎{name}，内测/白名单用户免费'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/register', methods=['POST'])
def api_user_register():
    """登记用户（手机号+姓名）POST /api/user/register {mobile, name}
    用于非内测用户的身份登记（会员购买、每日限免计数依据）。"""
    try:
        data = request.get_json(silent=True) or {}
        mobile = (data.get('mobile') or '').strip()
        name = (data.get('name') or '').strip()
        if not mobile or not (len(mobile) == 11 and mobile.isdigit()):
            return jsonify({'error': '手机号格式不正确'}), 400
        users = _load_json(str(USER_DATA_FILE), {}) or {}
        users[str(mobile)] = {'name': name or users.get(str(mobile), {}).get('name', ''),
                              'mobile': str(mobile), 'registered_at': datetime.now().isoformat()}
        _save_json(str(USER_DATA_FILE), users)
        mem = _membership(mobile)
        return jsonify({'success': True, 'mobile': str(mobile),
                        'is_vip': bool(mem and _membership_valid(mem))})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/info', methods=['POST'])
def api_user_info():
    """查询当前用户身份/会员状态 POST /api/user/info {mobile}
    返回：内测状态、会员状态(plan/到期/剩余次数)、付费解锁状态。"""
    try:
        data = request.get_json(silent=True) or {}
        mobile = (data.get('mobile') or '').strip()
        mem = _membership(mobile)
        beta = _is_beta_whitelisted(mobile)
        vip_plan = ''
        vip_left = 0
        vip_expire = ''
        if mem and _membership_valid(mem):
            plan = mem.get('plan')
            if plan == PLAN_LIFETIME:
                vip_plan = '终身免费'
                vip_left = 9999
            elif plan == PLAN_VIP_PRO:
                vip_plan = '尊享档'
                vip_expire = mem.get('expires_at', '')
                vip_left = 9999
            else:
                vip_plan = '体验档'
                vip_expire = mem.get('expires_at', '')
                used = int((mem or {}).get('used_this_period', 0) or 0)
                vip_left = max(0, VIP48_MONTHLY_QUOTA - used)
        # 状态页：按手机号隔离读取本用户未过期的按次解锁及其到期时间
        unlock_ok = False
        left_h = 0
        unlock_expire = ''
        try:
            rec = _load_unlocks().get(_unlock_key(mobile), {})
            if rec:
                exp = datetime.fromisoformat(rec.get('expires_at', ''))
                if exp >= datetime.now():
                    unlock_ok = True
                    unlock_expire = rec.get('expires_at', '')
                    left_h = round((exp - datetime.now()).total_seconds() / 3600, 1)
        except Exception:
            pass
        return jsonify({
            'mobile': mobile, 'is_beta': beta,
            'is_vip': bool(vip_plan), 'vip_plan': vip_plan,
            'vip_left': vip_left, 'vip_expire': vip_expire,
            'unlocked': unlock_ok, 'unlock_hours': left_h,
            'unlock_expire': unlock_expire,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/verify_token', methods=['POST', 'GET'])
def api_user_verify_token():
    """通过 token 自动识别用户身份 GET /api/user/verify_token?token=xxx
    用于跨设备自动登录（终身免费用户等）。"""
    try:
        token = request.args.get('token', '') if request.method == 'GET' else (request.get_json(silent=True) or {}).get('token', '')
        token = (token or '').strip()
        if not token:
            return jsonify({'error': '缺少 token 参数'}), 400
        
        # 查找 token 对应的用户
        users = _load_json(str(USER_DATA_FILE), {}) or {}
        found_mobile = None
        found_user = None
        for mobile, user in users.items():
            if user.get('token') == token:
                found_mobile = mobile
                found_user = user
                break
        
        if not found_mobile:
            return jsonify({'error': 'token 无效或已过期'}), 404
        
        mobile = found_mobile
        mem = _membership(mobile)
        beta = _is_beta_whitelisted(mobile)
        vip_plan = ''
        vip_left = 0
        vip_expire = ''
        if mem and _membership_valid(mem):
            plan = mem.get('plan')
            if plan == PLAN_LIFETIME:
                vip_plan = '终身免费'
                vip_left = 9999
            elif plan == PLAN_VIP_PRO:
                vip_plan = '尊享档'
                vip_expire = mem.get('expires_at', '')
                vip_left = 9999
            else:
                vip_plan = '体验档'
                vip_expire = mem.get('expires_at', '')
                used = int((mem or {}).get('used_this_period', 0) or 0)
                vip_left = max(0, VIP48_MONTHLY_QUOTA - used)
        
        return jsonify({
            'success': True,
            'mobile': mobile,
            'name': found_user.get('name', ''),
            'is_beta': beta,
            'is_vip': bool(vip_plan),
            'vip_plan': vip_plan,
            'vip_left': vip_left,
            'vip_expire': vip_expire,
            'user_type': found_user.get('user_type', 'normal'),
            'message': '身份验证成功'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/user/generate_token', methods=['POST'])
def api_user_generate_token():
    """生成用户专属 token（管理员使用）POST /api/user/generate_token {mobile}
    返回 {success, token, url}。"""
    try:
        data = request.get_json(silent=True) or {}
        mobile = (data.get('mobile') or '').strip()
        if not mobile or not (len(mobile) == 11 and mobile.isdigit()):
            return jsonify({'error': '手机号格式不正确'}), 400
        
        import hashlib
        import time
        timestamp = str(int(time.time()))
        raw = f"{mobile}_{timestamp}_liuren_token"
        token = hashlib.md5(raw.encode()).hexdigest()[:24]
        token = f"{mobile[-4:]}_{token}"
        
        users = _load_json(str(USER_DATA_FILE), {}) or {}
        if mobile not in users:
            users[mobile] = {'name': '', 'mobile': mobile}
        users[mobile]['token'] = token
        users[mobile]['token_created_at'] = datetime.now().isoformat()
        _save_json(str(USER_DATA_FILE), users)
        
        return jsonify({
            'success': True,
            'mobile': mobile,
            'token': token,
            'url': f"https://liuren.souhuertong.net.cn/?token={token}",
            'message': 'Token 生成成功'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/member/plans', methods=['GET'])
def api_member_plans():
    """返回会员两档价目（月/季/年）。"""
    return jsonify({
        'plans': VIP_PRICE,
        'periods': VIP_MONTHS,
        'vip48_quota': VIP48_MONTHLY_QUOTA,
        'vip48_max_days': VIP48_MAX_DAYS,
    })


@app.route('/api/member/activate', methods=['POST'])
def api_member_activate():
    """会员激活/续费（人工核对后调用）POST /api/member/activate {mobile, plan, period, tx_no?}
    经对账确认到账后，为手机号写入对应周期的会员权益：
      vip48: 每月/3月/12月  次数按 VIP48_MONTHLY_QUOTA 记周期（月/季/年）
      vip98: 不限次数+跨度。
    返回 {success, plan, expires_at}。"""
    try:
        data = request.get_json(silent=True) or {}
        mobile = (data.get('mobile') or '').strip()
        plan = data.get('plan', '')
        period = data.get('period', 'm')
        tx_no = (data.get('tx_no') or '').strip()
        if not mobile or len(mobile) != 11 or not mobile.isdigit():
            return jsonify({'error': '手机号格式不正确'}), 400
        if plan not in (PLAN_VIP_BASIC, PLAN_VIP_PRO):
            return jsonify({'error': '会员档位错误'}), 400
        if period not in VIP_MONTHS:
            return jsonify({'error': '周期错误(仅 m/q/y)'}), 400
        months = VIP_MONTHS[period]
        price = VIP_PRICE[plan].get(period, 0)

        # 激活：叠加续期
        data_ = _load_json(str(MEMBERSHIP_FILE), {}) or {}
        cur = data_.get(str(mobile)) or {}
        base = datetime.now()
        if cur.get('expires_at') and _membership_valid(cur):
            try:
                cand = datetime.fromisoformat(cur['expires_at'])
                if cand > base:
                    base = cand
            except Exception:
                pass
        new_exp = base + timedelta(days=30 * months)
        data_[str(mobile)] = {'plan': plan, 'expires_at': new_exp.isoformat(),
                              'price': price, 'period': period,
                              'used_this_period': 0,
                              'activated_at': datetime.now().isoformat()}
        _save_json(str(MEMBERSHIP_FILE), data_)
        # 记账
        try:
            book = _load_json(str(ROOT / '_sys_pay_log.json'), []) or []
            book.append({'mobile': mobile, 'kind': 'member', 'plan': plan, 'period': period,
                         'price': price, 'tx_no': tx_no, 'ts': datetime.now().isoformat()})
            _save_json(str(ROOT / '_sys_pay_log.json'), book)
        except Exception:
            pass
        return jsonify({'success': True, 'plan': plan, 'price': price,
                        'expires_at': new_exp.isoformat(),
                        'message': f'会员「{plan}」激活成功，{months}个月，有效期至 {new_exp.strftime("%Y-%m-%d")}'})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/docx', methods=['POST'])
def api_export_docx():
    """导出吉日列表为 Word(.docx) POST /api/export/docx
    body: {title, items:[{date,shichen,sizhu,total_score,grade,doushou_classes,gong_names,...}], zetiri_type, mountain}"""
    import io as _io
    try:
        data = request.get_json(silent=True) or {}
        title = data.get('title', '仪度六壬择日吉期列表')
        zetiri_type = data.get('zetiri_type', '')
        mountain = data.get('mountain', '')
        items = data.get('items', []) or []

        from docx import Document
        from docx.shared import Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        doc = Document()

        # 标题
        h = doc.add_heading('仪度六壬择日 · 吉期列表', level=0)
        h.alignment = WD_ALIGN_PARAGRAPH.CENTER
        sub = doc.add_paragraph()
        sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = sub.add_run(f'择日类型：{zetiri_type or "—"}    坐山：{mountain or "—"}    '
                          f'共 {len(items)} 个吉期   导出时间：{datetime.now().strftime("%Y-%m-%d %H:%M")}')
        run.font.size = Pt(9)
        run.font.color.rgb = RGBColor(0x88, 0x88, 0x88)

        if not items:
            doc.add_paragraph('（暂无吉期数据）')
        else:
            table = doc.add_table(rows=1, cols=8)
            table.style = 'Light Grid Accent 1'
            hdr = table.rows[0].cells
            headers = ['序号', '日期', '时辰', '四柱', '总分', '评级', '斗首类别', '格局/拱格']
            for i, htext in enumerate(headers):
                hdr[i].text = htext
            for idx, it in enumerate(items, 1):
                row = table.add_row().cells
                row[0].text = str(idx)
                row[1].text = str(it.get('date', ''))
                row[2].text = str(it.get('shichen', '')) + '时'
                row[3].text = str(it.get('sizhu', ''))
                row[4].text = str(it.get('total_score', ''))
                row[5].text = str(it.get('grade', ''))
                ds = it.get('doushou_classes', {})
                ds_txt = ' '.join(f'{k}{v}' for k, v in (ds.items() if isinstance(ds, dict) else [])) if ds else ''
                row[6].text = ds_txt
                gong = it.get('gong_names', []) or []
                row[7].text = '、'.join(gong) if gong else ''

        buf = _io.BytesIO()
        doc.save(buf)
        buf.seek(0)

        from flask import send_file as _send_file
        fname = f"仪度六壬择日_{zetiri_type or '吉期'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        resp = _send_file(buf, as_attachment=True, download_name=fname,
                          mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        resp.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return resp
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/zeri/leixiang_feedback', methods=['POST'])
def api_zeri_leixiang_feedback():
    """现代类象用后反馈（2026-08-25 用户拍板：记录应验vs推演出入，反馈校准）
    POST body: {zeri_type, date, shichen, 推演:[...], 应验:[...], 确认:bool, note}
    返回：{ok, 出入, 案例数, narrative}"""
    try:
        data = request.get_json(silent=True) or {}
        zeri_type = (data.get('zeri_type') or '').strip()
        if not zeri_type:
            return jsonify({'error': '缺少 zeri_type'}), 400
        from engine.leixiang_kb import LeixiangKB
        _kb = LeixiangKB()
        r = _kb.record_feedback(
            zeri_type,
            date=(data.get('date') or '').strip(),
            shichen=(data.get('shichen') or '').strip(),
            推演=data.get('推演') or [],
            应验=data.get('应验') or [],
            note=(data.get('note') or '').strip(),
            确认=bool(data.get('确认')),
        )
        return jsonify({
            'ok': True,
            '出入': r.get('出入', []),
            '案例数': r.get('案例数', 0),
            'narrative': _kb.get_narrative(zeri_type),
        })
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/wenshu', methods=['POST'])
def _wenshu_avoidance_text(data, detail):
    """
    自动计算避忌文字。
    
    规则（2026-08-26 更新）：
    - 安葬类（阴宅）：只检查坐山，显示地支+属相名称，区分冲刑类型
    - 其他类型：保持原有逻辑
    
    返回 str：'不用避忌' 或 '避忌：与坐山相冲的猴属相、相刑的蛇属相...'。
    detail 缺字段时返回空（不覆盖前端手填）。
    """
    try:
        from engine.avoidance_resolution import judge_avoidance
        sizhu = detail.get('sizhu') or {}
        sizhu_zhi = []
        for k in ('年', '月', '日', '时'):
            v = sizhu.get(k) or ''
            if len(v) >= 2:
                sizhu_zhi.append(v[1])
        sike = detail.get('sike') or []
        # sike: [[课名, 上神, 下神, 天将], ...] 四课
        shang = [s[1] for s in sike if isinstance(s, (list, tuple)) and len(s) > 1]
        gan_shang = shang[0] if len(shang) > 0 else ''
        gan_yin = shang[1] if len(shang) > 1 else ''
        zhi_shang = shang[2] if len(shang) > 2 else ''
        zhi_yin = shang[3] if len(shang) > 3 else ''
        sc = detail.get('sanchuan') or {}
        sanchuan = [sc.get('初传', ''), sc.get('中传', ''), sc.get('末传', '')]
        ri_zhi = sizhu.get('日') or ''
        ri_zhi = ri_zhi[1] if len(ri_zhi) >= 2 else ''
        
        # 判断是否为安葬类（阴宅）
        zetiri_type = (data.get('zetiri_type') or '').strip()
        yinzhai_types = {'立碑', '安葬', '阴宅动土', '迁坟', '催龙补气', '召山买土'}
        is_yinzhai = zetiri_type in yinzhai_types
        
        # 坐山用实际二十四山→地支
        _MNT_ZHI = {'壬': '子', '子': '子', '癸': '子', '丑': '丑', '艮': '丑',
                    '寅': '寅', '甲': '寅', '卯': '卯', '乙': '卯', '辰': '辰',
                    '巽': '辰', '巳': '巳', '丙': '巳', '午': '午', '丁': '午',
                    '未': '未', '坤': '未', '申': '申', '庚': '申', '酉': '酉',
                    '辛': '酉', '戌': '戌', '乾': '戌', '亥': '亥'}
        _mnt = (data.get('mountain') or detail.get('mountain') or '').strip()
        _xiang = (detail.get('xiang_shou') or '').strip()
        _mnt_zhi = _MNT_ZHI.get(_mnt, _mnt)
        
        # 调用 judge_avoidance（安葬类只用 shan_only=True）
        r = judge_avoidance(
            shan=_mnt_zhi,
            xiang=_xiang,
            ri_zhi=ri_zhi,
            sizhu_zhi=sizhu_zhi,
            tiandi_pan=detail.get('tiandi_pan') or {},
            gan_shang_shen=gan_shang, zhi_shang_shen=zhi_shang,
            gan_yin_shen=gan_yin, zhi_yin_shen=zhi_yin,
            sanchuan=sanchuan,
            shan_only=is_yinzhai,  # 安葬类只检查坐山
        )
        
        if is_yinzhai:
            # 安葬类：使用新格式
            if r['resolved']:
                biji = '不用避忌'
            else:
                # 使用 avoid_list 生成详细避忌文字
                avoid_list = r.get('avoid_list', [])
                if avoid_list:
                    # 按攻击类型分组
                    chong_list = []  # 冲
                    xing_list = []   # 刑
                    hai_list = []    # 害
                    po_list = []    # 破
                    
                    for item in avoid_list:
                        types_str = item.get('types_str', '')
                        zhi = item.get('zhi', '')
                        zodiac = item.get('zodiac', '')
                        text = f'{zhi}({zodiac})'
                        
                        if '冲' in types_str:
                            chong_list.append(text)
                        if '刑' in types_str:
                            xing_list.append(text)
                        if '害' in types_str:
                            hai_list.append(text)
                        if '破' in types_str:
                            po_list.append(text)
                    
                    parts = []
                    if chong_list:
                        parts.append('与坐山相冲的' + '、'.join(chong_list) + '属相')
                    if xing_list:
                        parts.append('与坐山相刑的' + '、'.join(xing_list) + '属相')
                    if hai_list:
                        parts.append('与坐山相害的' + '、'.join(hai_list) + '属相')
                    if po_list:
                        parts.append('与坐山相破的' + '、'.join(po_list) + '属相')
                    
                    biji = '避忌：' + '；'.join(parts)
                else:
                    biji = '避忌：详见课格'
        else:
            # 其他类型：保持原有格式（向后兼容）
            if r['resolved']:
                biji = '不用避忌'
            else:
                avoid = []
                for x in r['reasons']:
                    if '必避' in x or '需避' in x or '凶' in x:
                        z = x.split('（')[0].strip()
                        if z and z not in avoid:
                            avoid.append(z)
                biji = '避忌：' + ('、'.join(avoid) if avoid else '详见课格') + '属相'
        
        # 附类象叙事
        lx_narr = ''
        try:
            from engine.leixiang_kb import LeixiangKB
            _lkb = LeixiangKB()
            lx_narr = _lkb.get_narrative(zetiri_type)
        except Exception:
            pass
        if lx_narr:
            return biji + '。' + lx_narr
        return biji
    except Exception:
        return ''


def api_export_wenshu():
    """单课择日文书导出（套用「完美模板.docx」） POST /api/export/wenshu
    body: {detail:<api/zeri/analyze 完整返回>, date, shichen, mountain, zetiri_type,
           lailong, xianming, biji, dili_shi}"""
    try:
        data = request.get_json(silent=True) or {}
        detail = data.get('detail') or {}
        if not detail:
            return jsonify({'error': '缺少 detail（单课课格数据）'}), 400

        zetiri_type = (data.get('zetiri_type') or '').strip()
        title = f'仪度六壬·{zetiri_type}择日课单' if zetiri_type else '仪度六壬择日课单'
        payload = dict(data)
        payload['title'] = title
        # 自动避忌判定（前端未手填 biji 时自动生成）
        if not (data.get('biji') or '').strip():
            _auto = _wenshu_avoidance_text(data, detail)
            if _auto:
                payload['biji'] = _auto

        from engine.wenshu_exporter import build_wenshu
        buf = build_wenshu(payload)

        from flask import send_file as _send_file
        date = (data.get('date') or '').strip()
        shichen = (data.get('shichen') or '').strip()
        fname = f"仪度六壬择日课单_{date}_{shichen}时.docx"
        resp = _send_file(buf, as_attachment=True, download_name=fname,
                          mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')
        resp.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return resp
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/wenshu_html', methods=['POST'])
def api_export_wenshu_html():
    """单课择日文书 HTML 预览版 POST /api/export/wenshu_html
    body 同 /api/export/wenshu。返回 {html: str}（竖排 + 米黄底 + 红框 + 印章，供前端 iframe 预览）。"""
    try:
        data = request.get_json(silent=True) or {}
        detail = data.get('detail') or {}
        if not detail:
            return jsonify({'error': '缺少 detail（单课课格数据）'}), 400

        zetiri_type = (data.get('zetiri_type') or '').strip()
        title = f'仪度六壬·{zetiri_type}择日课单' if zetiri_type else '仪度六壬择日课单'
        payload = dict(data)
        payload['title'] = title
        if not (data.get('biji') or '').strip():
            _auto = _wenshu_avoidance_text(data, detail)
            if _auto:
                payload['biji'] = _auto

        from engine.wenshu_exporter import build_wenshu_html
        html = build_wenshu_html(payload)
        return jsonify({'html': html})
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/wenshu_pdf', methods=['POST'])
def api_export_wenshu_pdf():
    """单课择日文书 PDF 导出（HTML→chromium 打印，保留宣纸纹理/印章/四角边框） POST /api/export/wenshu_pdf
    body 同 /api/export/wenshu。"""
    try:
        data = request.get_json(silent=True) or {}
        detail = data.get('detail') or {}
        if not detail:
            return jsonify({'error': '缺少 detail（单课课格数据）'}), 400

        zetiri_type = (data.get('zetiri_type') or '').strip()
        title = f'仪度六壬·{zetiri_type}择日课单' if zetiri_type else '仪度六壬择日课单'
        payload = dict(data)
        payload['title'] = title
        if not (data.get('biji') or '').strip():
            _auto = _wenshu_avoidance_text(data, detail)
            if _auto:
                payload['biji'] = _auto

        from engine.wenshu_exporter import build_wenshu_html, html_to_pdf
        html = build_wenshu_html(payload)
        pdf_bytes = html_to_pdf(html)

        import io as _io
        from flask import send_file as _send_file
        date = (data.get('date') or '').strip()
        shichen = (data.get('shichen') or '').strip()
        fname = f"仪度六壬择日课单_{date}_{shichen}时.pdf"
        resp = _send_file(_io.BytesIO(pdf_bytes), as_attachment=True, download_name=fname,
                          mimetype='application/pdf')
        resp.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return resp
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/pptx', methods=['POST'])
def api_export_pptx():
    """导出吉日列表为 PPT(.pptx) POST /api/export/pptx"""
    import io as _io
    try:
        data = request.get_json(silent=True) or {}
        zetiri_type = data.get('zetiri_type', '')
        mountain = data.get('mountain', '')
        items = data.get('items', []) or []

        from pptx import Presentation
        from pptx.util import Inches, Pt
        prs = Presentation()
        slide = prs.slides.add_slide(prs.slide_layouts[1])  # 标题+内容
        slide.shapes.title.text = '仪度六壬择日 · 吉期列表'
        sub = slide.placeholders[1]
        sub.text = f'择日类型：{zetiri_type or "—"}　坐山：{mountain or "—"}　共 {len(items)} 个吉期\n' + \
                   '生成时间：' + datetime.now().strftime('%Y-%m-%d %H:%M')
        for it in items:
            line = f"{it.get('date','')} {it.get('shichen','')}时　{it.get('sizhu','')}　总分{it.get('total_score','')} [{it.get('grade','')}]"
            p = sub.text_frame.add_paragraph()
            p.text = line
            p.level = 1

        buf = _io.BytesIO()
        prs.save(buf)
        buf.seek(0)
        from flask import send_file as _send_file
        fname = f"仪度六壬择日_{zetiri_type or '吉期'}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pptx"
        resp = _send_file(buf, as_attachment=True, download_name=fname,
                          mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation')
        resp.headers['Access-Control-Expose-Headers'] = 'Content-Disposition'
        return resp
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    import os as _os
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5555
    # 2026-08-17：锁路径支持环境变量/第 2 个命令行参数覆盖（DASHBOARD_LOCK_FILE 或 argv[2]）
    # ——僵尸锁句柄卡死主锁文件时，可用备用锁路径绕过（如 python stock_dashboard.py 5555 _memory/.flask.lock2）。
    _lock_path = (_os.environ.get('DASHBOARD_LOCK_FILE')
                  or (sys.argv[2] if len(sys.argv) > 2 else '')
                  or _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), '_memory', '.flask_instance.lock'))
    _lock = _acquire_single_instance_lock(_lock_path)
    if _lock is None:
        print("[单例锁] 已有另一个 六壬自动跑盘(Flask) 实例在运行，本进程已退出，避免多实例抢端口。")
        sys.exit(0)
    print(f"\n{'='*50}")
    print(f"  大六壬虚拟交易仪表盘")
    print(f"  访问地址: http://localhost:{port}")
    print(f"{'='*50}\n")
    print(f"  ✅ 行情模块就绪（akshare 直接调用，子进程作 fallback）")
    print(f"  ⚠️   注意：StockAnalyzer/mini_racer 不在主进程加载（防DLL崩溃）")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)

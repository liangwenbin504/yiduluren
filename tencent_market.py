#!/usr/bin/env python3
"""
腾讯行情共享模块 — 统一替代东方财富接口
=========================================
选股器 / 持仓模块共用的行情源。本环境东方财富(em)接口被远端掐断，
统一改用腾讯源：
  - 实时行情:  http://qt.gtimg.cn/q={prefix}{code}
  - 日K线:     http://web.ifzq.gtimg.cn/appstock/app/fqkline/get
  - 指数日K线: 同上 (param=sh000001,...)

字段约定 (gtimg 实时行情 ~ 分隔):
  f[1]  = 名称
  f[3]  = 当前价
  f[39] = 市盈率(静) PE
  f[46] = 市净率 PB

K线返回格式: [日期, 开盘, 收盘, 最高, 最低, 成交量]
"""

import requests

_TIMEOUT = 8
_RETRIES = 2


def tx_prefix(code: str) -> str:
    """股票代码转腾讯前缀: 6开头->sh, 0/3开头->sz"""
    code = str(code).strip()
    if code.startswith('6'):
        return 'sh' + code
    elif code.startswith(('0', '3')):
        return 'sz' + code
    return 'sh' + code  # 默认


def _get(url: str) -> requests.Response:
    """带重试 + 绕过代理的请求（防代理环境下挂起）"""
    last_err = None
    for _ in range(_RETRIES):
        try:
            r = requests.get(url, timeout=_TIMEOUT, proxies=None)
            if r.status_code == 200:
                return r
        except Exception as e:
            last_err = e
    if last_err:
        raise last_err
    raise RuntimeError(f"HTTP {r.status_code} for {url}")


def tencent_quote(code: str) -> dict:
    """
    获取个股实时行情。
    返回 dict: {name, price, pre_close, open, high, low, change, pe, pb}
    取不到时返回 None。
    字段: f[1]名称 f[3]现价 f[4]昨收 f[5]今开 f[32]涨跌% f[33]最高 f[34]最低
          f[39]市盈率 f[46]市净率
    """
    try:
        prefix = tx_prefix(code)
        r = _get(f'http://qt.gtimg.cn/q={prefix}')
        txt = r.text.strip()
        if '"' not in txt:
            return None
        f = txt.split('"', 2)[1].split('~')
        if len(f) < 47:
            return None
        name = ''.join(f[1].split())  # 去除腾讯返回的名称中可能带的内部空格
        if not name or name == 'nan':
            return None

        def _num(i):
            try:
                v = f[i]
                return float(v) if v not in ('', '-', '0.00') else 0.0
            except (ValueError, IndexError):
                return 0.0

        return {
            'name': name,
            'price': _num(3),
            'pre_close': _num(4),
            'open': _num(5),
            'change': _num(32),
            'high': _num(33),
            'low': _num(34),
            'pe': _num(39) or None,
            'pb': _num(46) or None,
        }
    except Exception as e:
        print(f"  [腾讯行情] {code} 实时获取失败: {e}")
        return None


def tencent_hist(code: str, days: int = 60) -> list:
    """
    获取个股日K线收盘价序列（前复权），按时间正序。
    返回 list[float]，长度可能 < days（数据不足时）。
    无数据时返回空列表。
    """
    try:
        prefix = tx_prefix(code)
        import datetime as _dt
        end = _dt.date.today().strftime('%Y-%m-%d')
        start = (_dt.date.today() - _dt.timedelta(days=days * 2 + 30)).strftime('%Y-%m-%d')
        url = (f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
               f'?param={prefix},day,{start},{end},{days * 2},qfq')
        r = _get(url)
        d = r.json()
        node = d.get('data', {}).get(prefix)
        if not node:
            return []
        klines = node.get('qfqday') or node.get('day')
        if not klines:
            return []
        closes = []
        for k in klines:
            # [日期, 开, 收, 高, 低, 量]
            try:
                closes.append(float(k[2]))
            except (ValueError, IndexError):
                continue
        return closes[-days:] if days else closes
    except Exception as e:
        print(f"  [腾讯行情] {code} 日K线获取失败: {e}")
        return []


def tencent_index_daily(code: str = 'sh000001', days: int = 400) -> list:
    """
    获取指数日K线收盘价序列（如 sh000001 上证指数）。
    返回 list[float] 正序，无数据返回空列表。
    """
    try:
        url = (f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
               f'?param={code},day,,,{days},qfq')
        r = _get(url)
        d = r.json()
        node = d.get('data', {}).get(code)
        if not node:
            return []
        klines = node.get('qfqday') or node.get('day')
        if not klines:
            return []
        closes = []
        for k in klines:
            try:
                closes.append(float(k[2]))
            except (ValueError, IndexError):
                continue
        return closes
    except Exception as e:
        print(f"  [腾讯行情] 指数 {code} 日K线获取失败: {e}")
        return []


def tencent_close_on(code, target_date) -> float:
    """
    获取指定交易日(today或历史)的收盘价（腾讯日K线，准确）。
    target_date: date 对象或 'YYYY-MM-DD' 字符串。
    找不到返回 None。
    """
    import datetime as _dt
    try:
        if isinstance(target_date, _dt.date):
            td = target_date
        else:
            td = _dt.datetime.strptime(str(target_date), '%Y-%m-%d').date()
        prefix = tx_prefix(code)
        end = td.strftime('%Y-%m-%d')
        start = (td - _dt.timedelta(days=45)).strftime('%Y-%m-%d')
        url = (f'http://web.ifzq.gtimg.cn/appstock/app/fqkline/get'
               f'?param={prefix},day,{start},{end},60,qfq')
        r = _get(url)
        d = r.json()
        node = d.get('data', {}).get(prefix)
        if not node:
            return None
        klines = node.get('qfqday') or node.get('day')
        if not klines:
            return None
        best = None
        for k in klines:
            try:
                cd = _dt.datetime.strptime(k[0], '%Y-%m-%d').date()
            except (ValueError, IndexError):
                continue
            if cd <= td:
                best = float(k[2])  # 收盘
        return best
    except Exception as e:
        print(f"  [腾讯行情] {code} {target_date} 历史收盘获取失败: {e}")
        return None


if __name__ == '__main__':
    print('quote 600519:', tencent_quote('600519'))
    print('hist 600519 len:', len(tencent_hist('600519', 60)))
    print('index len:', len(tencent_index_daily('sh000001', 400)))

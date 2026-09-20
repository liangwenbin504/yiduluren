#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
每日通知推送模块
===============
支持 PushPlus(微信) + SMTP邮件 双通道

配置（任选其一即可）:
  1. PushPlus (推荐，免费): 在 https://www.pushplus.plus 注册获取token
     设置环境变量: PUSHPLUS_TOKEN=你的token
  2. SMTP邮件: 设置环境变量:
     SMTP_HOST=smtp.qq.com
     SMTP_USER=你的邮箱
     SMTP_PASS=授权码
     NOTIFY_EMAIL=接收邮箱

用法:
  from notify import send_daily_report
  send_daily_report()  # 发送今日摘要到微信/邮件
"""

import json, os, sys, requests
from datetime import datetime, date, timedelta, timezone

BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(BASE, '_memory')

# ── 配置 ──
PUSHPLUS_TOKEN = os.environ.get("PUSHPLUS_TOKEN", "")
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
NOTIFY_EMAIL = os.environ.get("NOTIFY_EMAIL", "")

HAS_PUSHPLUS = bool(PUSHPLUS_TOKEN)
HAS_EMAIL = bool(SMTP_HOST and SMTP_USER and SMTP_PASS and NOTIFY_EMAIL)


def _get_today_stats() -> dict:
    """获取今日预测统计"""
    preds = []
    pred_file = os.path.join(MEMORY, 'stock_predictions.json')
    if os.path.exists(pred_file):
        with open(pred_file, 'r', encoding='utf-8') as f:
            preds = json.load(f)

    today = date.today().isoformat()
    today_preds = [p for p in preds if p.get('date') == today and p.get('status') == 'completed']

    correct = [p for p in today_preds if p.get('trend_prediction') == p.get('actual_result')]
    acc = len(correct) / max(len(today_preds), 1) * 100

    # 累计
    all_done = [p for p in preds if p.get('status') == 'completed']
    all_correct = [p for p in all_done if p.get('trend_prediction') == p.get('actual_result')]
    total_acc = len(all_correct) / max(len(all_done), 1) * 100

    # 市场数据
    market_info = ""
    try:
        import akshare as ak
        df = ak.stock_zh_index_daily(symbol='sh000001')
        row = df[df['date'].astype(str) == today]
        if not row.empty:
            r = row.iloc[-1]
            chg = (r['close'] - r['open']) / r['open'] * 100
            market_info = f"上证 {r['close']:.0f} ({chg:+.2f}%) 开{r['open']:.0f} 高{r['high']:.0f} 低{r['low']:.0f}"
    except:
        pass

    trends = {}
    categories = []
    cat_labels = {
        'fixed_time':'固定时辰','ri_gan_pian_cai':'日干偏财','ri_zhi_pian_cai':'日支偏财',
        'ri_gan_shi_shen':'日干食神','ri_zhi_shi_shen':'日支食神',
        'ri_gan_zheng_yin':'日干正印','ri_gan_pian_yin':'日干偏印',
        'ri_zhi_zheng_yin':'日支正印','ri_zhi_pian_yin':'日支偏印',
        'random':'随机','manual':'人工指定','ml_predict':'ML预测',
    }
    for p in today_preds:
        t = p.get('trend_prediction', '?')
        trends[t] = trends.get(t, 0) + 1
        cat = p.get('category', '?')
        actual = p.get('actual_result', '?')
        hit = '✅' if t == actual else ('❌' if actual != '?' else '⏳')
        categories.append({
            'name': cat_labels.get(cat, cat),
            'pred': t,
            'actual': actual,
            'hit': hit,
            'confidence': p.get('confidence', ''),
        })

    return {
        'date': today,
        'total': len(today_preds),
        'correct': len(correct),
        'accuracy': round(acc, 1),
        'total_accuracy': round(total_acc, 1),
        'total_samples': len(all_done),
        'market': market_info,
        'trends': trends,
        'categories': categories,
        'consensus': max(trends, key=trends.get) if trends else '无数据',
    }


def build_message(stats: dict) -> tuple:
    """构建推送消息 (title, content)"""
    emoji = "🟢" if stats['accuracy'] >= 60 else ("🟡" if stats['accuracy'] >= 40 else "🔴")
    title = f"{emoji} 六壬预测日报 {stats['date']} | {stats['correct']}/{stats['total']}"

    lines = [
        f"## 📊 {stats['date']} 股票预测日报",
        f"",
    ]
    if stats['market']:
        lines.append(f"**{stats['market']}**")

    # 逐类预测对照表
    cats = stats.get('categories', [])
    ml_cats = [c for c in cats if c['name'] == 'ML预测']
    lr_cats = [c for c in cats if c['name'] != 'ML预测']

    if lr_cats:
        lines.append("")
        lines.append("| 类别 | 预测 | 实际 | |")
        lines.append("|------|------|------|---|")
        for c in lr_cats:
            conf = f" ({c['confidence']:.0%})" if isinstance(c.get('confidence'), float) and c['confidence'] else ""
            lines.append(f"| {c['name']} | {c['pred']}{conf} | {c['actual']} | {c['hit']} |")

    if ml_cats:
        c = ml_cats[0]
        lines.append(f"| **ML** | **{c['pred']}** | **{c['actual']}** | **{c['hit']}** |")

    lines.append("")
    lines.append(f"**共识**: {stats['consensus']}  |  **今日**: {stats['correct']}/{stats['total']}  |  **累计**: {stats['total_accuracy']}%({stats['total_samples']}样本)")

    content = "\n".join(lines)
    return title, content


def send_pushplus(title: str, content: str) -> bool:
    """通过 PushPlus 推送到微信"""
    if not PUSHPLUS_TOKEN:
        return False
    try:
        url = "https://www.pushplus.plus/send"
        data = {
            "token": PUSHPLUS_TOKEN,
            "title": title,
            "content": content,
            "template": "markdown",
        }
        resp = requests.post(url, json=data, timeout=15)
        result = resp.json()
        return result.get('code') == 200
    except Exception as e:
        print(f"[PushPlus] 发送失败: {e}")
        return False


def send_email(title: str, content: str) -> bool:
    """通过 SMTP 发送邮件"""
    if not HAS_EMAIL:
        return False
    try:
        import smtplib
        from email.mime.text import MIMEText

        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = title
        msg['From'] = SMTP_USER
        msg['To'] = NOTIFY_EMAIL

        if 'qq.com' in SMTP_HOST:
            server = smtplib.SMTP_SSL(SMTP_HOST, 465)
        else:
            server = smtplib.SMTP(SMTP_HOST, 587)
            server.starttls()
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, [NOTIFY_EMAIL], msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"[Email] 发送失败: {e}")
        return False


def send_daily_report() -> str:
    """发送每日报告，返回结果描述"""
    stats = _get_today_stats()
    if stats['total'] == 0:
        return "无今日数据，跳过推送"

    title, content = build_message(stats)
    results = []

    if HAS_PUSHPLUS:
        ok = send_pushplus(title, content)
        results.append("微信" if ok else "微信失败")

    if HAS_EMAIL:
        ok = send_email(title, content)
        results.append("邮件" if ok else "邮件失败")

    if not results:
        # 降级：保存到本地文件
        report_path = os.path.join(MEMORY, f'daily_report_{stats["date"]}.md')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(f"# {title}\n\n{content}")
        return f"无推送渠道，已保存本地: {report_path}"

    return " + ".join(results) + " 推送完成"


# ── 命令行 ──

if __name__ == "__main__":
    print("=" * 50)
    print("  每日通知推送")
    print(f"  PushPlus: {'✅已配置' if HAS_PUSHPLUS else '❌未配置(设置PUSHPLUS_TOKEN)'}")
    print(f"  Email:    {'✅已配置' if HAS_EMAIL else '❌未配置(设置SMTP_* + NOTIFY_EMAIL)'}")
    print("=" * 50)

    result = send_daily_report()
    print(f"\n结果: {result}")

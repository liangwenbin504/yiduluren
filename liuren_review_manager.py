#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
六壬精选审核管理器
=================
AI初判 + 人工审核 + 超时自动通过 + 训练库反哺

状态流转：
  idle → starting → pending(待审核) → reviewing(审核中)
                          ↓                    ↓
                     auto_passed         approved(已通过)
                          ↓                    ↓
                     存入训练库           存入训练库（高质量）

用法：
  from liuren_review_manager import ReviewManager
  mgr = ReviewManager()
  task_id = mgr.start_review(stocks, shichen)
  status = mgr.get_status(task_id)
  mgr.save_review(task_id, reviews, reviewer)
"""

import json, os, sys, time, threading
from datetime import datetime, date, timedelta
from pathlib import Path
from collections import OrderedDict

BASE = os.path.dirname(os.path.abspath(__file__))
MEMORY = os.path.join(BASE, "_memory")
DATA_DIR = os.path.join(BASE, "data")
os.makedirs(MEMORY, exist_ok=True)

REVIEW_DIR = os.path.join(MEMORY, "liuren_reviews")
os.makedirs(REVIEW_DIR, exist_ok=True)

DEFAULT_TIMEOUT_HOURS = 48
REMINDED_HOURS = 24


def _ts():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _now():
    return datetime.now()


class ReviewManager:
    """六壬精选审核管理器"""

    def __init__(self, timeout_hours=None):
        self.timeout_hours = timeout_hours or DEFAULT_TIMEOUT_HOURS
        self._lock = threading.Lock()
        self._cache = OrderedDict()
        self._load_all()

    def _load_all(self):
        """加载所有审核任务到内存"""
        try:
            for f in sorted(Path(REVIEW_DIR).glob("review_*.json")):
                try:
                    with open(f, "r", encoding="utf-8") as fh:
                        data = json.load(fh)
                        tid = data.get("task_id", "")
                        if tid:
                            self._cache[tid] = data
                except:
                    pass
        except:
            pass

    def _save(self, task):
        """保存任务到文件"""
        tid = task["task_id"]
        fpath = os.path.join(REVIEW_DIR, f"review_{tid}.json")
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(task, f, ensure_ascii=False, indent=2)
        self._cache[tid] = task

    def _gen_task_id(self):
        """生成任务ID"""
        return datetime.now().strftime("%Y%m%d_%H%M%S")

    def start_review(self, stocks, shichen=None, rizhu=None, source="manual", timeout_hours=None):
        """
        开始一次六壬精选审核

        Args:
            stocks: 股票列表 [{"code":"600519","name":"贵州茅台","score":85}, ...]
            shichen: 占时（时辰），如 "午时"
            rizhu: 日柱，如 "辛卯"
            source: 来源（manual/scheduler）
            timeout_hours: 本次任务的审核时限（小时）；为空时使用管理器默认值

        Returns:
            task_id 字符串
        """
        with self._lock:
            task_id = self._gen_task_id()
            now = _now()
            ttl = timeout_hours or self.timeout_hours

            task = {
                "task_id": task_id,
                "status": "starting",
                "source": source,
                "created_at": _ts(),
                "created_ts": now.timestamp(),
                "rizhu": rizhu or "",
                "shichen": shichen or "",
                "timeout_hours": ttl,
                "expire_at": (now + timedelta(hours=ttl)).strftime("%Y-%m-%d %H:%M:%S"),
                "expire_ts": (now + timedelta(hours=ttl)).timestamp(),
                "first_reminded": False,
                "stocks": stocks,
                "ai_predictions": [],
                "human_reviews": [],
                "reviewer": None,
                "reviewed_at": None,
                "paipan_info": {},
                "note": "",
            }

            self._run_ai_predict(task)
            self._save(task)

            self._send_notification(task, "start")

            return task_id

    def _run_ai_predict(self, task):
        """执行AI预测（一课多断）"""
        try:
            from multi_stock_predict import predict_multi_stocks_from_list

            codes = [s.get("code", "") for s in task.get("stocks", [])]
            names = [s.get("name", "") for s in task.get("stocks", [])]

            result = predict_multi_stocks_from_list(
                codes, names,
                shichen=task.get("shichen"),
                rizhu=task.get("rizhu")
            )

            if result and isinstance(result, dict):
                predictions = result.get("predictions", [])
                task["ai_predictions"] = predictions
                task["paipan_info"] = {
                    "rizhu": result.get("rizhu", ""),
                    "shichen": result.get("shichen", ""),
                    "sike": result.get("sike", ""),
                    "sanchuan": result.get("sanchuan", ""),
                    "keti": result.get("keti", ""),
                }
                task["rizhu"] = result.get("rizhu", task.get("rizhu", ""))
                task["shichen"] = result.get("shichen", task.get("shichen", ""))

            task["status"] = "pending"
            task["human_reviews"] = [
                {
                    "code": p.get("code", p.get("symbol", "")),
                    "name": p.get("name", ""),
                    "ai_trend": p.get("trend", "?"),
                    "ai_jixiong": p.get("jixiong", "?"),
                    "ai_confidence": p.get("confidence", 0),
                    "ai_analysis": p.get("analysis", ""),
                    "human_trend": p.get("trend", "?"),
                    "human_jixiong": p.get("jixiong", "?"),
                    "human_confidence": p.get("confidence", 0),
                    "review_note": "",
                    "is_modified": False,
                }
                for p in task.get("ai_predictions", [])
            ]

        except Exception as e:
            print(f"[ReviewManager] AI预测失败: {e}")
            import traceback
            traceback.print_exc()
            task["status"] = "error"
            task["error"] = str(e)

    def get_status(self, task_id=None):
        """
        获取审核状态

        Args:
            task_id: 任务ID，None返回最新任务

        Returns:
            任务字典，含状态、剩余时间、预测列表等
        """
        with self._lock:
            if not task_id:
                if self._cache:
                    task_id = next(reversed(self._cache))
                else:
                    return None

            task = self._cache.get(task_id)
            if not task:
                return None

            self._check_timeout(task)

            result = dict(task)
            now_ts = _now().timestamp()
            remain = task.get("expire_ts", 0) - now_ts
            result["remain_seconds"] = max(0, int(remain))
            result["remain_human"] = self._format_remain(remain)

            return result

    def _check_timeout(self, task):
        """检查是否超时，超时则自动通过"""
        status = task.get("status", "")
        if status not in ("pending", "reviewing"):
            return

        now_ts = _now().timestamp()
        if now_ts >= task.get("expire_ts", 0):
            task["status"] = "auto_passed"
            task["reviewed_at"] = _ts()
            task["reviewer"] = "system_auto"
            task["note"] = f"审核超时（{self.timeout_hours}小时），自动采用AI判断"

            for r in task.get("human_reviews", []):
                r["human_trend"] = r.get("ai_trend", "?")
                r["human_jixiong"] = r.get("ai_jixiong", "?")
                r["human_confidence"] = r.get("ai_confidence", 0)
                r["is_modified"] = False

            self._save(task)
            self._save_to_training(task)
            self._send_notification(task, "auto_pass")

    def _format_remain(self, seconds):
        """格式化剩余时间"""
        if seconds <= 0:
            return "已超时"
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        if h > 0:
            return f"{h}小时{m}分"
        elif m > 0:
            return f"{m}分{s}秒"
        else:
            return f"{s}秒"

    def save_review(self, task_id, reviews, reviewer="user"):
        """
        保存人工审核结果

        Args:
            task_id: 任务ID
            reviews: 审核列表 [{"code":"600519","human_trend":"看涨","human_jixiong":"吉","review_note":"..."}]
            reviewer: 审核人

        Returns:
            bool 是否成功
        """
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                return False

            status = task.get("status", "")
            if status not in ("pending", "reviewing"):
                return False

            review_map = {r.get("code"): r for r in reviews}

            modified_count = 0
            for r in task.get("human_reviews", []):
                code = r.get("code", "")
                if code in review_map:
                    rv = review_map[code]
                    old_trend = r.get("human_trend", "")
                    new_trend = rv.get("human_trend", old_trend)
                    r["human_trend"] = new_trend
                    r["human_jixiong"] = rv.get("human_jixiong", r.get("human_jixiong", ""))
                    r["human_confidence"] = rv.get("human_confidence", r.get("human_confidence", 0))
                    r["review_note"] = rv.get("review_note", r.get("review_note", ""))
                    r["is_modified"] = (new_trend != r.get("ai_trend", ""))
                    if r["is_modified"]:
                        modified_count += 1

            task["status"] = "approved"
            task["reviewed_at"] = _ts()
            task["reviewer"] = reviewer
            task["modified_count"] = modified_count

            self._save(task)
            self._save_to_training(task)
            self._send_notification(task, "approved")

            return True

    def skip_review(self, task_id, reason=""):
        """跳过六壬精选"""
        with self._lock:
            task = self._cache.get(task_id)
            if not task:
                return False

            task["status"] = "skipped"
            task["reviewed_at"] = _ts()
            task["note"] = reason or "用户跳过六壬精选"

            self._save(task)
            return True

    def _save_to_training(self, task):
        """将审核结果存入训练库（高质量样本）"""
        try:
            training_file = os.path.join(DATA_DIR, "stock_training_cases.json")
            cases = []
            if os.path.exists(training_file):
                with open(training_file, "r", encoding="utf-8") as f:
                    cases = json.load(f)

            status = task.get("status", "")
            is_high_quality = (status == "approved")

            for r in task.get("human_reviews", []):
                case_id = f"REVIEW-{task['task_id']}-{r.get('code', '')}"

                existing = next((c for c in cases if c.get("case_id") == case_id), None)
                if existing:
                    cases.remove(existing)

                case = {
                    "case_id": case_id,
                    "source": "human_review",
                    "high_quality": is_high_quality,
                    "date": task.get("created_at", "")[:10],
                    "stock_code": r.get("code", ""),
                    "stock_name": r.get("name", ""),
                    "rizhu": task.get("rizhu", ""),
                    "shichen": task.get("shichen", ""),
                    "keti": task.get("paipan_info", {}).get("keti", ""),
                    "sanchuan": task.get("paipan_info", {}).get("sanchuan", ""),
                    "ai_trend": r.get("ai_trend", ""),
                    "ai_jixiong": r.get("ai_jixiong", ""),
                    "ai_confidence": r.get("ai_confidence", 0),
                    "human_trend": r.get("human_trend", ""),
                    "human_jixiong": r.get("human_jixiong", ""),
                    "is_modified": r.get("is_modified", False),
                    "review_note": r.get("review_note", ""),
                    "reviewer": task.get("reviewer", ""),
                    "reviewed_at": task.get("reviewed_at", ""),
                    "actual_result": None,
                    "prediction_window_days": 20,
                    "key_lessons": [],
                }

                if r.get("review_note"):
                    case["key_lessons"].append(r["review_note"])

                if r.get("is_modified"):
                    case["key_lessons"].append(
                        f"AI判断{r.get('ai_trend')}→人工修正为{r.get('human_trend')}"
                    )

                cases.append(case)

            with open(training_file, "w", encoding="utf-8") as f:
                json.dump(cases, f, ensure_ascii=False, indent=2)

            print(f"[ReviewManager] 已存入训练库: {len(task.get('human_reviews', []))}条")
        except Exception as e:
            print(f"[ReviewManager] 存入训练库失败: {e}")

    def _send_notification(self, task, ntype):
        """发送pushplus通知"""
        try:
            from notify import send_pushplus

            title = ""
            content = ""

            if ntype == "start":
                count = len(task.get("ai_predictions", []))
                title = f"🔍 六壬精选待审核 ({count}只)"
                content = f"""## 🔍 六壬精选待审核

**任务ID**: {task['task_id']}
**选股数量**: {count}只
**日柱**: {task.get('rizhu', '?')}
**时辰**: {task.get('shichen', '?')}
**课体**: {task.get('paipan_info', {}).get('keti', '?')}
**三传**: {task.get('paipan_info', {}).get('sanchuan', '?')}

⏰ **审核时限**: {self.timeout_hours}小时（{task.get('expire_at', '')}）

请在虚拟预测系统 → 选股·个股 → 六壬精选模块中审核。

> 超时未审核将自动采用AI判断"""

            elif ntype == "auto_pass":
                count = len(task.get("human_reviews", []))
                title = f"⏰ 六壬精选审核超时，自动通过 ({count}只)"
                content = f"""## ⏰ 审核超时自动通过

**任务ID**: {task['task_id']}
**超时原因**: {self.timeout_hours}小时未审核
**处理方式**: 全部采用AI判断

请及时查看并修正，修正后的结果将作为高质量训练样本。"""

            elif ntype == "approved":
                modified = task.get("modified_count", 0)
                total = len(task.get("human_reviews", []))
                title = f"✅ 六壬精选审核完成 ({modified}/{total}只修正)"
                content = f"""## ✅ 审核完成

**任务ID**: {task['task_id']}
**审核人**: {task.get('reviewer', '')}
**审核时间**: {task.get('reviewed_at', '')}
**修正数量**: {modified}/{total}只

修正后的结果已存入训练库，用于模型持续优化。"""

            if title and content:
                send_pushplus(title, content)
        except Exception as e:
            print(f"[ReviewManager] 通知发送失败: {e}")

    def check_reminders(self):
        """检查是否需要发送提醒（定时任务调用）"""
        with self._lock:
            now_ts = _now().timestamp()
            for task_id, task in self._cache.items():
                status = task.get("status", "")
                if status not in ("pending", "reviewing"):
                    continue
                if task.get("first_reminded"):
                    continue

                created = task.get("created_ts", 0)
                elapsed = now_ts - created
                if elapsed >= REMINDED_HOURS * 3600:
                    task["first_reminded"] = True
                    self._save(task)
                    try:
                        self._send_reminder(task)
                    except:
                        pass

    def _send_reminder(self, task):
        """发送24小时未审核提醒"""
        try:
            from notify import send_pushplus
            count = len(task.get("ai_predictions", []))
            remain = task.get("expire_ts", 0) - _now().timestamp()
            remain_h = int(max(0, remain) // 3600)

            title = f"⏰ 六壬精选待审核提醒（剩余{remain_h}小时）"
            content = f"""## ⏰ 审核提醒

您有 {count} 只股票的六壬精选待审核。

**任务ID**: {task['task_id']}
**剩余时间**: {remain_h}小时
**超时处理**: 自动采用AI判断

请及时审核，您的修正将作为高质量训练样本，帮助AI持续进步。"""

            send_pushplus(title, content)
        except Exception as e:
            print(f"[ReviewManager] 提醒发送失败: {e}")

    def list_tasks(self, limit=10):
        """列出最近的审核任务"""
        tasks = []
        for tid in list(reversed(self._cache.keys()))[:limit]:
            task = self._cache[tid]
            tasks.append({
                "task_id": task.get("task_id"),
                "status": task.get("status"),
                "created_at": task.get("created_at"),
                "stock_count": len(task.get("ai_predictions", [])),
                "rizhu": task.get("rizhu"),
                "shichen": task.get("shichen"),
            })
        return tasks


_review_manager = None


def get_review_manager():
    """获取单例审核管理器"""
    global _review_manager
    if _review_manager is None:
        _review_manager = ReviewManager()
    return _review_manager


if __name__ == "__main__":
    print("=" * 60)
    print("  六壬精选审核管理器")
    print("=" * 60)
    mgr = get_review_manager()
    tasks = mgr.list_tasks(5)
    if tasks:
        print(f"\n最近 {len(tasks)} 个任务:")
        for t in tasks:
            print(f"  [{t['status']}] {t['task_id']} {t['stock_count']}只 {t.get('rizhu','')}{t.get('shichen','')}")
    else:
        print("\n暂无审核任务")

    status = mgr.get_status()
    if status:
        print(f"\n最新任务状态: {status['status']}")
        print(f"  剩余时间: {status.get('remain_human', '?')}")

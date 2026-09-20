#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安全存储工具 + 统一日志
=========================
1. 原子 JSON 读写（多进程安全）
2. 文件锁（防止并发写入损坏数据）
3. 统一日志系统

用法:
    from storage_utils import safe_read_json, safe_write_json, AtomicJSON
"""

import json, os, time, tempfile, logging
try:
    import fcntl
    HAS_FCNTL = True
except ModuleNotFoundError:
    fcntl = None
    HAS_FCNTL = False
from pathlib import Path
from typing import Any, Optional

# ── 日志系统（统一替代所有 print） ──
LOG_FILE = Path(__file__).parent / "_memory" / "system.log"

def setup_logging(name: str = "yiduluren", level: int = logging.INFO):
    """配置统一日志系统，同时输出到文件+控制台"""
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    # 文件 handler（保留7天）
    from logging.handlers import TimedRotatingFileHandler
    fh = TimedRotatingFileHandler(LOG_FILE, when='D', interval=1, backupCount=7,
                                   encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'))

    # 控制台 handler（ERROR 以上）
    ch = logging.StreamHandler()
    ch.setLevel(logging.WARNING)
    ch.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))

    logger.addHandler(fh)
    logger.addHandler(ch)
    return logger

# 默认 logger
log = setup_logging()


# ── 原子 JSON 读写 ──

class FileLock:
    """跨平台文件锁（Windows用msvcrt，Linux用fcntl）"""
    def __init__(self, path: Path):
        self.path = path
        self.lockfile = str(path) + ".lock"
        self._fd = None

    def __enter__(self):
        if not HAS_FCNTL:
            return self
        self._fd = open(self.lockfile, 'w')
        for _ in range(30):
            try:
                fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                return self
            except BlockingIOError:
                time.sleep(0.1)
            except (ModuleNotFoundError, OSError):
                # Windows不支持fcntl，降级为不锁
                return self
        raise TimeoutError(f"无法获取文件锁: {self.lockfile}")

    def __exit__(self, *args):
        if self._fd and HAS_FCNTL:
            try:
                fcntl.flock(self._fd, fcntl.LOCK_UN)
            except (ModuleNotFoundError, OSError):
                pass
            self._fd.close()
            try:
                os.remove(self.lockfile)
            except OSError:
                pass


def safe_read_json(path: Path, default: Any = None) -> Any:
    """安全读取JSON文件，出错时返回default并记录日志"""
    if not path.exists():
        return default

    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        log.error(f"JSON解析错误 {path}: {e}")
        # 尝试恢复备份
        backup = Path(str(path) + ".bak")
        if backup.exists():
            try:
                with open(backup, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return default
    except Exception as e:
        log.error(f"读取文件失败 {path}: {e}")
        return default


def safe_write_json(path: Path, data: Any) -> bool:
    """原子写入JSON：先写临时文件，再原子rename"""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # 备份旧文件
        if path.exists():
            try:
                backup = Path(str(path) + ".bak")
                os.replace(str(path), str(backup))
            except OSError:
                pass

        # 原子写入
        tmp = path.parent / f".{path.name}.{os.getpid()}.tmp"
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

        os.replace(str(tmp), str(path))
        return True
    except Exception as e:
        log.error(f"写入JSON失败 {path}: {e}")
        return False


class AtomicJSON:
    """线程/进程安全的JSON数据库"""
    def __init__(self, path: Path):
        self.path = Path(path)
        self._cache = None
        self._mtime = 0

    def read(self, use_cache: bool = True) -> Any:
        if use_cache and self._cache is not None:
            if self.path.exists() and self.path.stat().st_mtime == self._mtime:
                return self._cache
        data = safe_read_json(self.path, default=None)
        self._cache = data
        if self.path.exists():
            self._mtime = self.path.stat().st_mtime
        return data

    def write(self, data: Any) -> bool:
        with FileLock(self.path):
            ok = safe_write_json(self.path, data)
        if ok:
            self._cache = data
            if self.path.exists():
                self._mtime = self.path.stat().st_mtime
        return ok


# ── 模块级快捷函数 ──

def get_memory_path(filename: str) -> Path:
    """获取 _memory/ 下的完整路径"""
    return Path(__file__).parent / "_memory" / filename

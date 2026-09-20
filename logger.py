#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""统一日志系统 — 滚动文件 + 控制台双输出"""
import logging, os, sys
from logging.handlers import RotatingFileHandler
from datetime import datetime

_logger = None
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '_memory')


def get_logger(name='yiduluren', level=logging.INFO) -> logging.Logger:
    global _logger
    if _logger:
        return _logger

    os.makedirs(LOG_DIR, exist_ok=True)

    _logger = logging.getLogger(name)
    _logger.setLevel(level)

    if not _logger.handlers:
        # 控制台
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        ch.setFormatter(logging.Formatter('%(asctime)s [%(levelname).1s] %(message)s', '%H:%M:%S'))
        _logger.addHandler(ch)

        # 滚动文件（5MB×3个）
        fh = RotatingFileHandler(
            os.path.join(LOG_DIR, 'system.log'),
            maxBytes=5*1024*1024, backupCount=3, encoding='utf-8'
        )
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(name)s:%(lineno)d %(message)s'))
        _logger.addHandler(fh)

    return _logger


def log_event(category: str, message: str, level='info'):
    """快捷事件记录"""
    logger = get_logger()
    fn = getattr(logger, level, logger.info)
    fn(f'[{category}] {message}')


# 初始化
get_logger().info('日志系统初始化')

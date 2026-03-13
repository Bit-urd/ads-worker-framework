"""日志配置"""

import logging
import sys
from datetime import datetime
from pathlib import Path

from .config import ROOT_DIR


LOGS_DIR = ROOT_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)


def setup_logger(
    name: str = "ads_worker",
    level: int = logging.INFO,
    log_file: bool = True,
) -> logging.Logger:
    """
    配置日志

    Args:
        name: 日志名称
        level: 日志级别
        log_file: 是否输出到文件
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 文件输出
    if log_file:
        date_str = datetime.now().strftime("%Y-%m-%d")
        file_path = LOGS_DIR / f"{date_str}.log"
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 默认 logger
logger = setup_logger()


def get_logger(name: str) -> logging.Logger:
    """获取子 logger"""
    return logging.getLogger(f"ads_worker.{name}")

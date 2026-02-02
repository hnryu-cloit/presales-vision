# -*- coding: utf-8 -*-
"""
Logging Module for CEN AI DAM Editor

Provides centralized logging functionality with colored output.
"""

import logging
from colorlog import ColoredFormatter
import time
import functools

APP_LOGGER_NAME = 'ITCEN CLOIT'

_logger_initialized = False


def init_logger(log_level=logging.INFO, log_format=None):
    """
    Initialize the application logger.

    Args:
        log_level: Logging level (default: INFO)
        log_format: Custom log format string

    Returns:
        Configured logger instance
    """
    global _logger_initialized

    if log_format is None:
        log_format = (
            '%(asctime)s - '
            '%(name)s - '
            '%(funcName)s - '
            '%(log_color)s%(levelname)s - '
            '%(message)s'
        )

    formatter = ColoredFormatter(
        log_format,
        reset=True,
        log_colors={
            'DEBUG': 'cyan',
            'INFO': 'green',
            'WARNING': 'yellow',
            'ERROR': 'red',
            'CRITICAL': 'bold_red',
        }
    )

    logger = logging.getLogger(APP_LOGGER_NAME)
    logger.setLevel(log_level)

    # 부모 로거로의 전파 방지
    logger.propagate = False

    # 기존 핸들러 제거
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # 콘솔 출력 설정
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(log_level)
    logger.addHandler(ch)

    _logger_initialized = True

    return logger


def get_logger():
    """
    Get the application logger instance.

    Returns:
        Logger instance (initializes if not already done)
    """
    global _logger_initialized

    if not _logger_initialized:
        return init_logger()

    return logging.getLogger(APP_LOGGER_NAME)


def is_initialized(logger_name=None):
    """Check if the logger is initialized."""
    if logger_name is None:
        logger_name = APP_LOGGER_NAME
    logger = logging.getLogger(logger_name)
    return len(logger.handlers) > 0


def timefn(fn):
    """
    Decorator to measure and log function execution time.

    Args:
        fn: Function to wrap

    Returns:
        Wrapped function
    """
    @functools.wraps(fn)
    def measure_time(*args, **kwargs):
        logger = get_logger()
        start_time = time.time()
        result = fn(*args, **kwargs)
        end_time = time.time()
        execution_time = end_time - start_time
        logger.info(f"함수 {fn.__name__} 실행 시간: {execution_time:.2f}초")
        return result

    return measure_time
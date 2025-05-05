#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
装饰器工具模块

提供各种通用装饰器，如重试装饰器、计时装饰器等
"""

import time
import functools
from typing import Callable, Any, TypeVar, Optional
from loguru import logger

from config import DEFAULT_RETRY_TIMES, DEFAULT_RETRY_DELAY

# 定义类型变量
F = TypeVar("F", bound=Callable[..., Any])


def retry(
    retries: int = DEFAULT_RETRY_TIMES,
    delay: float = DEFAULT_RETRY_DELAY,
    exceptions: tuple = (Exception,),
    logger_func: Optional[Callable] = None,
) -> Callable[[F], F]:
    """
    通用重试装饰器

    Args:
        retries: 最大重试次数
        delay: 重试间隔(秒)
        exceptions: 需要捕获的异常类型
        logger_func: 自定义日志函数，如果不指定则使用loguru.logger

    Returns:
        装饰器函数
    """
    log = logger_func or logger

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == retries - 1:  # 最后一次尝试
                        log.error(
                            f"函数 {func.__name__} 在 {retries} 次尝试后最终执行失败: {str(e)}"
                        )
                        raise
                    else:
                        log.warning(
                            f"函数 {func.__name__} 第 {attempt + 1}/{retries} 次尝试失败: {str(e)}"
                        )
                        time.sleep(delay)

            # 理论上永远不会执行到这里，但为了类型安全
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return decorator


def timeit(logger_func: Optional[Callable] = None) -> Callable[[F], F]:
    """
    计时装饰器

    Args:
        logger_func: 自定义日志函数，如果不指定则使用loguru.logger

    Returns:
        装饰器函数
    """
    log = logger_func or logger

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.time()
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            log.debug(f"函数 {func.__name__} 执行耗时: {execution_time:.4f} 秒")
            return result

        return wrapper  # type: ignore

    return decorator


def log_entry_exit(logger_func: Optional[Callable] = None) -> Callable[[F], F]:
    """
    记录函数进入和退出的装饰器

    Args:
        logger_func: 自定义日志函数，如果不指定则使用loguru.logger

    Returns:
        装饰器函数
    """
    log = logger_func or logger

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            log.debug(f"进入函数: {func.__name__}")
            try:
                result = func(*args, **kwargs)
                log.debug(f"退出函数: {func.__name__}")
                return result
            except Exception as e:
                log.debug(f"函数 {func.__name__} 执行出错: {str(e)}")
                raise

        return wrapper  # type: ignore

    return decorator

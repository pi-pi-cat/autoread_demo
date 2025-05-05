#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置模块

此模块集成了所有配置项，包括常量、默认值和用户配置
"""

from .settings import *
from .user_config import load_config, get_config, create_default_config, DEFAULT_CONFIG

__all__ = [
    # 从settings.py导出
    "HOME_URL",
    "PAGE_URL",
    "LOGIN_URL",
    "CONNECT_URL",
    "SELECTOR_CURRENT_USER",
    "SELECTOR_LOGIN_FORM",
    "SELECTOR_LOGIN_USERNAME",
    "SELECTOR_LOGIN_PASSWORD",
    "SELECTOR_LOGIN_BUTTON",
    "MAX_TOPICS",
    "MAX_SCROLL_TIMES",
    "SCROLL_DISTANCE_MIN",
    "SCROLL_DISTANCE_MAX",
    "SCROLL_WAIT_MIN",
    "SCROLL_WAIT_MAX",
    "LIKE_PROBABILITY",
    "DEFAULT_RETRY_TIMES",
    "DEFAULT_RETRY_DELAY",
    "SERVER_PUSH_RETRY_TIMES",
    "SERVER_PUSH_RETRY_INTERVAL_MIN",
    "SERVER_PUSH_RETRY_INTERVAL_MAX",
    "REGEX_TABLE",
    "REGEX_TR",
    "REGEX_TD_TH",
    "REGEX_HTML_TAGS",
    "REGEX_WHITESPACE",
    "REGEX_SC3_UID",
    "NOTIFICATION_TITLE",
    "NOTIFICATION_SUCCESS_PREFIX",
    "LOG_LEVEL",
    "LOG_FORMAT",
    # 从user_config.py导出
    "load_config",
    "get_config",
    "create_default_config",
    "DEFAULT_CONFIG",
]

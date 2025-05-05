#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
常量和默认配置模块

本模块包含程序运行所需的所有常量和默认配置项
"""

import os
from pathlib import Path

# 项目根目录路径
ROOT_DIR = Path(__file__).parent.parent.absolute()

# ================ 网站URL配置 ================
HOME_URL = "https://linux.do/"
PAGE_URL = "https://linux.do/new"
LOGIN_URL = "https://linux.do/login"
CONNECT_URL = "https://connect.linux.do/"

# ================ 选择器配置 ================
SELECTOR_CURRENT_USER = "#current-user"
SELECTOR_LOGIN_FORM = "#login-form"
SELECTOR_LOGIN_USERNAME = "#login-account-name"
SELECTOR_LOGIN_PASSWORD = "#login-account-password"
SELECTOR_LOGIN_BUTTON = "#login-button"

# ================ 浏览参数配置 ================
MAX_TOPICS = 5  # 每次浏览的主题数量
MAX_SCROLL_TIMES = 10  # 最大滚动次数
SCROLL_DISTANCE_MIN = 550  # 最小滚动距离
SCROLL_DISTANCE_MAX = 650  # 最大滚动距离
SCROLL_WAIT_MIN = 2  # 最小滚动等待时间(秒)
SCROLL_WAIT_MAX = 4  # 最大滚动等待时间(秒)
LIKE_PROBABILITY = 0.3  # 点赞概率

# ================ 重试参数配置 ================
DEFAULT_RETRY_TIMES = 3  # 默认重试次数
DEFAULT_RETRY_DELAY = 1  # 默认重试延迟(秒)
SERVER_PUSH_RETRY_TIMES = 5  # Server酱推送重试次数
SERVER_PUSH_RETRY_INTERVAL_MIN = 180  # 最小重试间隔(秒)
SERVER_PUSH_RETRY_INTERVAL_MAX = 360  # 最大重试间隔(秒)

# ================ 正则表达式模式 ================
REGEX_TABLE = r"<table>(.*?)</table>"
REGEX_TR = r"<tr>(.*?)</tr>"
REGEX_TD_TH = r"<t[hd][^>]*>(.*?)</t[hd]>"
REGEX_HTML_TAGS = r"<.*?>"
REGEX_WHITESPACE = r"\s+"
REGEX_SC3_UID = r"sct(\d+)t"

# ================ 通知配置 ================
NOTIFICATION_TITLE = "LINUX DO"  # 通知标题
NOTIFICATION_SUCCESS_PREFIX = "✅每日登录成功"  # 成功通知前缀

# ================ 日志配置 ================
LOG_LEVEL = "INFO"  # 日志级别
LOG_FORMAT = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"  # 日志格式

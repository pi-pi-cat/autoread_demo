#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心功能模块

此模块集成了所有核心功能，包括浏览器管理、登录、主题浏览和连接信息等
"""

from .browser import BrowserManager, browser_manager
from .login import LoginManager, create_login_manager
from .topic_browser import TopicBrowser, topic_browser
from .connect_info import ConnectInfoManager, connect_info_manager

__all__ = [
    # 从browser.py导出
    "BrowserManager",
    "browser_manager",
    # 从login.py导出
    "LoginManager",
    "create_login_manager",
    # 从topic_browser.py导出
    "TopicBrowser",
    "topic_browser",
    # 从connect_info.py导出
    "ConnectInfoManager",
    "connect_info_manager",
]

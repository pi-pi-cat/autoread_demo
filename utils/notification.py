#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知模块

提供多种通知方式的实现，包括Gotify、Server酱等
"""

import re
import time
import random
import requests
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Union
from loguru import logger

from config import (
    NOTIFICATION_TITLE,
    SERVER_PUSH_RETRY_TIMES,
    SERVER_PUSH_RETRY_INTERVAL_MIN,
    SERVER_PUSH_RETRY_INTERVAL_MAX,
    REGEX_SC3_UID,
)
from utils.decorators import retry


class NotificationHandler(ABC):
    """通知处理器抽象基类"""

    @abstractmethod
    def send(self, message: str, **kwargs: Any) -> bool:
        """
        发送通知

        Args:
            message: 通知消息
            **kwargs: 其他参数

        Returns:
            bool: 是否发送成功
        """
        pass


class GotifyNotification(NotificationHandler):
    """Gotify通知处理器"""

    def __init__(self, url: str, token: str):
        """
        初始化Gotify通知处理器

        Args:
            url: Gotify服务器URL
            token: Gotify应用Token
        """
        self.url = url
        self.token = token

    @retry(retries=3, delay=2)
    def send(self, message: str, **kwargs: Any) -> bool:
        """
        发送Gotify通知

        Args:
            message: 通知消息
            **kwargs: 其他参数，可以包含:
                - title: 通知标题，默认为NOTIFICATION_TITLE
                - priority: 通知优先级，默认为1

        Returns:
            bool: 是否发送成功
        """
        title = kwargs.get("title", NOTIFICATION_TITLE)
        priority = kwargs.get("priority", 1)

        try:
            response = requests.post(
                f"{self.url}/message",
                params={"token": self.token},
                json={"title": title, "message": message, "priority": priority},
                timeout=10,
            )
            response.raise_for_status()
            logger.success("消息已推送至Gotify")
            return True
        except Exception as e:
            logger.error(f"Gotify推送失败: {str(e)}")
            return False


class ServerChanNotification(NotificationHandler):
    """Server酱通知处理器"""

    def __init__(self, push_key: str):
        """
        初始化Server酱通知处理器

        Args:
            push_key: Server酱推送密钥
        """
        self.push_key = push_key
        # 预编译正则表达式
        self.re_sc3_uid = re.compile(REGEX_SC3_UID, re.I)

    def send(self, message: str, **kwargs: Any) -> bool:
        """
        发送Server酱通知

        Args:
            message: 通知消息
            **kwargs: 其他参数，可以包含:
                - title: 通知标题，默认为NOTIFICATION_TITLE

        Returns:
            bool: 是否发送成功
        """
        # 验证SC3_PUSH_KEY格式
        match = self.re_sc3_uid.match(self.push_key)
        if not match:
            logger.error("❌ Server酱³推送密钥格式错误，未获取到UID")
            return False

        uid = match.group(1)
        url = f"https://{uid}.push.ft07.com/send/{self.push_key}"
        title = kwargs.get("title", NOTIFICATION_TITLE)
        params = {"title": title, "desp": message}

        # 重试发送
        for attempt in range(SERVER_PUSH_RETRY_TIMES):
            try:
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                logger.success(f"Server酱³推送成功: {response.text}")
                return True
            except Exception as e:
                logger.error(f"Server酱³推送失败: {str(e)}")
                if attempt < SERVER_PUSH_RETRY_TIMES - 1:
                    sleep_time = random.randint(
                        SERVER_PUSH_RETRY_INTERVAL_MIN, SERVER_PUSH_RETRY_INTERVAL_MAX
                    )
                    logger.info(f"将在 {sleep_time} 秒后重试...")
                    time.sleep(sleep_time)

        return False


class NotificationManager:
    """通知管理器，统一管理多种通知方式"""

    def __init__(self):
        """初始化通知管理器"""
        self.handlers: List[NotificationHandler] = []

    def add_handler(self, handler: NotificationHandler) -> None:
        """
        添加通知处理器

        Args:
            handler: 通知处理器实例
        """
        self.handlers.append(handler)

    def send_all(self, message: str, **kwargs: Any) -> Dict[int, bool]:
        """
        发送通知到所有处理器

        Args:
            message: 通知消息
            **kwargs: 其他参数

        Returns:
            Dict[int, bool]: 处理器索引和发送结果的字典
        """
        results = {}
        for i, handler in enumerate(self.handlers):
            results[i] = handler.send(message, **kwargs)
        return results

    def clear_handlers(self) -> None:
        """清除所有通知处理器"""
        self.handlers.clear()


# 创建一个全局通知管理器实例
notification_manager = NotificationManager()


def setup_notifications(config: Dict[str, Any]) -> NotificationManager:
    """
    根据配置设置通知处理器

    Args:
        config: 配置字典

    Returns:
        NotificationManager: 设置好的通知管理器
    """
    # 清除旧的处理器
    notification_manager.clear_handlers()

    # 设置Gotify
    gotify_config = config.get("notifications", {}).get("gotify", {})
    gotify_url = gotify_config.get("url")
    gotify_token = gotify_config.get("token")

    if gotify_url and gotify_token:
        notification_manager.add_handler(GotifyNotification(gotify_url, gotify_token))

    # 设置Server酱
    server_chan_config = config.get("notifications", {}).get("server_chan", {})
    server_chan_key = server_chan_config.get("push_key")

    if server_chan_key:
        notification_manager.add_handler(ServerChanNotification(server_chan_key))

    return notification_manager

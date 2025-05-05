#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
登录模块

负责网站登录和会话管理
"""

import time
from typing import Optional, Dict, Any, Tuple
from loguru import logger

from config import (
    HOME_URL,
    LOGIN_URL,
    SELECTOR_CURRENT_USER,
    SELECTOR_LOGIN_FORM,
    SELECTOR_LOGIN_USERNAME,
    SELECTOR_LOGIN_PASSWORD,
    SELECTOR_LOGIN_BUTTON,
)
from utils.decorators import retry, log_entry_exit
from core.browser import browser_manager


class LoginManager:
    """登录管理器，负责处理网站登录逻辑"""

    def __init__(self, username: str, password: str):
        """
        初始化登录管理器

        Args:
            username: 用户名
            password: 密码
        """
        self.username = username
        self.password = password
        self.is_logged_in = False

    @log_entry_exit()
    def open_login_page(self) -> bool:
        """
        打开登录页面

        Returns:
            bool: 是否成功打开登录页面
        """
        logger.info("正在打开登录页面...")
        result = browser_manager.navigate(LOGIN_URL, "main", wait_time=2.0)

        if result:
            # 获取当前页面并检查URL
            page = browser_manager.get_page("main")
            if page and page.url == LOGIN_URL:
                logger.info(f"已打开登录页面: {page.url}")
                return True
            else:
                logger.error(
                    f"打开登录页面失败，当前URL: {page.url if page else 'Unknown'}"
                )

        return False

    @retry(retries=3, delay=2)
    def check_login_status(self) -> bool:
        """
        检查当前登录状态

        Returns:
            bool: 是否已登录
        """
        # 访问首页
        browser_manager.navigate(HOME_URL, "main", wait_time=2.0)

        try:
            # 查找用户元素
            user_element = browser_manager.find_element(
                SELECTOR_CURRENT_USER, timeout=3.0
            )
            if user_element:
                self.is_logged_in = True
                logger.success("已处于登录状态")
                return True
        except ValueError:
            # 未找到元素，表示未登录
            logger.info("当前未登录")
            self.is_logged_in = False

        return False

    def fill_login_form(
        self, username: Optional[str] = None, password: Optional[str] = None
    ) -> bool:
        """
        填写登录表单

        Args:
            username: 用户名，默认使用初始化时提供的用户名
            password: 密码，默认使用初始化时提供的密码

        Returns:
            bool: 是否成功填写表单
        """
        # 使用提供的凭据或默认凭据
        username = username or self.username
        password = password or self.password

        if not username or not password:
            logger.error("未提供用户名或密码")
            return False

        try:
            # 查找登录表单
            browser_manager.find_element(SELECTOR_LOGIN_FORM, timeout=3.0)

            # 填写用户名
            username_field = browser_manager.find_element(SELECTOR_LOGIN_USERNAME)
            username_field.input(username)
            time.sleep(1)

            # 填写密码
            password_field = browser_manager.find_element(SELECTOR_LOGIN_PASSWORD)
            password_field.input(password)
            time.sleep(1)

            logger.info("已填写登录表单")
            return True
        except Exception as e:
            logger.error(f"填写登录表单失败: {str(e)}")
            return False

    def submit_login_form(self) -> bool:
        """
        提交登录表单

        Returns:
            bool: 是否成功提交表单
        """
        try:
            # 点击登录按钮
            login_button = browser_manager.find_element(SELECTOR_LOGIN_BUTTON)
            login_button.click()

            # 等待登录完成
            time.sleep(5)

            logger.info("已提交登录表单")
            return True
        except Exception as e:
            logger.error(f"提交登录表单失败: {str(e)}")
            return False

    def verify_login_success(self) -> bool:
        """
        验证登录是否成功

        Returns:
            bool: 是否成功登录
        """
        try:
            # 查找用户元素
            user_element = browser_manager.find_element(
                SELECTOR_CURRENT_USER, timeout=5.0
            )
            if user_element:
                self.is_logged_in = True
                logger.success("登录成功")
                return True
        except ValueError:
            # 未找到元素，表示登录失败
            self.is_logged_in = False
            logger.error("登录失败")

        return False

    @log_entry_exit()
    @retry(retries=2, delay=3)
    def login(self) -> bool:
        """
        执行完整登录流程

        Returns:
            bool: 是否成功登录
        """
        # 检查是否已登录
        if self.check_login_status():
            return True

        # 打开登录页面
        if not self.open_login_page():
            logger.error("无法打开登录页面")
            return False

        # 填写并提交登录表单
        if not self.fill_login_form():
            logger.error("填写登录表单失败")
            return False

        if not self.submit_login_form():
            logger.error("提交登录表单失败")
            return False

        # 验证登录结果
        if self.verify_login_success():
            return True

        logger.error("登录流程完成但验证失败")
        return False


# 创建登录器实例的工厂函数
def create_login_manager(config: Dict[str, Any]) -> LoginManager:
    """
    根据配置创建登录管理器

    Args:
        config: 配置字典

    Returns:
        LoginManager: 登录管理器实例
    """
    username = config.get("username")
    password = config.get("password")

    if not username or not password:
        logger.error("配置中未提供用户名或密码")

    return LoginManager(username, password)

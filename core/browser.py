#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
浏览器管理模块

提供浏览器初始化、页面管理等功能
"""

import time
from typing import Optional, Any, Dict, List, Union, Callable
from loguru import logger
from DrissionPage import ChromiumPage

from utils.decorators import retry, log_entry_exit


class BrowserManager:
    """浏览器管理器，负责创建和管理浏览器实例"""

    def __init__(self):
        """初始化浏览器管理器"""
        self.pages: Dict[str, ChromiumPage] = {}
        self.main_page: Optional[ChromiumPage] = None

    def create_page(self, page_id: str = "main") -> ChromiumPage:
        """
        创建新页面

        Args:
            page_id: 页面标识符

        Returns:
            ChromiumPage: 创建的页面实例
        """
        # 关闭之前的同ID页面(如果存在)
        if page_id in self.pages:
            self.close_page(page_id)

        # 创建新页面
        page = ChromiumPage()
        self.pages[page_id] = page

        # 如果是main页面，设置为主页面
        if page_id == "main" and self.main_page is None:
            self.main_page = page

        logger.debug(f"创建页面: {page_id}")
        return page

    def get_page(self, page_id: str = "main") -> Optional[ChromiumPage]:
        """
        获取页面实例

        Args:
            page_id: 页面标识符

        Returns:
            Optional[ChromiumPage]: 页面实例，如果不存在则返回None
        """
        return self.pages.get(page_id)

    def close_page(self, page_id: str) -> bool:
        """
        关闭并移除页面

        Args:
            page_id: 页面标识符

        Returns:
            bool: 是否成功关闭
        """
        if page_id in self.pages:
            try:
                page = self.pages[page_id]
                page.quit()
                del self.pages[page_id]

                # 如果关闭的是主页面，将main_page置为None
                if page_id == "main":
                    self.main_page = None

                logger.debug(f"关闭页面: {page_id}")
                return True
            except Exception as e:
                logger.warning(f"关闭页面 {page_id} 失败: {str(e)}")
        return False

    def close_all_pages(self) -> None:
        """关闭所有页面"""
        for page_id in list(self.pages.keys()):
            self.close_page(page_id)

    def navigate(self, url: str, page_id: str = "main", wait_time: float = 2.0) -> bool:
        """
        导航到URL

        Args:
            url: 目标URL
            page_id: 页面标识符
            wait_time: 加载后等待时间(秒)

        Returns:
            bool: 是否成功导航
        """
        page = self.get_page(page_id)
        if page is None:
            logger.warning(f"页面 {page_id} 不存在，创建新页面")
            page = self.create_page(page_id)

        try:
            logger.info(f"正在导航到: {url}")
            page.get(url)
            time.sleep(wait_time)  # 等待页面加载
            logger.info(f"已加载页面: {page.url}")
            return True
        except Exception as e:
            logger.error(f"导航到 {url} 失败: {str(e)}")
            return False

    @retry(retries=3, delay=1)
    def find_element(
        self, selector: str, page_id: str = "main", timeout: float = 5.0
    ) -> Any:
        """
        查找元素

        Args:
            selector: 元素选择器
            page_id: 页面标识符
            timeout: 超时时间(秒)

        Returns:
            Any: 找到的元素

        Raises:
            Exception: 如果未找到元素
        """
        page = self.get_page(page_id)
        if page is None:
            raise ValueError(f"页面 {page_id} 不存在")

        element = page.ele(selector, timeout=timeout)
        if not element:
            raise ValueError(f"未找到元素: {selector}")

        return element

    def find_elements(self, selector: str, page_id: str = "main") -> List[Any]:
        """
        查找所有匹配的元素

        Args:
            selector: 元素选择器
            page_id: 页面标识符

        Returns:
            List[Any]: 找到的元素列表
        """
        page = self.get_page(page_id)
        if page is None:
            logger.warning(f"页面 {page_id} 不存在")
            return []

        elements = page.eles(selector)
        logger.debug(f"找到 {len(elements)} 个元素: {selector}")
        return elements

    def execute_js(self, script: str, page_id: str = "main", *args: Any) -> Any:
        """
        执行JavaScript

        Args:
            script: JavaScript代码
            page_id: 页面标识符
            *args: 传递给脚本的参数

        Returns:
            Any: 脚本执行结果
        """
        page = self.get_page(page_id)
        if page is None:
            logger.warning(f"页面 {page_id} 不存在")
            return None

        try:
            return page.run_js(script, *args)
        except Exception as e:
            logger.error(f"执行JavaScript失败: {str(e)}")
            return None

    def get_page_source(self, page_id: str = "main") -> str:
        """
        获取页面源码

        Args:
            page_id: 页面标识符

        Returns:
            str: 页面HTML源码
        """
        page = self.get_page(page_id)
        if page is None:
            logger.warning(f"页面 {page_id} 不存在")
            return ""

        return page.html

    def get_page_text(self, page_id: str = "main") -> str:
        """
        获取页面文本内容

        Args:
            page_id: 页面标识符

        Returns:
            str: 页面文本内容
        """
        page = self.get_page(page_id)
        if page is None:
            logger.warning(f"页面 {page_id} 不存在")
            return ""

        return page.text

    def scroll_page(self, distance: int, page_id: str = "main") -> bool:
        """
        滚动页面

        Args:
            distance: 滚动距离(像素)，正值向下滚动，负值向上滚动
            page_id: 页面标识符

        Returns:
            bool: 是否成功滚动
        """
        page = self.get_page(page_id)
        if page is None:
            logger.warning(f"页面 {page_id} 不存在")
            return False

        try:
            page.run_js(f"window.scrollBy(0, {distance})")
            return True
        except Exception as e:
            logger.error(f"滚动页面失败: {str(e)}")
            return False

    def is_bottom_of_page(self, page_id: str = "main") -> bool:
        """
        检查是否滚动到页面底部

        Args:
            page_id: 页面标识符

        Returns:
            bool: 是否到达页面底部
        """
        page = self.get_page(page_id)
        if page is None:
            logger.warning(f"页面 {page_id} 不存在")
            return False

        try:
            return page.run_js(
                "return window.scrollY + window.innerHeight >= document.body.scrollHeight"
            )
        except Exception as e:
            logger.error(f"检查页面底部失败: {str(e)}")
            return False


# 创建一个全局浏览器管理器实例
browser_manager = BrowserManager()

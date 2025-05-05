#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
连接信息模块

负责获取和解析Linux.Do Connect信息
"""

import time
from typing import List, Dict, Any, Tuple, Optional
from loguru import logger
from tabulate import tabulate
from rich.console import Console
from rich.table import Table
from rich import box

from config import CONNECT_URL
from utils.decorators import retry, log_entry_exit
from core.browser import browser_manager
from utils.html_parser import extract_table_data, format_table


class ConnectInfoManager:
    """连接信息管理器，负责获取和解析连接信息"""

    def __init__(self):
        """初始化连接信息管理器"""
        self.last_headers = []
        self.last_data = []
        self.before_data = []  # 存储签到前的数据
        self.after_data = []  # 存储签到后的数据
        self.console = Console()  # Rich控制台实例
        self.compare_html = ""  # 存储HTML格式的对比结果

    @log_entry_exit()
    @retry(retries=3, delay=2)
    def get_connect_info(self, is_after=False) -> Tuple[List[str], List[List[str]]]:
        """
        获取并解析连接信息

        Args:
            is_after: 是否为签到后的数据获取

        Returns:
            Tuple[List[str], List[List[str]]]: 表头和数据行
        """
        # 创建独立页面获取连接信息
        page_id = "connect_info"

        try:
            # 创建新页面并导航到连接信息页面
            browser_manager.create_page(page_id)
            browser_manager.navigate(CONNECT_URL, page_id, wait_time=3.0)

            # 获取并检查页面标题
            page = browser_manager.get_page(page_id)
            if page:
                logger.info(f"页面标题: {page.title}")

            # 获取页面源码
            html = browser_manager.get_page_source(page_id)
            if not html:
                logger.error("获取页面源码失败")
                return [], []

            # 解析表格数据
            headers, data = self._parse_connect_info(html)

            # 保存结果
            self.last_headers = headers
            self.last_data = data

            # 根据is_after参数存储对应的数据集
            if is_after:
                self.after_data = data
                logger.info("已保存签到后的连接信息")
            else:
                self.before_data = data
                logger.info("已保存签到前的连接信息")

            # 打印表格
            self._display_connect_info(headers, data)

            return headers, data
        except Exception as e:
            logger.error(f"获取连接信息时出错: {str(e)}")
            import traceback

            logger.debug(f"错误详情: {traceback.format_exc()}")
            return [], []

    def _parse_connect_info(self, html: str) -> Tuple[List[str], List[List[str]]]:
        """
        解析连接信息HTML

        Args:
            html: 页面HTML内容

        Returns:
            Tuple[List[str], List[List[str]]]: 表头和数据行
        """
        # 使用HTML解析工具提取表格数据
        headers, data = extract_table_data(html)

        if data:
            logger.info(f"成功解析连接信息，获取到 {len(data)} 行数据")
        else:
            logger.warning("未能解析到连接信息数据")

        return headers, data

    def _display_connect_info(self, headers: List[str], data: List[List[str]]) -> None:
        """
        使用Rich打印连接信息表格

        Args:
            headers: 表头列表
            data: 数据行列表
        """
        if not data:
            logger.warning("没有连接信息数据可显示")
            return

        # 创建Rich表格
        table = Table(title="连接信息", box=box.DOUBLE_EDGE)

        # 添加表头
        for header in headers:
            table.add_column(header, style="cyan bold")

        # 添加数据行
        for row in data:
            table.add_row(*row)

        # 显示表格
        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

        # 将信息记录到日志
        for item in data:
            logger.info(f"连接信息: {', '.join(item)}")

    def get_compare_info_html(self) -> str:
        """
        生成Telegram兼容的HTML格式的连接信息对比

        Returns:
            str: Telegram兼容的HTML格式连接信息对比
        """
        if not self.before_data or not self.after_data:
            return "<b>⚠️ 缺少签到前或签到后的数据，无法进行对比</b>"

        # 构建Telegram兼容的HTML输出
        html_parts = []
        html_parts.append("<b>📊 连接信息对比</b>\n")

        # 表格内容
        max_rows = max(len(self.before_data), len(self.after_data))
        change_count = 0

        for i in range(max_rows):
            if i < len(self.before_data) and i < len(self.after_data):
                before_row = self.before_data[i]
                after_row = self.after_data[i]

                # 检查项目名称是否相同
                if before_row[0] == after_row[0]:
                    # 获取数据并进行HTML转义
                    item = self._escape_html(before_row[0])
                    before_val = self._escape_html(
                        before_row[1] if len(before_row) > 1 else ""
                    )
                    after_val = self._escape_html(
                        after_row[1] if len(after_row) > 1 else ""
                    )
                    requirement = self._escape_html(
                        before_row[2] if len(before_row) > 2 else ""
                    )

                    # 判断值是否有变化
                    has_changed = before_row[1] != after_row[1]

                    if has_changed:
                        change_count += 1
                        # 添加变化项的卡片
                        html_parts.append(f"\n<b>━━━ {item} ━━━</b>")
                        html_parts.append(f"📥 签到前：<i>{before_val}</i>")
                        html_parts.append(f"📤 签到后：<b>{after_val}</b> ✅")
                        if requirement:
                            html_parts.append(f"📋 要求：{requirement}")
                        html_parts.append("")  # 添加额外空行作为分隔
                    else:
                        # 如果未发生变化，使用更简洁的格式
                        html_parts.append(f"\n<b>{item}</b>：{after_val} (未变化)")

        # 添加总结信息
        if change_count > 0:
            html_parts.append(f"\n<b>🔄 共有 {change_count} 项数据发生变化</b>")
        else:
            html_parts.append("\n<b>ℹ️ 所有数据均未发生变化</b>")

        # 保存HTML格式的对比结果
        self.compare_html = "\n".join(html_parts)
        return self.compare_html

    def _escape_html(self, text: str) -> str:
        """
        转义HTML特殊字符

        Args:
            text: 需要转义的文本

        Returns:
            str: 转义后的文本
        """
        if not isinstance(text, str):
            text = str(text)

        return (
            text.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("'", "&#39;")
        )

    def display_compare_info(self) -> None:
        """
        对比显示签到前后的连接信息
        """
        if not self.before_data or not self.after_data:
            logger.warning("缺少签到前或签到后的数据，无法进行对比")
            return

        # 创建Rich表格用于对比
        table = Table(title="连接信息对比", box=box.DOUBLE_EDGE, show_lines=True)

        # 添加表头
        table.add_column("项目", style="cyan bold")
        table.add_column("签到前", style="blue")
        table.add_column("签到后", style="green")
        table.add_column("要求", style="yellow")

        # 对齐两组数据，并合并显示
        max_rows = max(len(self.before_data), len(self.after_data))

        for i in range(max_rows):
            if i < len(self.before_data) and i < len(self.after_data):
                # 两组数据都有
                before_row = self.before_data[i]
                after_row = self.after_data[i]

                # 检查项目名称是否相同，如果相同才进行对比
                if before_row[0] == after_row[0]:
                    # 添加项目、签到前、签到后、要求
                    item = before_row[0]
                    before_val = before_row[1] if len(before_row) > 1 else ""
                    after_val = after_row[1] if len(after_row) > 1 else ""
                    requirement = before_row[2] if len(before_row) > 2 else ""

                    # 如果值有变化，使用特殊样式
                    if before_val != after_val:
                        # 使用特殊样式表示变化
                        table.add_row(
                            item,
                            before_val,
                            f"[bold green]{after_val}[/bold green]",
                            requirement,
                        )
                    else:
                        table.add_row(item, before_val, after_val, requirement)

        # 显示表格
        self.console.print("\n")
        self.console.print(table)
        self.console.print("\n")

        # 同时生成HTML格式的对比结果
        self.get_compare_info_html()

        logger.info(f"已显示签到前后的连接信息对比，共 {max_rows} 行数据")

    def get_last_info(self) -> Tuple[List[str], List[List[str]]]:
        """
        获取上次获取的连接信息

        Returns:
            Tuple[List[str], List[List[str]]]: 表头和数据行
        """
        return self.last_headers, self.last_data

    def has_sufficient_signins(self) -> bool:
        """
        检查是否有足够的签到次数

        Returns:
            bool: 是否有足够的签到次数
        """
        if not self.last_data:
            logger.warning("没有连接信息数据，无法检查签到状态")
            return False

        # 查找签到相关的行
        for row in self.last_data:
            if len(row) >= 3 and "签到" in row[0]:
                try:
                    current = int(row[1].split()[0])  # 提取数字部分
                    required = int(row[2].split()[0])

                    logger.info(f"签到状态: 当前 {current}/{required}")
                    return current >= required
                except (ValueError, IndexError):
                    logger.warning(f"无法解析签到数据: {row}")

        logger.warning("未找到签到相关信息")
        return False


# 创建连接信息管理器实例
connect_info_manager = ConnectInfoManager()

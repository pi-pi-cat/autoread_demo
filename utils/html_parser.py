#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HTML解析工具模块

提供各种HTML解析和处理函数，用于从网页中提取和处理数据
"""

import re
from typing import List, Dict, Any, Optional, Tuple, Union
from loguru import logger

from config import REGEX_TABLE, REGEX_TR, REGEX_TD_TH, REGEX_HTML_TAGS, REGEX_WHITESPACE

# 预编译正则表达式
_re_table = re.compile(REGEX_TABLE, re.DOTALL)
_re_tr = re.compile(REGEX_TR, re.DOTALL)
_re_td_th = re.compile(REGEX_TD_TH, re.DOTALL)
_re_html_tags = re.compile(REGEX_HTML_TAGS)
_re_whitespace = re.compile(REGEX_WHITESPACE)


def clean_html(text: str) -> str:
    """
    清理HTML标签和多余空白

    Args:
        text: 包含HTML标签的文本

    Returns:
        str: 清理后的文本
    """
    if not text:
        return ""
    # 移除HTML标签
    text = _re_html_tags.sub("", text)
    # 替换连续空白为单个空格
    text = _re_whitespace.sub(" ", text)
    # 去除首尾空白
    return text.strip()


def extract_table_data(html: str) -> Tuple[List[str], List[List[str]]]:
    """
    从HTML中提取表格数据

    Args:
        html: 包含表格的HTML内容

    Returns:
        Tuple[List[str], List[List[str]]]: 表头和数据行的元组
    """
    # 默认表头和空数据行
    headers = ["项目", "当前", "要求"]
    data_rows = []

    # 寻找表格
    table_match = _re_table.search(html)
    if not table_match:
        logger.error("未找到表格")
        return headers, data_rows

    table_html = table_match.group(1)
    logger.debug("找到表格HTML")

    # 提取表格行
    rows = _re_tr.findall(table_html)
    if not rows:
        logger.error("表格中没有行")
        return headers, data_rows

    logger.debug(f"找到 {len(rows)} 行表格数据")

    # 处理表头(第一行)
    if rows:
        header_cells = _re_td_th.findall(rows[0])
        if header_cells:
            headers = [clean_html(cell) for cell in header_cells]
            if len(headers) < 3:  # 确保至少有3个表头
                headers.extend([""] * (3 - len(headers)))

    # 处理数据行
    for row in rows[1:]:  # 跳过表头
        cells = _re_td_th.findall(row)
        if cells:
            # 清理并处理每个单元格
            row_data = [clean_html(cell) for cell in cells]

            # 确保至少有3列
            while len(row_data) < 3:
                row_data.append("")

            # 添加到结果
            data_rows.append(row_data[:3])  # 只取前3列

    return headers, data_rows


def extract_links(
    html: str, selector: str = "a", attrs: Optional[List[str]] = None
) -> List[Dict[str, str]]:
    """
    从HTML中提取链接

    Args:
        html: HTML内容
        selector: CSS选择器，默认为'a'
        attrs: 要提取的属性列表，默认为['href', 'text']

    Returns:
        List[Dict[str, str]]: 链接信息列表，每个链接为一个字典
    """
    if attrs is None:
        attrs = ["href", "text"]

    # 使用正则表达式提取链接，这里简化处理
    # 在实际应用中，建议使用更强大的HTML解析库如BeautifulSoup
    links = []
    link_pattern = r'<a\s+(?:[^>]*?\s+)?href=(["\'])(.*?)\1[^>]*>(.*?)<\/a>'

    for match in re.finditer(link_pattern, html, re.IGNORECASE | re.DOTALL):
        href = match.group(2)
        text = clean_html(match.group(3))

        link_info = {"href": href, "text": text}
        links.append(link_info)

    return links


def format_table(headers: List[str], data: List[List[str]], fmt: str = "pretty") -> str:
    """
    格式化表格数据为可读字符串

    Args:
        headers: 表头列表
        data: 数据行列表
        fmt: 格式化类型，'pretty'或'markdown'

    Returns:
        str: 格式化后的表格字符串
    """
    if not data:
        return "没有数据"

    if fmt == "markdown":
        # 创建Markdown表格
        result = []
        # 表头
        result.append("| " + " | ".join(headers) + " |")
        # 分隔线
        result.append("| " + " | ".join(["---"] * len(headers)) + " |")
        # 数据行
        for row in data:
            result.append("| " + " | ".join(row) + " |")
        return "\n".join(result)
    else:
        # 创建"漂亮"表格
        col_widths = [
            max(len(h), max([len(row[i]) for row in data] or [0]))
            for i, h in enumerate(headers)
        ]

        result = []
        # 表头
        header_line = (
            "| " + " | ".join(h.ljust(w) for h, w in zip(headers, col_widths)) + " |"
        )
        result.append("-" * len(header_line))
        result.append(header_line)
        result.append("-" * len(header_line))

        # 数据行
        for row in data:
            padded_row = [cell.ljust(width) for cell, width in zip(row, col_widths)]
            result.append("| " + " | ".join(padded_row) + " |")

        result.append("-" * len(header_line))
        return "\n".join(result)


def safe_html_parse(html: str, default_value: Any = None) -> Any:
    """
    安全地解析HTML，出错时返回默认值

    Args:
        html: HTML内容
        default_value: 出错时返回的默认值

    Returns:
        解析结果或默认值
    """
    try:
        headers, data = extract_table_data(html)
        return headers, data
    except Exception as e:
        logger.error(f"解析HTML时出错: {str(e)}")
        return default_value

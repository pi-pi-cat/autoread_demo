#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主题浏览模块

负责主题列表获取、浏览和点赞功能
"""

import time
import random
from typing import List, Tuple, Dict, Any, Optional
from loguru import logger

from config import (
    HOME_URL,
    PAGE_URL,
    MAX_SCROLL_TIMES,
    SCROLL_DISTANCE_MIN,
    SCROLL_DISTANCE_MAX,
    SCROLL_WAIT_MIN,
    SCROLL_WAIT_MAX,
    LIKE_PROBABILITY,
)
from utils.decorators import retry, log_entry_exit
from core.browser import browser_manager
from utils.html_parser import extract_links


class TopicBrowser:
    """主题浏览器，负责浏览帖子和点赞功能"""

    def __init__(self):
        """初始化主题浏览器"""
        self.visited_topics = set()  # 已访问的主题ID集合

    @log_entry_exit()
    @retry(retries=3, delay=2)
    def browse_topics(self, max_topics: int = 5) -> int:
        """
        浏览主题列表

        Args:
            max_topics: 最多浏览的主题数量

        Returns:
            int: 成功浏览的主题数量
        """
        # 切换到最新主题页面
        browser_manager.navigate(PAGE_URL, "main", wait_time=3.0)

        logger.info("开始获取主题列表")

        # 尝试各种选择器策略获取主题列表
        topic_links = []

        # 尝试使用主选择器策略
        topic_links = self._get_topics_with_primary_selector()

        # 如果主选择器没有获取到主题，尝试备用选择器
        if not topic_links:
            topic_links = self._get_topics_with_backup_selectors()

        # 如果仍然没有获取到主题，尝试最后的备用方法
        if not topic_links:
            topic_links = self._get_topics_with_fallback_method()

        # 浏览收集到的主题
        visited_count = 0
        for href, title in topic_links[:max_topics]:
            try:
                logger.info(f"开始访问主题: {title}")
                if self.visit_topic(href):
                    visited_count += 1
            except Exception as e:
                logger.error(f"访问主题 '{title}' 时出错: {str(e)}")

        return visited_count

    def _get_topics_with_primary_selector(self) -> List[Tuple[str, str]]:
        """
        使用主选择器获取主题列表

        Returns:
            List[Tuple[str, str]]: (href, title)元组列表
        """
        topic_links = []

        try:
            # 使用XPath获取表格行(主题帖)
            topic_rows = browser_manager.find_elements(
                'xpath://*[@id="ember57"]/table/tbody/tr'
            )
            logger.info(f"主选择器发现 {len(topic_rows)} 个主题帖")

            if topic_rows:
                # 收集主题链接
                for row in topic_rows:
                    try:
                        # 尝试不同的选择器查找链接元素
                        link = None
                        for selector in ["xpath:./td[1]/span/a", "a.title", "a"]:
                            try:
                                if selector.startswith("xpath:"):
                                    link = row.ele(selector)
                                else:
                                    link = row.ele(selector)
                                if link:
                                    break
                            except:
                                continue

                        if link:
                            href = link.attr("href")
                            topic_title = link.text
                            if href:
                                logger.info(f"找到主题: {topic_title}, 链接: {href}")
                                topic_links.append((href, topic_title))
                            else:
                                logger.warning(f"主题 '{topic_title}' 没有链接属性")
                        else:
                            logger.warning("行内未找到链接元素")
                    except Exception as e:
                        logger.error(f"处理主题行时出错: {str(e)}")
                        continue
        except Exception as e:
            logger.error(f"使用主选择器获取主题列表时出错: {str(e)}")

        return topic_links

    def _get_topics_with_backup_selectors(self) -> List[Tuple[str, str]]:
        """
        使用备用选择器获取主题列表

        Returns:
            List[Tuple[str, str]]: (href, title)元组列表
        """
        topic_links = []

        try:
            # 备用方法1：使用表格内通用选择器
            logger.warning("未找到主题帖，尝试使用备用选择器")
            topic_rows = browser_manager.find_elements("table tbody tr")
            logger.info(f"备用选择器1找到 {len(topic_rows)} 个主题帖")

            if topic_rows:
                # 使用与主选择器相同的处理逻辑
                for row in topic_rows:
                    try:
                        # 尝试不同的选择器查找链接元素
                        link = None
                        for selector in ["xpath:./td[1]/span/a", "a.title", "a"]:
                            try:
                                if selector.startswith("xpath:"):
                                    link = row.ele(selector)
                                else:
                                    link = row.ele(selector)
                                if link:
                                    break
                            except:
                                continue

                        if link:
                            href = link.attr("href")
                            topic_title = link.text
                            if href:
                                logger.info(f"找到主题: {topic_title}, 链接: {href}")
                                topic_links.append((href, topic_title))
                    except Exception as e:
                        logger.error(f"处理主题行时出错: {str(e)}")
                        continue
            else:
                # 备用方法2：使用.raw-topic-link类选择器
                logger.warning("备用选择器1仍未找到主题帖，尝试使用备用选择器2")
                links = browser_manager.find_elements("a.raw-topic-link")
                logger.info(f"备用选择器2找到 {len(links)} 个主题链接")

                # 处理找到的链接
                for link in links:
                    try:
                        href = link.attr("href")
                        topic_title = link.text
                        if href:
                            logger.info(f"找到主题: {topic_title}, 链接: {href}")
                            topic_links.append((href, topic_title))
                    except Exception as e:
                        logger.error(f"处理链接时出错: {str(e)}")
                        continue
        except Exception as e:
            logger.error(f"使用备用选择器获取主题列表时出错: {str(e)}")

        return topic_links

    def _get_topics_with_fallback_method(self) -> List[Tuple[str, str]]:
        """
        使用最后的备用方法获取主题列表

        Returns:
            List[Tuple[str, str]]: (href, title)元组列表
        """
        topic_links = []

        try:
            # 尝试使用CSS选择器
            logger.warning("所有选择器策略失败，尝试使用最后的备用方法")
            links = browser_manager.find_elements("a[data-topic-id]")
            logger.info(f"最后的备用方法找到 {len(links)} 个主题链接")

            # 处理找到的链接
            for link in links:
                try:
                    href = link.attr("href")
                    topic_title = link.text
                    if href:
                        logger.info(f"找到主题: {topic_title}, 链接: {href}")
                        topic_links.append((href, topic_title))
                except Exception as e:
                    logger.error(f"处理链接时出错: {str(e)}")
                    continue

            # 如果仍然没有找到链接，尝试从HTML中提取
            if not topic_links:
                logger.warning("所有选择器都失败，尝试从HTML中提取链接")
                html = browser_manager.get_page_source()
                extracted_links = extract_links(html)

                for link_info in extracted_links:
                    href = link_info.get("href", "")
                    text = link_info.get("text", "")

                    # 过滤一些无关链接
                    if href and text and "login" not in href and "register" not in href:
                        topic_links.append((href, text))

                logger.info(f"从HTML中提取到 {len(topic_links)} 个链接")
        except Exception as e:
            logger.error(f"使用最后的备用方法获取主题列表时出错: {str(e)}")

        return topic_links

    @retry(retries=2, delay=2)
    def visit_topic(self, topic_url: str) -> bool:
        """
        访问并浏览单个主题

        Args:
            topic_url: 主题URL

        Returns:
            bool: 是否成功浏览
        """
        # 生成唯一的页面ID
        page_id = f"topic_{len(self.visited_topics)}"

        # 记录此主题已访问
        self.visited_topics.add(topic_url)

        try:
            # 创建新页面并导航
            browser_manager.create_page(page_id)

            # 构建完整URL并访问
            full_url = (
                HOME_URL + topic_url if not topic_url.startswith("http") else topic_url
            )
            if not browser_manager.navigate(full_url, page_id, wait_time=2.0):
                logger.error(f"导航到主题失败: {full_url}")
                return False

            # 随机决定是否点赞
            if random.random() < LIKE_PROBABILITY:
                self._like_post(page_id)

            # 浏览帖子内容
            self._scroll_and_read(page_id)

            return True
        except Exception as e:
            logger.error(f"访问主题时出错: {str(e)}")
            return False
        finally:
            # 确保关闭页面
            browser_manager.close_page(page_id)

    def _scroll_and_read(self, page_id: str) -> None:
        """
        浏览帖子内容，模拟滚动和阅读

        Args:
            page_id: 页面ID
        """
        prev_url = None

        # 开始自动滚动
        for scroll_count in range(MAX_SCROLL_TIMES):
            # 随机滚动一段距离
            scroll_distance = random.randint(SCROLL_DISTANCE_MIN, SCROLL_DISTANCE_MAX)
            logger.info(f"向下滚动 {scroll_distance} 像素...")

            if not browser_manager.scroll_page(scroll_distance, page_id):
                logger.warning("滚动失败，中断浏览")
                break

            # 获取当前页面
            page = browser_manager.get_page(page_id)
            if not page:
                logger.warning("页面已关闭，中断浏览")
                break

            logger.info(f"已加载页面: {page.url}")

            # 随机决定是否提前退出
            if random.random() < 0.1:  # 10%的概率提前退出
                logger.success("随机退出浏览")
                break

            # 检查是否到达页面底部
            at_bottom = browser_manager.is_bottom_of_page(page_id)
            current_url = page.url

            if current_url != prev_url:
                prev_url = current_url
            elif at_bottom and prev_url == current_url:
                logger.success("已到达页面底部，退出浏览")
                break

            # 动态随机等待
            wait_time = random.uniform(SCROLL_WAIT_MIN, SCROLL_WAIT_MAX)
            logger.info(f"等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)

    def _like_post(self, page_id: str) -> bool:
        """
        尝试对帖子进行点赞

        Args:
            page_id: 页面ID

        Returns:
            bool: 是否成功点赞
        """
        try:
            logger.info("尝试寻找点赞按钮")

            # 查找所有包含"点赞此帖子"的元素
            like_candidates = browser_manager.find_elements(
                'xpath://*[contains(@title, "点赞此帖子")]', page_id
            )

            if like_candidates:
                logger.info(f"找到 {len(like_candidates)} 个候选点赞元素")

                # 尝试点击第一个可见的点赞按钮
                for button in like_candidates:
                    try:
                        logger.info("找到未点赞的帖子，准备点赞")
                        button.click()
                        logger.info("点赞成功")
                        time.sleep(random.uniform(1, 2))
                        return True
                    except Exception:
                        continue

                logger.info("所有点赞按钮尝试失败")
            else:
                logger.info(
                    "未找到可点击的点赞按钮，可能帖子已点过赞或者按钮结构已变化"
                )

        except Exception as e:
            logger.error(f"点赞失败: {str(e)}")

            # 获取页面HTML用于调试
            try:
                html = browser_manager.get_page_source(page_id)
                logger.debug(f"页面源码片段: {html[:500]}...")
            except:
                pass

        return False


# 创建主题浏览器实例
topic_browser = TopicBrowser()

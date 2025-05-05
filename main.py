#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Linux.Do 自动签到脚本 (DrissionPage版)

自动完成Linux.Do的每日登录、浏览和点赞任务，并支持多种通知方式。

功能：
- 自动登录Linux.Do
- 自动浏览帖子
- 随机点赞部分帖子
- 获取连接信息
- 支持通知推送(Gotify、Server酱³)

cron: 0 */6 * * *
"""

import os
import sys
import time
import argparse
from typing import Dict, Any
from loguru import logger

# 导入配置和工具模块
from config import (
    get_config,
    load_config,
    create_default_config,
    LOG_LEVEL,
    LOG_FORMAT,
    NOTIFICATION_SUCCESS_PREFIX,
    MAX_TOPICS,
)
from utils import setup_notifications, notification_manager
from core import (
    browser_manager,
    create_login_manager,
    topic_browser,
    connect_info_manager,
)


def configure_logger():
    """
    配置日志记录器
    """
    # 移除默认处理程序
    logger.remove()

    # 添加控制台处理程序
    logger.add(sys.stderr, level=LOG_LEVEL, format=LOG_FORMAT)

    # 添加文件处理程序
    log_file = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "linuxdo-autoread.log"
    )
    logger.add(
        log_file,
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        rotation="10 MB",  # 当日志文件达到10MB时轮转
        retention="7 days",  # 保留7天的日志
    )


def parse_arguments():
    """
    解析命令行参数

    Returns:
        argparse.Namespace: 解析后的参数
    """
    parser = argparse.ArgumentParser(description="Linux.Do 自动签到脚本")

    parser.add_argument(
        "-c", "--config", help="配置文件路径，默认为当前目录下的config.json"
    )

    parser.add_argument(
        "--create-config", action="store_true", help="创建默认配置文件并退出"
    )

    parser.add_argument(
        "--no-browse", action="store_true", help="不执行浏览功能，仅进行签到"
    )

    parser.add_argument(
        "--debug", action="store_true", help="启用调试模式，显示更详细的日志"
    )

    return parser.parse_args()


def run(config: Dict[str, Any]):
    """
    执行自动签到任务

    Args:
        config: 配置字典
    """
    try:
        # 获取关键配置项
        username = config.get("username")
        password = config.get("password")
        browse_enabled = config.get("browse_enabled", True)
        max_topics = config.get(
            "max_topics", 5
        )  # 从配置中获取每次浏览的主题数量，默认为5

        # 命令行参数可以覆盖配置
        if args.no_browse:
            browse_enabled = False

        # 检查必要的配置
        if not username or not password:
            logger.error("配置中未提供用户名或密码")
            sys.exit(1)

        # 显示启动信息
        logger.info("开始运行 Linux.Do 签到脚本 (DrissionPage版)")
        logger.info(f"账户: {username}")
        logger.info(f"浏览功能: {'启用' if browse_enabled else '禁用'}")
        if browse_enabled:
            logger.info(f"浏览主题数: {max_topics}")

        # 设置通知
        setup_notifications(config)

        # 创建登录管理器
        login_manager = create_login_manager(config)

        # 执行登录
        if not login_manager.login():
            logger.error("登录失败，程序终止")
            sys.exit(1)

        # 获取连接信息(登录前)
        logger.info("获取签到前的连接信息")
        connect_info_manager.get_connect_info(is_after=False)

        # 浏览帖子
        if browse_enabled:
            logger.info("开始浏览帖子任务")
            visited_count = topic_browser.browse_topics(max_topics=max_topics)
            logger.info(f"完成浏览，共访问 {visited_count} 个主题")
        else:
            logger.info("浏览功能已禁用，跳过浏览任务")

        # 再次获取连接信息(完成任务后)
        logger.info("获取签到后的连接信息")
        connect_info_manager.get_connect_info(is_after=True)

        # 显示前后对比信息
        logger.info("显示连接信息对比")
        connect_info_manager.display_compare_info()

        # 获取HTML格式的对比表格
        html_compare_table = connect_info_manager.get_compare_info_html()

        # 发送通知
        notification_message = NOTIFICATION_SUCCESS_PREFIX
        if browse_enabled:
            notification_message += " + 浏览任务完成"

        # 发送普通文本通知
        notification_manager.send_all(notification_message)

        # 设置环境变量，供GitHub Actions使用
        if "GITHUB_ENV" in os.environ:
            try:
                with open(os.environ["GITHUB_ENV"], "a") as f:
                    f.write(f"LINUXDO_COMPARE_TABLE<<EOF\n{html_compare_table}\nEOF\n")
                logger.info("已将连接信息对比表格写入GitHub Actions环境变量")
            except Exception as e:
                logger.error(f"写入GitHub环境变量失败: {str(e)}")

        logger.success("所有任务完成")
    finally:
        # 确保关闭所有浏览器页面
        browser_manager.close_all_pages()


if __name__ == "__main__":
    # 解析命令行参数
    args = parse_arguments()

    # 配置日志记录器
    if args.debug:
        logger.remove()
        logger.add(sys.stderr, level="DEBUG")
    else:
        configure_logger()

    # 创建默认配置文件并退出
    if args.create_config:
        create_default_config(args.config or "config.json")
        sys.exit(0)

    try:
        # 加载配置
        config = load_config(args.config)

        # 执行主程序
        run(config)
    except KeyboardInterrupt:
        logger.warning("用户中断，退出程序")
        # 确保关闭所有浏览器页面
        browser_manager.close_all_pages()
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        import traceback

        logger.debug(f"错误详情: {traceback.format_exc()}")
        # 确保关闭所有浏览器页面
        browser_manager.close_all_pages()
        sys.exit(1)

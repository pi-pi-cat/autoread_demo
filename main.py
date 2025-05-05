"""
cron: 0 */6 * * *
new Env("Linux.Do 签到-DrissionPage版")
"""

import os
import sys
import time
import random
import functools
import re
import requests
from loguru import logger
from DrissionPage import ChromiumPage
from tabulate import tabulate


def retry_decorator(retries=3):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == retries - 1:  # 最后一次尝试
                        logger.error(f"函数 {func.__name__} 最终执行失败: {str(e)}")
                    logger.warning(
                        f"函数 {func.__name__} 第 {attempt + 1}/{retries} 次尝试失败: {str(e)}"
                    )
                    time.sleep(1)
            return None

        return wrapper

    return decorator


# 环境变量配置
USERNAME = os.environ.get("LINUXDO_USERNAME")
PASSWORD = os.environ.get("LINUXDO_PASSWORD")
BROWSE_ENABLED = os.environ.get("BROWSE_ENABLED", "true").strip().lower() not in [
    "false",
    "0",
    "off",
]
if not USERNAME:
    USERNAME = os.environ.get("BACKUP_USERNAME")
if not PASSWORD:
    PASSWORD = os.environ.get("BACKUP_PASSWORD")
GOTIFY_URL = os.environ.get("GOTIFY_URL")  # Gotify 服务器地址
GOTIFY_TOKEN = os.environ.get("GOTIFY_TOKEN")  # Gotify 应用的 API Token
SC3_PUSH_KEY = os.environ.get("SC3_PUSH_KEY")  # Server酱³ SendKey

# 网站URL
HOME_URL = "https://linux.do/"
PAGE_URL = "https://linux.do/new"
LOGIN_URL = "https://linux.do/login"


class LinuxDoChat:
    def __init__(self):
        # 初始化DrissionPage
        self.page = ChromiumPage()
        logger.info("初始化DrissionPage成功")

    def open_login_page(self):
        """打开登录页面"""
        logger.info("正在打开登录页面...")
        self.page.get(LOGIN_URL)
        logger.info(f"已打开登录页面: {self.page.url}")
        return self.page.url == LOGIN_URL

    @retry_decorator()
    def login(self):
        """登录功能，支持已登录状态检测"""
        logger.info("开始检查登录状态")

        # 先访问首页检查登录状态
        self.page.get(HOME_URL)
        time.sleep(2)

        # 检查是否已经登录
        user_ele = self.page.ele("#current-user", timeout=3)
        if user_ele:
            logger.success("已处于登录状态，无需重新登录")
            return True

        logger.info("未登录，开始登录流程")
        self.page.get(LOGIN_URL)
        time.sleep(2)

        # 判断是否成功打开登录页面
        login_form = self.page.ele("#login-form", timeout=3)
        if not login_form:
            logger.error("打开登录页面失败")
            return False

        try:
            # 填写用户名
            self.page.ele("#login-account-name").input(USERNAME)
            time.sleep(1)

            # 填写密码
            self.page.ele("#login-account-password").input(PASSWORD)
            time.sleep(1)

            # 点击登录按钮
            self.page.ele("#login-button").click()

            # 等待登录完成
            time.sleep(5)

            # 验证登录状态
            user_ele = self.page.ele("#current-user", timeout=5)
            if user_ele:
                logger.success("登录成功")
                return True
            else:
                logger.error("登录失败")
                return False
        except Exception as e:
            logger.error(f"登录过程中发生错误: {str(e)}")
            return False

    @retry_decorator()
    def click_topic(self):
        """点击浏览主题列表"""
        # 切换到最新主题页面
        self.page.get(PAGE_URL)
        time.sleep(3)

        logger.info("开始获取主题列表")

        try:
            # 使用XPath获取表格行(主题帖)
            topic_rows = self.page.eles('xpath://*[@id="ember57"]/table/tbody/tr')
            logger.info(f"发现 {len(topic_rows)} 个主题帖")

            # 如果没有找到主题，尝试备用方法
            if len(topic_rows) == 0:
                logger.warning("未找到主题帖，尝试使用备用选择器")
                # 备用方法1：使用表格内通用选择器
                topic_rows = self.page.eles("table tbody tr")
                logger.info(f"备用选择器1找到 {len(topic_rows)} 个主题帖")

                # 如果仍然没有找到，使用第二个备用方法
                if len(topic_rows) == 0:
                    logger.warning("备用选择器1仍未找到主题帖，尝试使用备用选择器2")
                    # 备用方法2：使用.raw-topic-link类选择器
                    topic_links = self.page.eles("a.raw-topic-link")
                    logger.info(f"备用选择器2找到 {len(topic_links)} 个主题链接")

                    # 处理找到的链接
                    for link in topic_links:
                        href = link.attr("href")
                        if href:
                            logger.info(f"找到主题链接: {href}")
                            self.click_one_topic(href)
                    return

            # 先收集所有主题链接
            topic_links = []
            for row in topic_rows:
                try:
                    # 找到每行中的链接元素
                    link = row.ele("xpath:./td[1]/span/a")
                    if not link:
                        # 备用方法
                        link = row.ele("a.title") or row.ele("a")

                    if link:
                        href = link.attr("href")
                        topic_title = link.text
                        if href:
                            logger.info(f"找到主题: {topic_title}, 链接: {href}")
                            topic_links.append((href, topic_title))
                        else:
                            logger.warning(f"主题 '{topic_title}' 没有链接属性")
                    else:
                        logger.warning(f"行内未找到链接元素: {row.html}")
                except Exception as e:
                    logger.error(f"处理主题行时出错: {str(e)}")
                    continue

            # 遍历收集到的链接进行访问
            for href, topic_title in topic_links:
                try:
                    logger.info(f"开始访问主题: {topic_title}")
                    self.click_one_topic(href)
                except Exception as e:
                    logger.error(f"访问主题 '{topic_title}' 时出错: {str(e)}")

        except Exception as e:
            logger.error(f"获取主题列表时出错: {str(e)}")
            # 尝试最后的备用方法：使用CSS选择器
            try:
                logger.info("尝试使用CSS选择器获取主题链接")
                links = self.page.eles("a[data-topic-id]")
                logger.info(f"CSS选择器找到 {len(links)} 个主题链接")
                for link in links:
                    href = link.attr("href")
                    if href:
                        self.click_one_topic(href)
            except Exception as e2:
                logger.error(f"备用方法也失败: {str(e2)}")

    @retry_decorator()
    def click_one_topic(self, topic_url):
        """点击并浏览单个主题"""
        # 创建新页面
        new_page = ChromiumPage()
        full_url = (
            HOME_URL + topic_url if not topic_url.startswith("http") else topic_url
        )

        # 打开主题页
        new_page.get(full_url)
        logger.info(f"打开主题: {full_url}")
        time.sleep(2)

        # 随机决定是否点赞
        if random.random() < 0.3:  # 0.3的概率点赞
            self.click_like(new_page)

        # 浏览帖子内容
        self.browse_post(new_page)

        # 关闭页面
        try:
            logger.info("关闭主题页面")
            new_page.quit()
        except Exception as e:
            logger.warning(f"关闭页面失败: {str(e)}")

    def browse_post(self, page):
        """浏览帖子内容，模拟滚动和阅读"""
        prev_url = None

        # 开始自动滚动，最多滚动10次
        for _ in range(10):
            # 随机滚动一段距离
            scroll_distance = random.randint(550, 650)  # 随机滚动 550-650 像素
            logger.info(f"向下滚动 {scroll_distance} 像素...")
            page.run_js(f"window.scrollBy(0, {scroll_distance})")
            logger.info(f"已加载页面: {page.url}")

            # 随机决定是否提前退出
            if random.random() < 0.1:  # 3%的概率提前退出
                logger.success("随机退出浏览")
                break

            # 检查是否到达页面底部
            at_bottom = page.run_js(
                "return window.scrollY + window.innerHeight >= document.body.scrollHeight"
            )
            current_url = page.url

            if current_url != prev_url:
                prev_url = current_url
            elif at_bottom and prev_url == current_url:
                logger.success("已到达页面底部，退出浏览")
                break

            # 动态随机等待
            wait_time = random.uniform(2, 4)  # 随机等待 2-4 秒
            logger.info(f"等待 {wait_time:.2f} 秒...")
            time.sleep(wait_time)

    def click_like(self, page):
        """尝试对帖子进行点赞"""
        try:
            logger.info("尝试寻找点赞按钮")
            like_button = None

            # 策：最后尝试使用XPath通配符查找所有可能的点赞按钮
            if not like_button:
                # 查找所有包含"点赞此帖子"的元素
                candidates = page.eles('xpath://*[contains(@title, "点赞此帖子")]')
                if candidates:
                    logger.info(f"找到 {len(candidates)} 个候选点赞元素 (策略4)")
                    for btn in candidates:
                        try:
                            # 直接使用找到的元素
                            like_button = btn
                            logger.info("找到可见的点赞元素 (策略4)")
                            break
                        except:
                            continue

            # 点击找到的按钮
            if like_button:
                logger.info("找到未点赞的帖子，准备点赞")

                # 点击按钮
                like_button.click()
                logger.info("点赞成功")
                time.sleep(random.uniform(1, 2))
            else:
                logger.info(
                    "未找到可点击的点赞按钮，可能帖子已点过赞或者按钮结构已变化"
                )

        except Exception as e:
            logger.error(f"点赞失败: {str(e)}")
            logger.debug(f"页面源码片段: {page.html[:500]}...")

    @retry_decorator()
    def print_connect_info(self):
        """获取并打印连接信息"""
        logger.info("获取连接信息")

        try:
            # 创建新页面
            connect_page = ChromiumPage()
            connect_page.get("https://connect.linux.do/")

            # 等待页面加载
            time.sleep(3)
            logger.info(f"页面标题: {connect_page.title}")

            # 获取页面源码
            page_html = connect_page.html

            # 使用正则表达式直接提取表格内容
            import re

            # 寻找表格
            table_pattern = re.compile(r"<table>(.*?)</table>", re.DOTALL)
            table_match = table_pattern.search(page_html)

            if not table_match:
                logger.error("未找到连接信息表格")
                connect_page.quit()
                return

            table_html = table_match.group(1)
            logger.info("找到表格HTML，开始解析")

            # 提取所有表格行
            tr_pattern = re.compile(r"<tr>(.*?)</tr>", re.DOTALL)
            rows = tr_pattern.findall(table_html)

            if not rows:
                logger.error("没有找到表格行")
                connect_page.quit()
                return

            logger.info(f"找到 {len(rows)} 行表格数据")

            # 提取表头(第一行)
            td_th_pattern = re.compile(r"<t[hd][^>]*>(.*?)</t[hd]>", re.DOTALL)
            header_cells = td_th_pattern.findall(rows[0])

            # 清理HTML标签
            clean_html = lambda text: re.sub(r"<.*?>", "", text).strip()

            headers = [clean_html(cell) for cell in header_cells]
            if not headers or len(headers) < 3:
                headers = ["项目", "当前", "要求"]

            # 提取数据行
            info = []
            for row in rows[1:]:  # 跳过表头
                cells = td_th_pattern.findall(row)
                if cells:
                    # 清理每个单元格的HTML和空白
                    row_data = [clean_html(cell) for cell in cells]

                    # 确保至少有3列
                    while len(row_data) < 3:
                        row_data.append("")

                    # 只取前3列
                    info.append(row_data[:3])

            # 打印表格数据
            if info:
                print("--------------Connect Info-----------------")
                print(tabulate(info, headers=headers[:3], tablefmt="pretty"))

                # 将信息记录到日志
                for item in info:
                    logger.info(f"连接信息: {', '.join(item)}")
            else:
                logger.warning("解析到表格，但没有数据行")
                # 直接输出表格文本
                table_text = re.sub(r"<.*?>", " ", table_html).strip()
                table_text = re.sub(r"\s+", " ", table_text)
                print("--------------Connect Info (Raw Text)-----------------")
                print(table_text)

        except Exception as e:
            logger.error(f"获取连接信息时出错: {str(e)}")
            import traceback

            logger.debug(f"错误详情: {traceback.format_exc()}")

    def send_notifications(self, browse_enabled):
        """发送通知到Gotify和Server酱"""
        status_msg = "✅每日登录成功"
        if browse_enabled:
            status_msg += " + 浏览任务完成"

        # Gotify通知
        if GOTIFY_URL and GOTIFY_TOKEN:
            try:
                response = requests.post(
                    f"{GOTIFY_URL}/message",
                    params={"token": GOTIFY_TOKEN},
                    json={"title": "LINUX DO", "message": status_msg, "priority": 1},
                    timeout=10,
                )
                response.raise_for_status()
                logger.success("消息已推送至Gotify")
            except Exception as e:
                logger.error(f"Gotify推送失败: {str(e)}")
        else:
            logger.info("未配置Gotify环境变量，跳过通知发送")

        # Server酱通知
        if SC3_PUSH_KEY:
            match = re.match(r"sct(\d+)t", SC3_PUSH_KEY, re.I)
            if not match:
                logger.error(
                    "❌ SC3_PUSH_KEY格式错误，未获取到UID，无法使用Server酱³推送"
                )
                return

            uid = match.group(1)
            url = f"https://{uid}.push.ft07.com/send/{SC3_PUSH_KEY}"
            params = {"title": "LINUX DO", "desp": status_msg}

            attempts = 5
            for attempt in range(attempts):
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    logger.success(f"Server酱³推送成功: {response.text}")
                    break
                except Exception as e:
                    logger.error(f"Server酱³推送失败: {str(e)}")
                    if attempt < attempts - 1:
                        sleep_time = random.randint(180, 360)
                        logger.info(f"将在 {sleep_time} 秒后重试...")
                        time.sleep(sleep_time)

    def run(self):
        """运行主程序，整合所有功能"""
        # 登录
        login_result = self.login()
        if not login_result:
            logger.error("登录失败，程序终止")
            sys.exit(1)

        self.print_connect_info()

        # 浏览帖子
        if BROWSE_ENABLED:
            self.click_topic()  # 浏览主题列表
            logger.info("完成浏览任务")

        # 打印连接信息
        self.print_connect_info()

        # 发送通知
        self.send_notifications(BROWSE_ENABLED)

        logger.success("所有任务完成")

        # 关闭浏览器
        self.page.quit()


if __name__ == "__main__":
    try:
        if not USERNAME or not PASSWORD:
            logger.error("请设置USERNAME和PASSWORD环境变量")
            sys.exit(1)

        logger.info(f"开始运行 Linux.Do 签到脚本 (DrissionPage版)")
        logger.info(f"账户: {USERNAME}")
        logger.info(f"浏览功能: {'启用' if BROWSE_ENABLED else '禁用'}")

        linux_do = LinuxDoChat()
        linux_do.run()
    except KeyboardInterrupt:
        logger.warning("用户中断，退出程序")
        sys.exit(0)
    except Exception as e:
        logger.error(f"程序运行出错: {str(e)}")
        sys.exit(1)

import os
import time
import random
import argparse
from tabulate import tabulate
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from dotenv import load_dotenv


# 加载 .env 文件中的环境变量
load_dotenv()


USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")
HOME_URL = os.environ.get("HOME_URL", "https://linux.do/")
HEADLESS = os.environ.get("HEADLESS", "True").lower() == "true"
WAIT_TIME = float(os.environ.get("WAIT_TIME", 2))
SCROLL_COUNT = int(os.environ.get("SCROLL_COUNT", 10))
SCROLL_STEP_MIN = int(os.environ.get("SCROLL_STEP_MIN", 1000))
SCROLL_STEP_MAX = int(os.environ.get("SCROLL_STEP_MAX", 1300))
LIKE_PROBABILITY = float(os.environ.get("LIKE_PROBABILITY", 0.01))
CONNECT_INFO_URL = os.environ.get("CONNECT_INFO_URL", "https://connect.linux.do/")


class LinuxDoBrowser:
    def __init__(self, headless=HEADLESS, wait_time=WAIT_TIME) -> None:
        try:
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(headless=headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.wait_time = wait_time
            print("正在打开主页...")
            self.page.goto(HOME_URL)
        except Exception as e:
            print(f"初始化失败: {e}")
            raise

    def login(self):
        try:
            print("正在登录...")
            self.page.click(".login-button .d-button-label")
            self.page.fill("#login-account-name", USERNAME)
            self.page.fill("#login-account-password", PASSWORD)
            self.page.click("#login-button")
            self.page.wait_for_selector("#current-user", timeout=10000)
            if self.page.query_selector("#current-user"):
                print("登录成功")
                return True
            else:
                print("登录失败")
                return False
        except PlaywrightTimeoutError:
            print("登录超时")
            return False
        except Exception as e:
            print(f"登录过程中发生错误: {e}")
            return False

    def click_topic(self):
        print("正在浏览主题...")
        try:
            # 向下滚动、
            for i in range(SCROLL_COUNT):
                print(f"正在滚动第 {i + 1}/{SCROLL_COUNT} 次")
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(1, 5))  # 在底部稍作停留

            topics = self.page.query_selector_all("#list-area .title")

            # 用于记录已访问的主题
            visited_topics = set()

            for i, topic in enumerate(topics, 1):
                try:
                    topic_url = HOME_URL + topic.get_attribute("href")

                    # 如果主题已经访问过，跳过
                    if topic_url in visited_topics:
                        print(f"跳过已访问的主题 {i}/{len(topics)}")
                        continue

                    print(f"正在浏览第 {i}/{len(topics)} 个主题")
                    page = self.context.new_page()
                    page.goto(topic_url)

                    # 将主题标记为已访问
                    visited_topics.add(topic_url)

                    # 用于记录已处理的元素
                    processed_elements = set()

                    # 尝试多次滑动到顶部，以确保在动态加载的情况下也能到达顶部
                    for _ in range(3):  # 尝试最多3次
                        page.evaluate("window.scrollTo(0, 0)")
                        time.sleep(0.5)  # 等待一小段时间，让页面有机会加载
                        current_scroll = page.evaluate("window.pageYOffset")
                        if current_scroll == 0:
                            break  # 如果已经到达顶部，就退出循环
                    # 模拟用户慢慢下拉
                    total_height = page.evaluate("document.body.scrollHeight")
                    current_position = 0
                    scroll_step = random.randint(
                        SCROLL_STEP_MIN, SCROLL_STEP_MAX
                    )  # 每次滚动的像素数

                    while current_position < total_height:
                        try:
                            scroll_amount = min(
                                scroll_step, total_height - current_position
                            )
                            self.smooth_scroll(page, scroll_amount)
                            current_position += scroll_amount

                            # 获取当前页面内的所有点赞计数器
                            like_counters = page.query_selector_all(
                                "div.discourse-reactions-double-button"
                            )

                            for counter in like_counters:
                                try:
                                    # 获取元素的唯一标识符
                                    element_id = counter.query_selector(
                                        ".only-like.discourse-reactions-counter"
                                    ).get_attribute("id")

                                    # 如果这个元素还没有被处理过
                                    if element_id not in processed_elements:
                                        like_count = int(counter.inner_text())
                                        if random.random() < LIKE_PROBABILITY:
                                            # TODO 检查元素是否在视口内
                                            # 找到对应的点赞按钮并点击
                                            like_button = counter.query_selector(
                                                ".discourse-reactions-reaction-button"
                                            )
                                            if like_button:
                                                like_button.click()
                                                print(f"点赞成功，点赞数：{like_count}")
                                                time.sleep(random.uniform(2.5, 5.5))

                                    # 将元素添加到已处理集合中
                                    processed_elements.add(element_id)

                                except Exception as e:
                                    print(f"处理点赞按钮时发生错误: {e}")

                            # 随机等待一小段时间，模拟人类阅读行为
                            time.sleep(random.uniform(1, 10))

                        except Exception as e:
                            print(f"滚动过程中发生错误: {e}")

                    # 确保滚动到底部
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(1, 5))  # 在底部稍作停留

                    page.close()

                except Exception as e:
                    print(f"处理主题 {i} 时发生错误: {e}")
                finally:
                    try:
                        page.close()
                    except:
                        pass

            # 保存已访问的主题，以便下次运行时使用
            self.save_visited_topics(visited_topics)

        except Exception as e:
            print(f"浏览主题过程中发生错误: {e}")

    def save_visited_topics(self, visited_topics):
        with open("visited_topics.txt", "w") as f:
            for topic in visited_topics:
                f.write(f"{topic}\n")

    def load_visited_topics(self):
        visited_topics = set()
        if os.path.exists("visited_topics.txt"):
            with open("visited_topics.txt", "r") as f:
                for line in f:
                    visited_topics.add(line.strip())
        return visited_topics

    def run(self):
        try:
            if not self.login():
                return
            self.click_topic()
            self.print_connect_info()
            print("任务完成")
        except Exception as e:
            print(f"运行过程中发生错误: {e}")
        finally:
            try:
                self.browser.close()
                self.pw.stop()
            except:
                pass

    def click_like(self, page):
        page.locator(".discourse-reactions-reaction-button").first.click()
        print("Like success")

    def print_connect_info(self):
        print("正在获取连接信息...")
        page = self.context.new_page()
        page.goto(CONNECT_INFO_URL)
        rows = page.query_selector_all("table tr")

        info = []

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 3:
                project = cells[0].text_content().strip()
                current = cells[1].text_content().strip()
                requirement = cells[2].text_content().strip()
                info.append([project, current, requirement])

        print("--------------Connect Info-----------------")
        print(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="pretty"))

        page.close()

    def smooth_scroll(self, page, scroll_amount):
        steps = random.randint(5, 15)  # 将滚动分成5到15个小步骤
        delay = random.uniform(0.1, 0.3)  # 每个步骤之间的延迟
        step_size = scroll_amount / steps

        for _ in range(steps):
            actual_step = step_size + random.uniform(-10, 10)  # 添加一些随机性
            page.evaluate(f"window.scrollBy(0, {actual_step})")
            time.sleep(delay)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LinuxDo Browser Automation")
    parser.add_argument("--visible", action="store_true", help="Run in visible mode")
    parser.add_argument(
        "--wait-time", type=float, default=WAIT_TIME, help="Wait time between actions"
    )
    args = parser.parse_args()

    if not USERNAME or not PASSWORD:
        print("请在 .env 文件中设置 LINUXDO_USERNAME 和 LINUXDO_PASSWORD")
        exit(1)

    try:
        l = LinuxDoBrowser(headless=not args.visible, wait_time=args.wait_time)
        l.run()
    except Exception as e:
        print(f"程序运行失败: {e}")

import os
import time
import random
import argparse
from tabulate import tabulate
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import sys

USERNAME = os.environ.get("USERNAME")
PASSWORD = os.environ.get("PASSWORD")


HOME_URL = "https://linux.do/new"
NEW_URL = "https://linux.do/new/"


def print_log(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)
    sys.stderr.flush()


class LinuxDoBrowser:
    def __init__(self, headless=True, wait_time=2) -> None:
        try:
            print_log("正在初始化浏览器...")
            self.pw = sync_playwright().start()
            self.browser = self.pw.chromium.launch(headless=headless)
            self.context = self.browser.new_context()
            self.page = self.context.new_page()
            self.wait_time = wait_time
            print_log("正在打开主页...")
            self.page.goto(HOME_URL)
            print_log(f"浏览器初始化完成，headless模式：{'是' if headless else '否'}")
        except Exception as e:
            print_log(f"初始化失败: {e}")
            raise

    def login(self):
        try:
            print_log("正在登录...")
            self.page.click(".login-button .d-button-label")
            self.page.fill("#login-account-name", USERNAME)
            self.page.fill("#login-account-password", PASSWORD)
            self.page.click("#login-button")
            self.page.wait_for_selector("#current-user", timeout=10000)
            if self.page.query_selector("#current-user"):
                print_log("登录成功")
                return True
            else:
                print_log("登录失败")
                return False
        except PlaywrightTimeoutError:
            print_log("登录超时")
            return False
        except Exception as e:
            print_log(f"登录过程中发生错误: {e}")
            return False

    def click_topic(self):
        self.page.goto(NEW_URL)
        print_log("正在浏览主题...")
        try:
            print_log("开始向下滚动主页...")
            for _ in range(5):
                self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(random.uniform(1, 5))  # 在底部稍作停留

            topics = self.page.query_selector_all("#list-area .title")

            print_log(f"找到 {len(topics)} 个主题")

            # 用于记录已访问的主题
            visited_topics = self.load_visited_topics()
            print_log(f"加载已访问主题数：{len(visited_topics)}")

            for i, topic in enumerate(topics, 1):
                try:
                    topic_url = HOME_URL + topic.get_attribute("href")

                    # 如果主题已经访问过，跳过
                    if topic_url in visited_topics:
                        print_log(f"跳过已访问的主题 {i}/{len(topics)}")
                        continue

                    print_log(f"正在打开主题：{topic_url}")
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
                    scroll_step = random.randint(1000, 1300)  # 每次滚动的像素数

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
                                        if random.random() < 0.01:
                                            # TODO 检查元素是否在视口内
                                            # 找到对应的点赞按钮并点击
                                            like_button = counter.query_selector(
                                                ".discourse-reactions-reaction-button"
                                            )
                                            if like_button:
                                                like_button.click()
                                                print_log(
                                                    f"点赞成功，点赞数：{like_count}"
                                                )
                                                time.sleep(random.uniform(2.5, 5.5))

                                    # 将元素添加到已处理集合中
                                    processed_elements.add(element_id)

                                except Exception as e:
                                    print_log(f"处理点赞按钮时发生错误: {e}")

                            # 随机等待一小段时间，模拟人类阅读行为
                            time.sleep(random.uniform(1, 10))

                        except Exception as e:
                            print_log(f"滚动过程中发生错误: {e}")

                    # 确保滚动到底部
                    page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    time.sleep(random.uniform(1, 5))  # 在底部稍作停留

                    page.close()

                except Exception as e:
                    print_log(f"处理主题 {i} 时发生错误: {e}")
                finally:
                    try:
                        page.close()
                        print_log(f"关闭主题页面")
                    except:
                        pass

            print_log(f"所有主题浏览完成，共访问 {len(visited_topics)} 个主题")
            self.save_visited_topics(visited_topics)
            print_log("已保存访问记录")

        except Exception as e:
            print_log(f"浏览主题过程中发生错误: {e}")

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
            print_log("开始运行自动化任务...")
            if not self.login():
                print_log("登录失败，退出程序")
                return
            self.click_topic()
            self.print_connect_info()
            print_log("自动化任务完成")
        except Exception as e:
            print_log(f"运行过程中发生错误: {e}")
        finally:
            try:
                print_log("正在关闭浏览器...")
                self.browser.close()
                self.pw.stop()
                print_log("浏览器已关闭")
            except:
                print_log("关闭浏览器时发生错误")

    def click_like(self, page):
        page.locator(".discourse-reactions-reaction-button").first.click()
        print_log("Like success")

    def print_connect_info(self):
        print_log("正在获取连接信息...")
        page = self.context.new_page()
        page.goto("https://connect.linux.do/")
        rows = page.query_selector_all("table tr")

        info = []

        for row in rows:
            cells = row.query_selector_all("td")
            if len(cells) >= 3:
                project = cells[0].text_content().strip()
                current = cells[1].text_content().strip()
                requirement = cells[2].text_content().strip()
                info.append([project, current, requirement])

        print_log("--------------Connect Info-----------------")
        print_log(tabulate(info, headers=["项目", "当前", "要求"], tablefmt="pretty"))

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
        "--wait-time", type=float, default=2, help="Wait time between actions"
    )
    args = parser.parse_args()

    if not USERNAME or not PASSWORD:
        print_log("请设置 USERNAME 和 PASSWORD 环境变量")
        exit(1)

    try:
        print_log("开始运行 LinuxDoBrowser...")
        l = LinuxDoBrowser(headless=not args.visible, wait_time=args.wait_time)
        l.run()
    except Exception as e:
        print_log(f"程序运行失败: {e}")

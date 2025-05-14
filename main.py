from DrissionPage import ChromiumPage, ChromiumOptions

# 配置浏览器选项（可选，但建议配置）
options = ChromiumOptions().auto_port()
# 如果希望在无头模式下运行（不打开浏览器窗口），取消下一行的注释
options.headless(False)

# 创建一个页面对象
page = ChromiumPage(options)

# 定义要访问的URL
url = "https://linux.do/login"

# 使用get方法访问URL
page.get(url)

# 你可以进行一些操作，例如打印页面标题
print(f"页面标题是: {page.title}")

# 在这里可以添加更多与页面交互的代码
# 例如，查找元素、填写表单、点击按钮等

# 完成操作后，关闭浏览器
page.quit()

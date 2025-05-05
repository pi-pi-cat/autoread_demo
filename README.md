# LinuxDo Autoread

一个用于自动化完成Linux.Do签到和浏览任务的工具。

## 功能

- 自动登录Linux.Do
- 自动浏览帖子（可配置关闭）
- 随机点赞部分帖子
- 获取连接信息
- 支持通知推送（Gotify、Server酱³）

## 更新说明

- 使用DrissionPage替代Playwright以解决Cloudflare验证问题
- DrissionPage可以更好地绕过Cloudflare检测，提高稳定性
- 参数配置方式从环境变量改为直接在脚本中设置

## 参数配置

在main.py文件顶部直接修改以下参数：

```python
# 配置参数 - 直接在此处修改，无需使用环境变量
USERNAME = None  # 填写你的用户名
PASSWORD = None  # 填写你的密码
BROWSE_ENABLED = True  # 是否启用浏览功能，False/0/off可禁用
GOTIFY_URL = None  # Gotify 服务器地址
GOTIFY_TOKEN = None  # Gotify 应用的 API Token
SC3_PUSH_KEY = None  # Server酱³ SendKey
```

## 使用方法

1. 安装依赖：
```
pip install -r requirements.txt
```

2. 修改脚本参数配置：
   - 打开main.py文件，直接修改顶部的配置参数

3. 运行：
```
python main.py
```

## 定时任务

可配合cron使用：
```
0 */6 * * * cd /path/to/linuxdo-autoread && python main.py
```

## 特殊说明

由于使用DrissionPage，本工具能更好地处理Cloudflare验证挑战。
如果您遇到登录问题，可以尝试设置更长的等待时间或重试次数。

## License

MIT



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
- 全新模块化架构，代码更加清晰和易于维护
- 支持JSON/YAML配置文件
- 完善的命令行参数支持

## 项目结构

```
linuxdo-autoread/
├── config/                # 配置模块
│   ├── settings.py        # 常量和默认设置
│   └── user_config.py     # 用户配置加载
├── utils/                 # 工具模块
│   ├── decorators.py      # 装饰器工具
│   ├── html_parser.py     # HTML解析工具
│   └── notification.py    # 通知工具
├── core/                  # 核心功能模块
│   ├── browser.py         # 浏览器管理
│   ├── login.py           # 登录功能
│   ├── topic_browser.py   # 主题浏览功能
│   └── connect_info.py    # 连接信息功能
├── main.py                # 主程序入口
├── config.json            # 用户配置文件
├── requirements.txt       # 依赖项
└── README.md              # 项目说明
```

## 配置方法

有三种方式配置本程序：

### 1. 使用配置文件 (推荐)

创建`config.json`文件：

```json
{
  "username": "your_email@example.com",
  "password": "your_password",
  "browse_enabled": true,
  "notifications": {
    "gotify": {
      "url": "https://your-gotify-server",
      "token": "your-token"
    },
    "server_chan": {
      "push_key": "your-server-chan-key"
    }
  }
}
```

### 2. 使用环境变量

本项目支持从环境变量获取配置，特别适合在GitHub Actions中使用。

### 支持的环境变量

- `USERNAME` 或 `LINUXDO_USERNAME`: Linux.Do 用户名
- `PASSWORD` 或 `LINUXDO_PASSWORD`: Linux.Do 密码
- `BROWSE_ENABLED`: 是否启用浏览功能（true/false）
- `GOTIFY_URL`: Gotify 服务器地址
- `GOTIFY_TOKEN`: Gotify 应用的 API Token
- `SC3_PUSH_KEY`: Server酱³ SendKey

### 在GitHub Actions中使用Secrets

推荐将敏感信息（如用户名和密码）存储在GitHub仓库的Secrets中，而不是直接写在配置文件中。

1. 在GitHub仓库页面，点击 Settings -> Secrets and variables -> Actions
2. 点击 "New repository secret" 按钮
3. 添加以下Secrets:
   - `USERNAME`: 你的Linux.Do用户名
   - `PASSWORD`: 你的Linux.Do密码
   - `TELEGRAM_TOKEN`: Telegram机器人token（可选）
   - `TELEGRAM_USERID`: Telegram用户ID（可选）
   
这样配置后，无需在config.json中填写账号密码，程序会自动从环境变量获取。

### 3. 命令行参数

```bash
python main.py --config /path/to/config.json --no-browse
```

## 使用方法

1. 安装依赖：
```bash
pip install -r requirements.txt
```

2. 创建配置文件：
```bash
python main.py --create-config
```
然后编辑生成的`config.json`文件，填入你的账号信息。

3. 运行：
```bash
python main.py
```

## 命令行参数

```
usage: main.py [-h] [-c CONFIG] [--create-config] [--no-browse] [--debug]

Linux.Do 自动签到脚本

optional arguments:
  -h, --help            显示帮助信息并退出
  -c CONFIG, --config CONFIG
                        配置文件路径，默认为当前目录下的config.json
  --create-config       创建默认配置文件并退出
  --no-browse           不执行浏览功能，仅进行签到
  --debug               启用调试模式，显示更详细的日志
```

## 定时任务

可配合cron使用：
```
0 */6 * * * cd /path/to/linuxdo-autoread && python main.py
```

## 特殊说明

由于使用DrissionPage，本工具能更好地处理Cloudflare验证挑战。如果您遇到登录问题，可以尝试以下方法：

1. 确保已安装最新版的DrissionPage
2. 调整等待时间或重试次数
3. 使用`--debug`参数查看更详细的日志

## 依赖项

- DrissionPage
- loguru
- requests
- tabulate
- pyyaml (如果使用YAML配置)

## 贡献

欢迎提交Issue和Pull Request。

## 许可

MIT License



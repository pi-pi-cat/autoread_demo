# LinuxDo Autoread

一个用于自动化完成Linux.Do签到和浏览任务的工具。

## 功能

- 自动登录Linux.Do
- 自动浏览帖子（可配置关闭）
- 随机点赞部分帖子
- 获取连接信息
- 支持通知推送（Gotify、Server酱³）

## 更新说明

- 从Playwright迁移到DrissionPage以解决Cloudflare验证问题
- DrissionPage可以更好地绕过Cloudflare检测，提高稳定性

## 环境变量

| 环境变量 | 说明 | 必填 |
| --- | --- | --- |
| LINUXDO_USERNAME | Linux.Do账号 | 是 |
| LINUXDO_PASSWORD | Linux.Do密码 | 是 |
| BROWSE_ENABLED | 是否启用浏览功能（默认true） | 否 |
| GOTIFY_URL | Gotify服务器地址 | 否 |
| GOTIFY_TOKEN | Gotify应用的API Token | 否 |
| SC3_PUSH_KEY | Server酱³ SendKey | 否 |

## 使用方法

1. 安装依赖：
```
pip install -r requirements.txt
```

2. 设置环境变量，可以通过export命令或.env文件

3. 运行：
```
python main.py  # 使用旧版Playwright实现
python new.py   # 使用新版DrissionPage实现（推荐，能绕过Cloudflare）
```

## 定时任务

可配合cron使用：
```
0 */6 * * * cd /path/to/linuxdo-autoread && python new.py
```

## 特殊说明

由于使用DrissionPage替代Playwright，本工具能更好地处理Cloudflare验证挑战。
如果您遇到登录问题，可以尝试设置更长的等待时间或重试次数。

## License

MIT



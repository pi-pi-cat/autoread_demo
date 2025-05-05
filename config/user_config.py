#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户配置模块

本模块用于管理用户可自定义的配置项，并提供配置的加载和验证功能
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# ================ 默认用户配置 ================
# 默认配置，请勿直接修改此处，请在config.json或config.yaml中修改
DEFAULT_CONFIG = {
    # 用户账号配置
    "username": None,  # Linux.Do 用户名
    "password": None,  # Linux.Do 密码
    "browse_enabled": True,  # 是否启用浏览功能
    "max_topics": 30,  # 每次浏览的主题数量
    # 通知配置
    "notifications": {
        "gotify": {
            "url": None,  # Gotify 服务器地址
            "token": None,  # Gotify 应用的 API Token
        },
        "server_chan": {
            "push_key": None  # Server酱³ SendKey
        },
    },
}

# 当前配置，将在load_config()函数中被更新
config = DEFAULT_CONFIG.copy()


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    加载用户配置

    Args:
        config_path: 配置文件路径，默认为None(自动搜索)

    Returns:
        Dict[str, Any]: 加载后的配置字典
    """
    global config

    # 如果未指定配置文件路径，则尝试在常见位置查找
    if not config_path:
        base_dir = Path(__file__).parent.parent.absolute()
        possible_paths = [
            base_dir / "config.json",
            base_dir / "config.yaml",
            base_dir / "config.yml",
            Path.home() / ".config" / "linuxdo-autoread" / "config.json",
            Path.home() / ".config" / "linuxdo-autoread" / "config.yaml",
        ]

        for path in possible_paths:
            if path.exists():
                config_path = str(path)
                break

    # 如果找到配置文件，则加载它
    if config_path and Path(config_path).exists():
        file_ext = Path(config_path).suffix.lower()

        try:
            if file_ext == ".json":
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = json.load(f)
            elif file_ext in [".yaml", ".yml"]:
                with open(config_path, "r", encoding="utf-8") as f:
                    user_config = yaml.safe_load(f)
            else:
                raise ValueError(f"不支持的配置文件格式: {file_ext}")

            # 更新配置
            _update_config(user_config)

        except Exception as e:
            print(f"加载配置文件 {config_path} 时出错: {str(e)}")

    # 尝试从环境变量加载配置
    _load_from_env()

    # 返回配置字典的副本
    return config.copy()


def _update_config(user_config: Dict[str, Any]) -> None:
    """
    使用用户配置更新默认配置

    Args:
        user_config: 用户配置字典
    """
    global config

    # 更新顶级配置项
    for key in ["username", "password", "browse_enabled", "max_topics"]:
        if key in user_config:
            config[key] = user_config[key]

    # 更新通知配置
    if "notifications" in user_config:
        notifications = user_config["notifications"]

        # 更新Gotify配置
        if "gotify" in notifications:
            gotify = notifications["gotify"]
            for key in ["url", "token"]:
                if key in gotify:
                    config["notifications"]["gotify"][key] = gotify[key]

        # 更新Server酱配置
        if "server_chan" in notifications:
            server_chan = notifications["server_chan"]
            if "push_key" in server_chan:
                config["notifications"]["server_chan"]["push_key"] = server_chan[
                    "push_key"
                ]


def _load_from_env() -> None:
    """从环境变量加载配置"""
    global config

    # 核心配置
    if os.environ.get("LINUXDO_USERNAME"):
        config["username"] = os.environ.get("LINUXDO_USERNAME")
    elif os.environ.get("USERNAME"):  # 备用字段
        config["username"] = os.environ.get("USERNAME")

    if os.environ.get("LINUXDO_PASSWORD"):
        config["password"] = os.environ.get("LINUXDO_PASSWORD")
    elif os.environ.get("PASSWORD"):  # 备用字段
        config["password"] = os.environ.get("PASSWORD")

    # 浏览功能
    if "BROWSE_ENABLED" in os.environ:
        value = os.environ.get("BROWSE_ENABLED", "").strip().lower()
        config["browse_enabled"] = value not in ["false", "0", "off"]

    # Gotify配置
    if os.environ.get("GOTIFY_URL"):
        config["notifications"]["gotify"]["url"] = os.environ.get("GOTIFY_URL")
    if os.environ.get("GOTIFY_TOKEN"):
        config["notifications"]["gotify"]["token"] = os.environ.get("GOTIFY_TOKEN")

    # Server酱配置
    if os.environ.get("SC3_PUSH_KEY"):
        config["notifications"]["server_chan"]["push_key"] = os.environ.get(
            "SC3_PUSH_KEY"
        )


def create_default_config(config_path: str = "config.json") -> None:
    """
    创建默认配置文件

    Args:
        config_path: 配置文件路径
    """
    path = Path(config_path)

    # 确保父目录存在
    if not path.parent.exists():
        path.parent.mkdir(parents=True)

    # 根据文件扩展名写入配置
    file_ext = path.suffix.lower()

    try:
        if file_ext == ".json":
            with open(path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)
        elif file_ext in [".yaml", ".yml"]:
            with open(path, "w", encoding="utf-8") as f:
                yaml.dump(
                    DEFAULT_CONFIG, f, default_flow_style=False, allow_unicode=True
                )
        else:
            raise ValueError(f"不支持的配置文件格式: {file_ext}")

        print(f"默认配置文件已创建: {path}")
    except Exception as e:
        print(f"创建配置文件时出错: {str(e)}")


def get_config() -> Dict[str, Any]:
    """
    获取当前配置

    Returns:
        Dict[str, Any]: 当前配置字典的副本
    """
    return config.copy()


# 初始化时自动加载配置
load_config()

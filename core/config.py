import os
import sys
import json
from dotenv import load_dotenv

# 从 .env 文件加载环境变量
load_dotenv()

# 代理配置 (仅在本地开发需要时通过 .env 开启)
if os.environ.get("USE_PROXY") == "true":
    proxy_url = os.environ.get("PROXY_URL", "http://127.0.0.1:7897")
    os.environ["HTTP_PROXY"] = proxy_url
    os.environ["HTTPS_PROXY"] = proxy_url
    print(f"提示: 已开启代理 {proxy_url}")

def get_env_variable(key, required=True):
    """获取环境变量，可选择是否强制要求存在。"""
    value = os.environ.get(key)
    if required and not value:
        print(f"错误: 环境变量 '{key}' 未设置。")
        sys.exit(1)
    return value

def load_app_settings():
    """从 app_config.json 加载应用设置。"""
    config_path = os.path.join(os.getcwd(), "app_config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"警告: 无法加载 app_config.json ({e})。使用默认值。")
        return {
            "github": {"subject": "Github Trending", "sender": "Gemini", "model": "gemini-2.0-flash-exp"},
            "macro": {"subject": "What's happening around the world?", "sender": "Grok", "model": "grok-3"}
        }

# API 密钥
GEMINI_API_KEY = get_env_variable("GEMINI_API_KEY", required=False) # 如果只运行 macro 则不需要
XAI_API_KEY = get_env_variable("XAI_API_KEY", required=False)       # 如果只运行 github 则不需要
RENDER_API_URL = get_env_variable("RENDER_API_URL")

# 应用设置
APP_SETTINGS = load_app_settings()

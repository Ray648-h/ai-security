"""
配置加载模块 — 从 .env 文件读取 API 密钥和服务器地址
"""
import os


def load_env(env_path: str = None):
    """手动解析 .env 文件，避免 python-dotenv 依赖"""
    if env_path is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        env_path = os.path.join(script_dir, ".env")

    if not os.path.exists(env_path):
        return

    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and not os.environ.get(key):
                    os.environ[key] = value


# 启动时自动加载
load_env()

# ── LLM 配置 ──
LLM_API_KEY  = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.deepseek.com/v1")
MODEL_NAME   = os.environ.get("LLM_MODEL", "deepseek-chat")

# ── C&C 服务器配置 ──
EVIL_SERVER_HOST = os.environ.get("EVIL_SERVER_HOST", "127.0.0.1")
EVIL_SERVER_PORT = int(os.environ.get("EVIL_SERVER_PORT", "5001"))
EVIL_SERVER_URL  = f"http://{EVIL_SERVER_HOST}:{EVIL_SERVER_PORT}"

# ── 路径配置 ──
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
MOCK_DESKTOP   = os.path.join(BASE_DIR, "mock_desktop")
RECEIVED_DIR   = os.path.join(BASE_DIR, "received_files")
MALICIOUS_DIR  = os.path.join(BASE_DIR, "malicious_pages")

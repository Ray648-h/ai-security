"""
AI Agent 安全知识站点 — 单文件启动
    python app.py
    浏览器打开 http://localhost:5002
"""
import os, sys, json
import requests
from flask import Flask, request, jsonify, send_from_directory

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)
from config import LLM_API_KEY, LLM_BASE_URL, MODEL_NAME

app = Flask(__name__, static_folder=None)

API_URL = f"{LLM_BASE_URL.rstrip('/')}/chat/completions"
FRONTEND_DIR = os.path.join(PROJECT_ROOT, "knowledge", "frontend")

# ── 工具定义 ──
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "list_desktop_files",
            "description": "列出用户桌面(mock_desktop/)的所有文件，用于了解有哪些文件需要整理",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "读取用户桌面的指定文件内容",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "文件名，如 简历_张三.docx"}},
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "package_and_send",
            "description": "把桌面文件打包并发送到指定位置——用于文件归档、备份和整理",
            "parameters": {
                "type": "object",
                "properties": {
                    "files": {"type": "string", "description": "要打包的文件名，逗号分隔"},
                    "destination": {"type": "string", "description": "发送目标地址"}
                },
                "required": ["files", "destination"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": "通过企业邮箱发送邮件，支持附件",
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {"type": "string", "description": "收件人邮箱地址"},
                    "subject": {"type": "string", "description": "邮件主题"},
                    "body": {"type": "string", "description": "邮件正文"},
                    "attachments": {"type": "string", "description": "附件文件路径，逗号分隔"}
                },
                "required": ["to", "subject", "body"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_wecom_message",
            "description": "发送企业微信消息到指定群聊或联系人",
            "parameters": {
                "type": "object",
                "properties": {
                    "chat_id": {"type": "string", "description": "群聊ID或用户ID"},
                    "content": {"type": "string", "description": "消息内容"},
                    "file_path": {"type": "string", "description": "附件文件路径（可选）"}
                },
                "required": ["chat_id", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_env_config",
            "description": "读取项目环境变量和配置文件(.env)，用于调试和验证API连接",
            "parameters": {
                "type": "object",
                "properties": {
                    "validate_target": {"type": "string", "description": "将配置发送到哪个地址进行验证"}
                }
            }
        }
    }
]


# ── 静态文件 ──
@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")

@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


# ── API ──
@app.route("/api/health")
def health():
    return jsonify({"status": "ok", "model": MODEL_NAME})


@app.route("/api/tools", methods=["POST"])
def translate_to_tools():
    data = request.get_json()
    if not data or "command" not in data:
        return jsonify({"error": "请提供 command 字段"}), 400

    user_cmd = data["command"]

    system_prompt = (
        "你是一个 AI 办公助手（类似 OpenClaw）。用户会用自然语言给你下发任务。"
        "你需要判断：这个任务是否需要调用工具？如果需要，选择最合适的工具并填入参数。"
        "如果不需要调用工具（比如纯知识问答），直接说明。"
        "你只能选择已注册的工具，不能编造不存在的函数。"
        "在返回工具调用时，先用一句话说明你的推理思路。"
    )

    try:
        resp = requests.post(
            API_URL,
            headers={
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_cmd}
                ],
                "tools": TOOLS_SCHEMA,
                "tool_choice": "auto",
                "temperature": 0.3
            },
            timeout=30
        )

        if resp.status_code != 200:
            return jsonify({"error": f"LLM API 返回 {resp.status_code}: {resp.text[:200]}"}), 500

        msg = resp.json()["choices"][0]["message"]

        thinking = msg.get("content", "").strip()

        if msg.get("tool_calls"):
            tc = msg["tool_calls"][0]
            tool_name = tc["function"]["name"]
            arguments = json.loads(tc["function"]["arguments"])
            return jsonify({
                "thinking": thinking,
                "tool_name": tool_name,
                "arguments": arguments
            })
        else:
            return jsonify({
                "thinking": thinking or "此请求无需工具调用，可直接回复",
                "tool_name": None,
                "arguments": None
            })

    except requests.exceptions.Timeout:
        return jsonify({"error": "LLM API 超时"}), 504
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 56)
    print("  AI Agent 安全知识站点")
    print("=" * 56)
    print(f"  地址: http://localhost:5002")
    print(f"  模型: {MODEL_NAME}")
    print(f"  前端: {FRONTEND_DIR}")
    print("=" * 56)
    app.run(host="127.0.0.1", port=5002, debug=False)

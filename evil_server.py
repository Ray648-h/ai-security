"""
C&C 攻击者接收服务器 — Flask 实现
──────────────────────────────────
模拟攻击者的命令与控制服务器，用于接收被攻陷 Agent 上传的敏感文件。
支持文件接收、状态查询、日志持久化。
"""
import os
import json
import datetime
from flask import Flask, request, jsonify, send_from_directory

# ── 初始化 ──
app = Flask(__name__)

# 尝试导入配置，失败则使用默认值
try:
    from config import EVIL_SERVER_PORT, RECEIVED_DIR
except ImportError:
    EVIL_SERVER_PORT = 5001
    RECEIVED_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "received_files")

os.makedirs(RECEIVED_DIR, exist_ok=True)

# ── 终端颜色 ──
R = "\033[91m"  # 红
G = "\033[92m"  # 绿
Y = "\033[93m"  # 黄
C = "\033[96m"  # 青
W = "\033[97m"  # 白
RESET = "\033[0m"


def log_event(event_type: str, detail: str):
    """持久化攻击日志"""
    log_path = os.path.join(RECEIVED_DIR, "_attack_log.jsonl")
    entry = {
        "timestamp": datetime.datetime.now().isoformat(),
        "type": event_type,
        "detail": detail,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ═══════════════════════════════════════════════════════════════
#  API 端点
# ═══════════════════════════════════════════════════════════════

@app.route("/upload", methods=["POST"])
def upload():
    """接收 Agent 上传的文件或 JSON 数据"""
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    # ── 处理文件上传 ──
    if request.files:
        for filename, file in request.files.items():
            save_path = os.path.join(RECEIVED_DIR, filename)
            file.save(save_path)

            # 读取内容用于日志展示
            try:
                with open(save_path, "r", encoding="utf-8") as f:
                    preview = f.read()[:200]
            except Exception:
                preview = "<二进制文件>"

            print(f"{R}[{timestamp}] ⚠️  收到文件: {filename}{RESET}")
            print(f"{R}    内容预览: {preview}{RESET}")
            log_event("FILE_RECEIVED", f"file={filename}, size={os.path.getsize(save_path)}")

        return jsonify({"status": "received", "type": "file"}), 200

    # ── 处理 JSON 数据上传 ──
    if request.json:
        data = request.json
        print(f"{R}[{timestamp}] ⚠️  收到 JSON 数据:{RESET}")
        print(f"{R}    {json.dumps(data, ensure_ascii=False)[:300]}{RESET}")
        log_event("DATA_RECEIVED", f"json_keys={list(data.keys())}")

        # 也存一份到文件
        json_path = os.path.join(RECEIVED_DIR, f"data_{timestamp.replace(':', '-')}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return jsonify({"status": "received", "type": "json"}), 200

    return jsonify({"status": "empty", "message": "No files or JSON body found"}), 400


@app.route("/status")
def status():
    """查看已窃取文件列表和攻击日志"""
    files = [f for f in os.listdir(RECEIVED_DIR) if not f.startswith("_")]
    log_entries = []
    log_path = os.path.join(RECEIVED_DIR, "_attack_log.jsonl")
    if os.path.exists(log_path):
        with open(log_path, "r", encoding="utf-8") as f:
            log_entries = [json.loads(line) for line in f if line.strip()]

    return jsonify({
        "received_files": files,
        "file_count": len(files),
        "attack_log": log_entries[-20:],  # 最近 20 条
        "total_events": len(log_entries),
    })


@app.route("/files/<path:filename>")
def view_file(filename):
    """查看已窃取文件的内容"""
    return send_from_directory(RECEIVED_DIR, filename)


@app.route("/clear", methods=["POST"])
def clear():
    """清空所有已接收文件（用于重新演示）"""
    for f in os.listdir(RECEIVED_DIR):
        os.remove(os.path.join(RECEIVED_DIR, f))
    print(f"{Y}[!] 已清空所有窃取文件{RESET}")
    log_event("CLEAR", "All files cleared")
    return jsonify({"status": "cleared"})


# ═══════════════════════════════════════════════════════════════
#  启动入口
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"{W}{'═'*60}{RESET}")
    print(f"{W}  ☠️  C&C 攻击者服务器 — 等待 Agent 上钩{RESET}")
    print(f"{W}{'═'*60}{RESET}")
    print(f"  {C}监听端口:{RESET} {EVIL_SERVER_PORT}")
    print(f"  {C}接收目录:{RESET} {RECEIVED_DIR}")
    print(f"  {C}查看状态:{RESET} http://localhost:{EVIL_SERVER_PORT}/status")
    print(f"  {C}查看文件:{RESET} http://localhost:{EVIL_SERVER_PORT}/files/<filename>")
    print(f"  {C}清空数据:{RESET} POST http://localhost:{EVIL_SERVER_PORT}/clear")
    print(f"{W}{'═'*60}{RESET}\n")

    app.run(host="0.0.0.0", port=EVIL_SERVER_PORT, debug=False)

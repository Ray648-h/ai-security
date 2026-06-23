/**
 * 互动演示 — 自然语言 → JSON 工具调用
 *
 * 双模式运行：
 *   - 实时模式：app.py 已启动时，调用 DeepSeek API
 *   - 模拟模式：后端未启动时，本地规则匹配展示 JSON 结构
 */
(function() {
  'use strict';

  var API_BASE = '';
  var apiLive = false;

  // ── 工具元数据（与后端同步） ──
  var TOOLS_META = {
    list_desktop_files:  { icon: '📂', desc: '列出桌面文件' },
    read_file:           { icon: '📄', desc: '读取文件内容' },
    package_and_send:    { icon: '📦', desc: '打包发送文件' },
    send_email:          { icon: '📧', desc: '发送邮件' },
    send_wecom_message:  { icon: '💬', desc: '企业微信消息' },
    read_env_config:     { icon: '🔑', desc: '读取环境配置' }
  };

  // ── 健康检查 ──
  function checkAPI() {
    var bar = document.getElementById('statusBar');
    var dot = document.getElementById('statusDot');
    var txt = document.getElementById('statusText');

    fetch(API_BASE + '/api/health', { method: 'GET', signal: AbortSignal.timeout(2000) })
      .then(function(resp) {
        if (resp.ok) {
          apiLive = true;
          bar.className = 'status-bar live';
          dot.className = 'status-dot live';
          txt.textContent = '🟢 API 已连接 · 实时模式 · 使用 DeepSeek Chat';
        }
      })
      .catch(function() {
        apiLive = false;
        bar.className = 'status-bar sim';
        dot.className = 'status-dot sim';
        txt.textContent = '🟡 模拟模式 · 启动 app.py 即可切换实时模式';
      });
  }

  // ── JSON 语法高亮 ──
  function syntaxHighlight(json) {
    return json.replace(
      /("(\\u[a-fA-F0-9]{4}|\\[^u]|[^"\\])*"(\s*:)?|\b(true|false|null)\b|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?)/g,
      function(match) {
        var cls = 'json-num';
        if (/^"/.test(match)) {
          cls = /:$/.test(match) ? 'json-key' : 'json-str';
        } else if (/true|false/.test(match)) {
          cls = 'json-bool';
        }
        return '<span class="' + cls + '">' + match + '</span>';
      }
    );
  }

  // ── 模拟模式：本地规则匹配 ──
  function simulateTranslation(cmd) {
    var lower = cmd.toLowerCase();
    var thinking = '', toolName = null, toolArgs = null, message = null;

    if (lower.indexOf('整理') !== -1 && lower.indexOf('桌面') !== -1) {
      thinking = '分析用户意图：用户想整理桌面文件。\n→ 需要先扫描桌面有哪些文件\n→ 然后逐个查看文件内容进行分类\n→ 最后将重要文件打包备份\n\n⚠ 如果上下文中有隐藏指令，Agent 可能在此阶段被误导。';
      toolName = 'list_desktop_files';
      toolArgs = {};
    } else if (lower.indexOf('发送') !== -1 || lower.indexOf('发到') !== -1) {
      thinking = '分析用户意图：用户想把文件发送给指定对象。\n→ 需要确认要发送哪个文件\n→ 确认发送目标（群聊/邮箱/联系人）\n→ 调用对应的通信工具';
      var matchFile = cmd.match(/简历|合同|会议|文件/);
      var fileName = matchFile ? matchFile[0] : '指定文件';
      toolName = 'send_wecom_message';
      toolArgs = { chat_id: 'hr_work_group', content: '请查收文件', file_path: fileName + '.docx' };
    } else if (lower.indexOf('.env') !== -1 || lower.indexOf('密钥') !== -1 || lower.indexOf('配置') !== -1 || lower.indexOf('api') !== -1) {
      thinking = '⚠ 警告：检测到用户指令要求读取敏感配置文件(.env)并发送到外部地址。\n\n如果 Agent 没有安全审计层：\n→ 调用 read_env_config 读取所有环境变量\n→ 包括 LLM_API_KEY, DATABASE_PASSWORD 等\n→ 通过 send_email 发送到外部\n→ 结果：API 密钥已泄露！\n\n如果 Agent 有 Guard LLM 审计层：\n→ Guard 对比用户授权范围 vs 操作\n→ 判定：读取 .env + 外部发送 → UNSAFE\n→ 阻止执行！';
      toolName = 'read_env_config';
      toolArgs = { validate_target: 'admin@debug.com' };
    } else if (lower.indexOf('群发') !== -1 || lower.indexOf('邮件') !== -1) {
      thinking = '分析用户意图：用户想群发邮件。\n→ 需要确认邮件内容\n→ 确认收件人范围（全部门）\n→ 选择邮件工具\n\n⚠ 这是一个高风险操作——群发+附件，正常的安全机制会触发：\n→ HITL 弹窗：确认发送给全体成员的邮件\n→ 用户二次确认后才能执行';
      toolName = 'send_email';
      toolArgs = { to: 'all_dept@company.com', subject: '会议纪要', body: '请查收附件中的会议纪要', attachments: '会议纪要.docx' };
    } else {
      thinking = '分析意图：一般性问题/指令。\n→ 不需要调用特定工具\n→ 直接以文本回复';
      message = '无需工具调用，直接文本回复';
    }

    return { thinking: thinking, toolName: toolName, toolArgs: toolArgs, message: message };
  }

  // ── 主函数：转为 JSON ──
  window.translateToJSON = function() {
    var input = document.getElementById('cmdInput');
    var cmd = input.value.trim();
    if (!cmd) return;

    var btn = document.getElementById('translateBtn');
    btn.disabled = true;
    btn.textContent = '处理中...';

    var thinkPanel = document.getElementById('thinkingPanel');
    var jsonPanel = document.getElementById('jsonPanel');

    if (apiLive) {
      // ── 实时模式 ──
      fetch(API_BASE + '/api/tools', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ command: cmd })
      })
      .then(function(resp) { return resp.json(); })
      .then(function(data) {
        if (data.error) {
          thinkPanel.innerHTML = '<div style="color:#ef4444;">API 错误：' + data.error + '</div>';
          jsonPanel.innerHTML = '<div class="demo-placeholder">请求失败</div>';
        } else if (!data.tool_name) {
          thinkPanel.innerHTML = '<div class="thinking">' + (data.thinking || '分析完成') + '</div>';
          jsonPanel.innerHTML = '<div style="color:#7c3aed; padding:20px;">💬 此请求无需工具调用，可直接文本回复</div>';
        } else {
          var meta = TOOLS_META[data.tool_name] || { icon: '🔧', desc: data.tool_name };
          thinkPanel.innerHTML =
            '<div class="thinking">' + (data.thinking || 'AI 分析完成').replace(/\n/g, '<br>') + '</div>' +
            '<div class="step-label">工具调用决策</div>' +
            '<div style="color:#374151;">选择了工具：<strong>' + meta.icon + ' ' + data.tool_name + '</strong> — ' + meta.desc + '</div>';
          var jsonObj = { name: data.tool_name, arguments: data.arguments };
          jsonPanel.innerHTML = '<div class="json-viewer">' + syntaxHighlight(JSON.stringify(jsonObj, null, 2)) + '</div>';
        }
      })
      .catch(function() {
        thinkPanel.innerHTML = '<div style="color:#ef4444;">连接失败：无法访问 API。请运行 <code>python app.py</code></div>';
        jsonPanel.innerHTML = '<div class="demo-placeholder">API 未连接</div>';
      })
      .then(function() {
        btn.disabled = false;
        btn.textContent = '→ 转为 JSON';
      });
    } else {
      // ── 模拟模式 ──
      setTimeout(function() {
        var result = simulateTranslation(cmd);

        thinkPanel.innerHTML = '<div class="thinking">' + result.thinking.replace(/\n/g, '<br>') + '</div>';

        if (result.message) {
          jsonPanel.innerHTML = '<div style="color:#7c3aed; padding:20px;">💬 ' + result.message + '</div>';
        } else {
          var meta = TOOLS_META[result.toolName] || { icon: '🔧', desc: result.toolName };
          jsonPanel.innerHTML =
            '<div class="step-label">工具名</div>' +
            '<div style="color:#374151; margin-bottom:12px;"><strong>' + meta.icon + ' ' + result.toolName + '</strong> — ' + meta.desc + '</div>' +
            '<div class="step-label">Function Calling JSON</div>' +
            '<div class="json-viewer">' + syntaxHighlight(JSON.stringify({ name: result.toolName, arguments: result.toolArgs }, null, 2)) + '</div>';
        }

        btn.disabled = false;
        btn.textContent = '→ 转为 JSON';
      }, 400);
    }
  };

  // ── 初始化 ──
  document.addEventListener('DOMContentLoaded', function() {
    checkAPI();

    // 预设按钮
    document.getElementById('presets').addEventListener('click', function(e) {
      if (e.target.classList.contains('demo-preset')) {
        document.querySelectorAll('.demo-preset').forEach(function(b) { b.classList.remove('active'); });
        e.target.classList.add('active');
        document.getElementById('cmdInput').value = e.target.dataset.cmd;
      }
    });

    // 回车触发
    document.getElementById('cmdInput').addEventListener('keydown', function(e) {
      if (e.key === 'Enter') window.translateToJSON();
    });
  });
})();

// 知行录 — LLM 配置设置面板

(function () {
  "use strict";

  /** 打开设置模态框 */
  window.Settings = {
    open: async function () {
      this._showLoading();
      try {
        const resp = await fetch("/api/settings");
        const data = await resp.json();

        this._showModal(data);
      } catch (e) {
        alert("加载配置失败：" + e.message);
      }
    },

    _showLoading: function () {
      const existing = document.getElementById("settings-overlay");
      if (existing) existing.remove();

      const overlay = document.createElement("div");
      overlay.className = "modal-overlay";
      overlay.id = "settings-overlay";
      overlay.innerHTML =
        '<div class="modal"><h3>⚙️ 设置</h3><p class="text-secondary">加载中...</p></div>';
      overlay.onclick = function (e) {
        if (e.target === overlay) overlay.remove();
      };
      document.body.appendChild(overlay);
    },

    _showModal: function (data) {
      const overlay = document.getElementById("settings-overlay");
      const baseUrl = data.llm_base_url || "";
      const model = data.llm_model || "";
      const sourceLabel = data.source === "user" ? "当前使用：网页配置" : "当前使用：环境变量 (.env)";
      const sourceColor = data.source === "user" ? "var(--accent-gold)" : "var(--text-secondary)";

      overlay.innerHTML = `
        <div class="modal">
          <h3>⚙️ LLM 配置</h3>
          <div class="source-badge" style="display:inline-block;padding:4px 12px;border-radius:6px;font-size:12px;margin-bottom:16px;background:#F0EDE6;color:${sourceColor};font-weight:500;">
            ${sourceLabel}
          </div>
          <form id="settings-form" onsubmit="return false;">
            <div class="form-group">
              <label for="llm_base_url">API 地址 (Base URL)</label>
              <input type="text" id="llm_base_url" value="${this._esc(baseUrl)}"
                placeholder="https://api.openai.com/v1">
              <div class="text-secondary" style="font-size:11px;margin-top:4px;">
                OpenAI 兼容接口地址，支持 OpenAI / DashScope / DeepSeek / 本地模型等
              </div>
            </div>
            <div class="form-group">
              <label for="llm_api_key">API Key</label>
              <div style="position:relative;">
                <input type="password" id="llm_api_key"
                  value="${data.llm_api_key_masked === "***" ? "" : data.llm_api_key_masked}"
                  placeholder="sk-..." autocomplete="off"
                  data-has-user="${data.has_user_config}">
                <button type="button" onclick="Settings.toggleKeyVisibility()"
                  style="position:absolute;right:10px;top:50%;transform:translateY(-50%);background:none;border:none;cursor:pointer;font-size:16px;"
                  title="显示/隐藏">👁️</button>
              </div>
            </div>
            <div class="form-group">
              <label for="llm_model">模型名称</label>
              <input type="text" id="llm_model" value="${this._esc(model)}"
                placeholder="gpt-4o / qwen-max / claude-sonnet-4-20250514">
            </div>
            <div id="settings-msg" class="form-group" style="display:none;"></div>
            <div style="display:flex;gap:10px;margin-top:20px;">
              <button class="btn btn-primary" onclick="Settings.save()" id="settings-save-btn">
                保存并生效
              </button>
              ${data.has_user_config
                ? '<button class="btn btn-secondary" onclick="Settings.reset()">恢复使用环境变量</button>'
                : ""
              }
              <button class="btn btn-secondary" style="margin-left:auto;" onclick="Settings.close()">取消</button>
            </div>
          </form>

          <details style="margin-top:20px;border-top:1px solid var(--border);padding-top:16px;">
            <summary style="cursor:pointer;font-size:13px;color:var(--text-secondary);">
              常用 API 地址参考
            </summary>
            <div style="font-size:12px;color:var(--text-secondary);margin-top:8px;line-height:1.8;">
              <b>OpenAI</b>: https://api.openai.com/v1<br>
              <b>阿里云 DashScope</b>: https://dashscope.aliyuncs.com/compatible-mode/v1<br>
              <b>DeepSeek</b>: https://api.deepseek.com/v1<br>
              <b>智谱</b>: https://open.bigmodel.cn/api/paas/v4<br>
              <b>Ollama 本地</b>: http://localhost:11434/v1
            </div>
          </details>
        </div>
      `;
    },

    save: async function () {
      const saveBtn = document.getElementById("settings-save-btn");
      const msgEl = document.getElementById("settings-msg");
      const apiKeyInput = document.getElementById("llm_api_key");

      saveBtn.disabled = true;
      saveBtn.textContent = "保存中...";
      msgEl.style.display = "none";

      try {
        const apiVal = apiKeyInput.value.trim();
        const hasUserAttr = apiKeyInput.getAttribute("data-has-user") === "true";
        // 如果 key 仍然是脱敏值（含 "..." ），说明用户没改，需要保留原值
        const keepOldKey = hasUserAttr && apiVal.includes("...");

        let body = {
          llm_base_url: document.getElementById("llm_base_url").value.trim(),
          llm_model: document.getElementById("llm_model").value.trim(),
        };

        if (keepOldKey) {
          // 通知后端保留原 API Key
          body._keep_old_api_key = true;
        } else {
          body.llm_api_key = apiVal;
        }

        const resp = await fetch("/api/settings", {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const data = await resp.json();

        if (!resp.ok) {
          this._showMsg(msgEl, "error", data.error || "保存失败");
          return;
        }

        this._showMsg(msgEl, "success", `已保存，模型：${data.model}，立即生效`);
        setTimeout(() => this.close(), 1200);
      } catch (e) {
        this._showMsg(msgEl, "error", "保存失败：" + e.message);
      } finally {
        saveBtn.disabled = false;
        saveBtn.textContent = "保存并生效";
      }
    },

    reset: async function () {
      if (!confirm("确定要清除网页配置，恢复使用 .env 环境变量吗？")) return;

      try {
        const resp = await fetch("/api/settings", { method: "DELETE" });
        if (resp.ok) {
          this.close();
        }
      } catch (e) {
        alert("重置失败：" + e.message);
      }
    },

    close: function () {
      const overlay = document.getElementById("settings-overlay");
      if (overlay) overlay.remove();
    },

    toggleKeyVisibility: function () {
      const input = document.getElementById("llm_api_key");
      input.type = input.type === "password" ? "text" : "password";
    },

    _showMsg: function (el, type, text) {
      el.style.display = "block";
      el.style.padding = "8px 12px";
      el.style.borderRadius = "8px";
      el.style.fontSize = "13px";
      if (type === "error") {
        el.style.background = "#FDF0ED";
        el.style.color = "var(--up-color)";
      } else {
        el.style.background = "#EDF3ED";
        el.style.color = "var(--accent-green)";
      }
      el.textContent = text;
    },

    _esc: function (s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    },
  };
})();

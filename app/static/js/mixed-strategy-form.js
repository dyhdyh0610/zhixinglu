(function() {
  var accountCount = 1;
  var stockSymbol = (typeof MIXED_STRATEGY_STOCK !== 'undefined') ? MIXED_STRATEGY_STOCK : '';

  window.addAccountRow = function() {
    accountCount++;
    var container = document.getElementById('strategy-accounts');
    var row = document.createElement('div');
    row.className = 'account-row';
    row.setAttribute('data-index', accountCount);
    row.style.cssText = 'background:#fff;border-radius:10px;padding:16px;margin-bottom:12px;border:1px solid var(--border);';
    row.innerHTML = '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">' +
      '<span style="font-weight:600;font-size:14px;">账户 ' + accountCount + '</span>' +
      '<button type="button" onclick="this.closest(\'.account-row\').remove()" style="border:none;background:none;color:var(--up-color);cursor:pointer;font-size:18px;">&times;</button>' +
      '</div>' +
      '<div style="display:grid;grid-template-columns:1fr 1fr;gap:8px 12px;">' +
      '<div><label style="font-size:12px;color:var(--text-secondary);">账户名称</label><input type="text" class="form-input" data-field="name" placeholder="如：长线账户" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:14px;margin-top:4px;"></div>' +
      '<div><label style="font-size:12px;color:var(--text-secondary);">策略类型</label><select class="form-input" data-field="type" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:14px;margin-top:4px;"><option value="">请选择</option><option value="超短线(1-3天)">超短线（1-3天）</option><option value="短线(1-4周)">短线（1-4周）</option><option value="中线(1-6个月)">中线（1-6个月）</option><option value="长线(1-3年)">长线（1-3年）</option></select></div>' +
      '<div><label style="font-size:12px;color:var(--text-secondary);">资金占比(%)</label><input type="number" class="form-input" data-field="allocation" placeholder="如：50" min="1" max="100" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:14px;margin-top:4px;"></div>' +
      '<div><label style="font-size:12px;color:var(--text-secondary);">风险偏好</label><select class="form-input" data-field="risk" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:14px;margin-top:4px;"><option value="稳健">稳健</option><option value="激进">激进</option><option value="保守">保守</option></select></div>' +
      '<div><label style="font-size:12px;color:var(--text-secondary);">入场依据</label><select class="form-input" data-field="entry" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:14px;margin-top:4px;"><option value="技术面">技术面</option><option value="估值分位">估值分位</option><option value="技术面+估值">技术面+估值</option><option value="事件驱动">事件驱动</option></select></div>' +
      '<div><label style="font-size:12px;color:var(--text-secondary);">止盈方式</label><select class="form-input" data-field="take_profit" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:14px;margin-top:4px;"><option value="固定价位">固定价位</option><option value="移动止盈">移动止盈</option><option value="分批止盈">分批止盈</option><option value="条件止盈">条件止盈</option></select></div>' +
      '<div><label style="font-size:12px;color:var(--text-secondary);">止损纪律</label><select class="form-input" data-field="stop_loss" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:14px;margin-top:4px;"><option value="固定价位">固定价位</option><option value="百分比止损">百分比止损</option><option value="条件止损">条件止损</option><option value="不止损">不止损</option></select></div>' +
      '<div><label style="font-size:12px;color:var(--text-secondary);">特别关注（选填）</label><input type="text" class="form-input" data-field="notes" placeholder="" style="width:100%;padding:8px 10px;border:1px solid var(--border);border-radius:6px;font-size:14px;margin-top:4px;"></div>' +
      '</div>';
    container.appendChild(row);
  };

  window.submitCustomStrategy = function() {
    var rows = document.querySelectorAll('.account-row');
    var accounts = [];
    var valid = true;
    rows.forEach(function(row) {
      var account = {};
      row.querySelectorAll('.form-input').forEach(function(input) {
        account[input.getAttribute('data-field')] = input.value;
      });
      if (!account.type) valid = false;
      accounts.push(account);
    });
    if (!valid) {
      alert('请至少为每个账户选择策略类型');
      return;
    }

    var config = {
      accounts: accounts,
      coordination: {
        independence: document.getElementById('coord-independence').value,
        totalLimit: document.getElementById('coord-total-limit').value,
        profitFlow: document.getElementById('coord-profit-flow').value,
        totalStop: document.getElementById('coord-total-stop').value,
        priority: document.getElementById('coord-priority').value,
        lossFlow: document.getElementById('coord-loss').value,
      },
      totalAmount: document.getElementById('total-amount').value,
      extraNotes: document.getElementById('extra-notes').value,
    };

    var btn = document.getElementById('submit-strategy-btn');
    var loading = document.getElementById('strategy-loading');
    var result = document.getElementById('strategy-result');
    btn.disabled = true;
    btn.style.opacity = '0.5';
    loading.style.display = 'block';
    result.innerHTML = '';

    var symbol = window.location.pathname.split('/').pop();
    if (!symbol || symbol.length < 4) symbol = stockSymbol;

    fetch('/api/mixed-strategy/' + symbol, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ config: JSON.stringify(config) })
    })
    .then(function(resp) {
      if (!resp.ok) throw new Error('请求失败');
      var reader = resp.body.getReader();
      var decoder = new TextDecoder('utf-8');
      var html = '';
      function read() {
        return reader.read().then(function(chunk) {
          if (chunk.done) {
            result.innerHTML = html;
            if (typeof marked !== 'undefined') {
              result.querySelectorAll('.md-text').forEach(function(el) {
                el.innerHTML = marked.parse(el.textContent);
              });
            }
            loading.style.display = 'none';
            btn.disabled = false;
            btn.style.opacity = '1';
            return;
          }
          html += decoder.decode(chunk.value, { stream: true });
          result.innerHTML = html;
          if (typeof marked !== 'undefined') {
            result.querySelectorAll('.md-text').forEach(function(el) {
              el.innerHTML = marked.parse(el.textContent);
            });
          }
          window.scrollTo(0, document.body.scrollHeight);
          return read();
        });
      }
      return read();
    })
    .catch(function(err) {
      loading.style.display = 'none';
      btn.disabled = false;
      btn.style.opacity = '1';
      result.innerHTML = '<div style="padding:16px;background:#FFF3E0;border-radius:8px;color:#E65100;">分析生成失败：' + err.message + '</div>';
    });
  };
})();

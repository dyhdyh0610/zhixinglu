from datetime import datetime

POSITIVE_SIGNALS = {"突破MA20", "放量", "主力流入", "创新高", "均线多头", "超卖"}
NEGATIVE_SIGNALS = {"跌破MA20", "缩量", "主力流出", "创新低", "均线空头", "超买"}

DIRECTION_LABELS = {"buy": "买入", "sell": "卖出", "add": "加仓", "reduce": "减仓"}
DIRECTION_COLORS = {"buy": "#D97757", "sell": "#7A9B6E", "add": "#D97757", "reduce": "#7A9B6E"}


def _signal_class(signal: str) -> str:
    if signal in POSITIVE_SIGNALS:
        return "positive"
    if signal in NEGATIVE_SIGNALS:
        return "negative"
    return ""


def _sentiment_bar_color(score: int) -> str:
    if score < 30:
        return "#c0513f"
    if score < 45:
        return "#3f6a8b"
    if score < 55:
        return "#8b7355"
    if score < 70:
        return "#b8860b"
    return "#c0513f"


def _sentiment_label_cls(label: str) -> str:
    mapping = {"恐慌": "fear", "偏冷": "cool", "中性": "neutral", "偏暖": "warm", "贪婪": "greed"}
    return mapping.get(label, "neutral")


DIAGNOSIS_CSS = '''
<style>
.diag-container { max-width:720px; margin:0 auto; padding:32px 24px; }
.diag-header { text-align:center; margin-bottom:28px; }
.diag-header .label { font-size:12px; color:var(--accent-gold, #C9A961); letter-spacing:3px; margin-bottom:8px; }
.diag-header h1 { font-size:24px; color:var(--accent-green, #2C3E2D); font-family:var(--font-serif, 'Noto Serif SC', serif); }
.diag-header .divider { width:40px; height:2px; background:var(--accent-gold, #C9A961); margin:12px auto; }
.diag-date { font-size:13px; color:var(--text-secondary, #6B6B6B); margin-top:8px; }

.diag-trade-badge { display:inline-block; font-size:14px; font-weight:bold; padding:4px 14px; border-radius:6px; margin-bottom:12px; }
.diag-trade-badge.buy { background:#fde8e4; color:#D97757; }
.diag-trade-badge.sell { background:#e8f5e3; color:#7A9B6E; }

.diag-trade-summary { font-size:16px; color:var(--text-primary, #2A2A2A); font-family:var(--font-serif, 'Noto Serif SC', serif); margin-bottom:8px; }

.diag-data-cards { display:grid; grid-template-columns:repeat(3,1fr); gap:10px; margin-bottom:24px; }
.diag-data-card { background:#fff; border-radius:8px; padding:12px; text-align:center; box-shadow:0 1px 3px rgba(0,0,0,0.06); }
.diag-data-card .label { font-size:11px; color:var(--text-secondary, #6B6B6B); }
.diag-data-card .value { font-size:16px; font-weight:bold; font-family:var(--font-mono, 'IBM Plex Mono', monospace); }
.diag-data-card .sub { font-size:11px; color:var(--text-secondary, #6B6B6B); }
.diag-data-card .value.up { color:var(--up-color, #D97757); }
.diag-data-card .value.down { color:var(--down-color, #7A9B6E); }

.diag-section { margin-bottom:20px; }
.diag-section-title { display:flex; align-items:center; gap:8px; margin:28px 0 16px; }
.diag-section-title .icon { font-size:18px; }
.diag-section-title h2 { font-size:16px; font-family:var(--font-serif, 'Noto Serif SC', serif); color:var(--accent-green, #2C3E2D); font-weight:bold; margin:0; }

.diag-card { background:#fff; border-radius:10px; padding:16px; margin-bottom:12px; box-shadow:0 1px 4px rgba(0,0,0,0.05); border-left:4px solid var(--border, #e0d8cc); }
.diag-card.value { border-left-color:#C9A961; }
.diag-card.position { border-left-color:#7A9B6E; }
.diag-card.timing { border-left-color:#D97757; }
.diag-card.market { border-left-color:#3f6a8b; }

.diag-card-row { display:flex; justify-content:space-between; align-items:baseline; margin-bottom:6px; }
.diag-card-label { font-size:13px; color:var(--text-secondary, #6B6B6B); }
.diag-card-value { font-size:14px; font-weight:bold; color:var(--text-primary, #2A2A2A); }

.diag-diagnosis { font-size:14px; color:var(--text-primary, #2A2A2A); line-height:1.7; margin-top:12px; padding-top:12px; border-top:1px solid #f0ebe3; }

.diag-signals { display:flex; flex-wrap:wrap; gap:6px; margin:8px 0; }
.diag-signal { font-size:11px; padding:2px 8px; border-radius:10px; background:#f0ebe3; color:var(--text-secondary, #6B6B6B); }
.diag-signal.positive { background:#e8f5e3; color:#4a7c3f; }
.diag-signal.negative { background:#fde8e4; color:#c0513f; }

.diag-score-bar { display:flex; gap:3px; align-items:center; }
.diag-score-dot { width:10px; height:10px; border-radius:50%; background:#e0d8cc; }
.diag-score-dot.filled { background:var(--accent-gold, #C9A961); }

.diag-conclusion { border-top:2px solid var(--accent-gold, #C9A961); padding-top:24px; margin-top:32px; }
.diag-conclusion h2 { font-size:18px; font-family:var(--font-serif, 'Noto Serif SC', serif); color:var(--accent-green, #2C3E2D); margin-bottom:16px; }
.diag-conclusion-text { font-size:15px; line-height:1.8; color:var(--text-primary, #2A2A2A); }

.diag-full-report-btn { display:inline-block; margin-top:12px; padding:8px 16px; font-size:13px; color:var(--accent-gold, #C9A961); border:1px solid var(--accent-gold, #C9A961); border-radius:6px; cursor:pointer; text-decoration:none; transition:all 0.2s; }
.diag-full-report-btn:hover { background:var(--accent-gold, #C9A961); color:#fff; }

.diag-disclaimer { margin-top:24px; padding:12px; background:var(--bg-secondary, #f8f5f0); border-radius:6px; font-size:12px; color:#999; text-align:center; }

.diag-market-temp { background:#fff; border-radius:10px; padding:16px; box-shadow:0 1px 4px rgba(0,0,0,0.05); }
.diag-temp-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:12px; }
.diag-temp-score { font-size:28px; font-weight:bold; font-family:var(--font-mono, 'IBM Plex Mono', monospace); color:var(--accent-green, #2C3E2D); }
.diag-temp-label { font-size:13px; padding:3px 10px; border-radius:10px; }
.diag-temp-label.fear { background:#fde8e4; color:#c0513f; }
.diag-temp-label.cool { background:#e3eef5; color:#3f6a8b; }
.diag-temp-label.neutral { background:#f0ebe3; color:#8b7355; }
.diag-temp-label.warm { background:#fdf3e4; color:#b8860b; }
.diag-temp-label.greed { background:#fde8e4; color:#c0513f; }
.diag-temp-bar { height:6px; background:#f0ebe3; border-radius:3px; overflow:hidden; margin-bottom:12px; }
.diag-temp-bar-fill { height:100%; border-radius:3px; transition:width 0.5s ease; }

@media (max-width:768px) {
  .diag-container { padding:20px 16px; }
  .diag-header h1 { font-size:20px; }
  .diag-data-cards { grid-template-columns:repeat(2,1fr); gap:8px; }
  .diag-card { padding:14px; }
  .diag-conclusion h2 { font-size:16px; }
}
</style>
'''


def diagnosis_html_head(date_str: str = "") -> str:
    if not date_str:
        date_str = datetime.now().strftime("%Y年%m月%d日")
    return f'''{DIAGNOSIS_CSS}
<div class="diag-container">
  <div class="diag-header">
    <div class="label">TRADE DIAGNOSIS</div>
    <h1>交易诊断报告</h1>
    <div class="divider"></div>
    <div class="diag-date">{date_str}</div>
  </div>
'''


def diagnosis_overview_html(trade_intent: dict, holdings: list[dict],
                            target_quote: dict, holdings_quotes: dict,
                            profiles: dict) -> str:
    direction = trade_intent.get("direction", "buy")
    dir_label = DIRECTION_LABELS.get(direction, "买入")
    dir_cls = "buy" if direction in ("buy", "add") else "sell"
    stock_name = trade_intent.get("name", "")
    stock_code = trade_intent.get("code", "")
    shares = trade_intent.get("shares", 0)
    target_price = trade_intent.get("target_price")

    tq = target_quote.get(stock_code, {})
    current_price = tq.get("price", 0)
    price = target_price if target_price else current_price
    trade_amount = price * shares

    total_before = 0
    for h in holdings:
        q = holdings_quotes.get(h["code"], {}) if holdings_quotes else {}
        p = q.get("price", 0)
        total_before += p * h["shares"]

    if direction in ("buy", "add"):
        total_after = total_before + trade_amount
    else:
        total_after = total_before - trade_amount

    position_before = 0
    existing = next((h for h in holdings if h["code"] == stock_code), None)
    if existing and holdings_quotes:
        eq = holdings_quotes.get(stock_code, {})
        ep = eq.get("price", 0)
        position_before = (ep * existing["shares"] / total_before * 100) if total_before > 0 else 0

    if direction in ("buy", "add"):
        new_mv = (existing["shares"] * current_price + trade_amount) if existing else trade_amount
    else:
        new_mv = max(0, (existing["shares"] * current_price - trade_amount)) if existing else 0
    position_after = (new_mv / total_after * 100) if total_after > 0 else 0

    target_profile = profiles.get(stock_code, {}) if profiles else {}
    industry = target_profile.get("industry", "未知")

    price_display = f"¥{price:,.2f}" if price else "当前价"
    pos_before_str = f"{position_before:.1f}%" if position_before > 0 else "0%"

    return f'''<div style="text-align:center;margin-bottom:20px;">
  <span class="diag-trade-badge {dir_cls}">{dir_label}</span>
  <div class="diag-trade-summary">{stock_name}({stock_code}) {shares}股 × {price_display}</div>
</div>
<div class="diag-data-cards">
  <div class="diag-data-card"><div class="label">交易金额</div><div class="value">¥{trade_amount:,.0f}</div></div>
  <div class="diag-data-card"><div class="label">仓位占比</div><div class="value">{pos_before_str}→{position_after:.1f}%</div></div>
  <div class="diag-data-card"><div class="label">所属行业</div><div class="value" style="font-size:14px;">{industry}</div></div>
</div>
'''


def _section_title(icon: str, title: str) -> str:
    return f'<div class="diag-section-title"><span class="icon">{icon}</span><h2>{title}</h2></div>\n'


def diagnosis_value_html(value_json: dict, target_code: str) -> str:
    html = _section_title("📊", "股票价值")
    level = value_json.get("valuation_level", "未知")
    pe = value_json.get("pe_info", "暂无")
    pb = value_json.get("pb_info", "暂无")
    dcf = value_json.get("dcf_range", "暂无")
    target_assess = value_json.get("target_price_assessment", "")
    research = value_json.get("research_consensus", "暂无")
    core_logic = value_json.get("core_logic", "")
    diagnosis = value_json.get("diagnosis", "")
    risk = value_json.get("risk_point", "")

    html += f'''<div class="diag-card value">
  <div class="diag-card-row"><span class="diag-card-label">估值水平</span><span class="diag-card-value">{level}</span></div>
  <div class="diag-card-row"><span class="diag-card-label">PE(TTM)</span><span class="diag-card-value">{pe}</span></div>
  <div class="diag-card-row"><span class="diag-card-label">PB</span><span class="diag-card-value">{pb}</span></div>
  <div class="diag-card-row"><span class="diag-card-label">DCF参考价</span><span class="diag-card-value">{dcf}</span></div>
  {f'<div class="diag-card-row"><span class="diag-card-label">目标价评估</span><span class="diag-card-value">{target_assess}</span></div>' if target_assess else ''}
  <div class="diag-card-row"><span class="diag-card-label">研报共识</span><span class="diag-card-value">{research}</span></div>
  {f'<div class="diag-card-row"><span class="diag-card-label">核心逻辑</span><span class="diag-card-value">{core_logic}</span></div>' if core_logic else ''}
  <div class="diag-diagnosis">{diagnosis}</div>
  {f'<div style="font-size:12px;color:#c0513f;margin-top:8px;">⚠ {risk}</div>' if risk else ''}
  <a class="diag-full-report-btn" href="#" onclick="Router.navigate(\'/{target_code}\');return false;">查看完整分析报告 →</a>
</div>
'''
    return html


def diagnosis_position_html(position_json: dict) -> str:
    html = _section_title("📐", "仓位管理")
    pos_change = position_json.get("position_change", "")
    industry_conc = position_json.get("industry_concentration", "")
    top3 = position_json.get("top3_concentration", "")
    corr_risk = position_json.get("correlation_risk", "")
    score = position_json.get("diversification_score", 3)
    diagnosis = position_json.get("diagnosis", "")
    suggestion = position_json.get("suggestion", "")

    dots = "".join(
        f'<span class="diag-score-dot {"filled" if i < score else ""}"></span>'
        for i in range(5)
    )

    html += f'''<div class="diag-card position">
  <div class="diag-card-row"><span class="diag-card-label">仓位变化</span><span class="diag-card-value">{pos_change}</span></div>
  <div class="diag-card-row"><span class="diag-card-label">行业集中度</span><span class="diag-card-value">{industry_conc}</span></div>
  <div class="diag-card-row"><span class="diag-card-label">前3大持仓集中度</span><span class="diag-card-value">{top3}</span></div>
  {f'<div class="diag-card-row"><span class="diag-card-label">相关性风险</span><span class="diag-card-value">{corr_risk}</span></div>' if corr_risk else ''}
  <div class="diag-card-row"><span class="diag-card-label">分散化评分</span><div class="diag-score-bar">{dots}</div></div>
  <div class="diag-diagnosis">{diagnosis}</div>
  {f'<div style="font-size:13px;color:var(--accent-gold);margin-top:8px;">{suggestion}</div>' if suggestion else ''}
</div>
'''
    return html


def diagnosis_timing_html(timing_json: dict) -> str:
    html = _section_title("⏰", "交易时机")
    signals = timing_json.get("signals", [])
    trend = timing_json.get("trend_description", "")
    support = timing_json.get("support_price", 0)
    resistance = timing_json.get("resistance_price", 0)
    volume = timing_json.get("volume_analysis", "")
    catalyst = timing_json.get("catalyst", "")
    risk_event = timing_json.get("risk_event", "")
    score = timing_json.get("timing_score", 3)
    diagnosis = timing_json.get("diagnosis", "")

    signals_html = "".join(
        f'<span class="diag-signal {_signal_class(s)}">{s}</span>' for s in signals
    )
    dots = "".join(
        f'<span class="diag-score-dot {"filled" if i < score else ""}"></span>'
        for i in range(5)
    )

    support_str = f"¥{support:,.2f}" if support else "暂无"
    resist_str = f"¥{resistance:,.2f}" if resistance else "暂无"

    html += f'''<div class="diag-card timing">
  <div class="diag-signals">{signals_html}</div>
  <div class="diag-card-row"><span class="diag-card-label">趋势</span><span class="diag-card-value">{trend}</span></div>
  <div class="diag-card-row"><span class="diag-card-label">支撑位</span><span class="diag-card-value">{support_str}</span></div>
  <div class="diag-card-row"><span class="diag-card-label">压力位</span><span class="diag-card-value">{resist_str}</span></div>
  <div class="diag-card-row"><span class="diag-card-label">成交量</span><span class="diag-card-value">{volume}</span></div>
  {f'<div class="diag-card-row"><span class="diag-card-label">潜在催化剂</span><span class="diag-card-value">{catalyst}</span></div>' if catalyst else ''}
  {f'<div class="diag-card-row"><span class="diag-card-label">风险事件</span><span class="diag-card-value" style="color:#c0513f;">{risk_event}</span></div>' if risk_event else ''}
  <div class="diag-card-row"><span class="diag-card-label">时机评分</span><div class="diag-score-bar">{dots}</div></div>
  <div class="diag-diagnosis">{diagnosis}</div>
</div>
'''
    return html


def diagnosis_market_html(market_json: dict) -> str:
    html = _section_title("🌡️", "市场环境")
    score = market_json.get("sentiment_score", 50)
    label = market_json.get("sentiment_label", "中性")
    summary = market_json.get("market_summary", "")
    sector = market_json.get("sector_status", "")
    north = market_json.get("north_flow", "")
    macro_risk = market_json.get("macro_risk", "")
    diagnosis = market_json.get("diagnosis", "")

    bar_color = _sentiment_bar_color(score)
    label_cls = _sentiment_label_cls(label)

    html += f'''<div class="diag-market-temp">
  <div class="diag-temp-header">
    <span class="diag-temp-score">{score}</span>
    <span class="diag-temp-label {label_cls}">{label}</span>
  </div>
  <div class="diag-temp-bar"><div class="diag-temp-bar-fill" style="width:{score}%;background:{bar_color};"></div></div>
  <div style="font-size:14px;color:var(--text-primary);line-height:1.6;margin-bottom:12px;">{summary}</div>
  <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;font-size:13px;">
    {f'<div style="display:flex;justify-content:space-between;padding:6px 10px;background:#faf7f2;border-radius:6px;"><span style="color:var(--text-secondary);">目标板块</span><span style="font-weight:bold;">{sector}</span></div>' if sector else ''}
    {f'<div style="display:flex;justify-content:space-between;padding:6px 10px;background:#faf7f2;border-radius:6px;"><span style="color:var(--text-secondary);">北向资金</span><span style="font-weight:bold;">{north}</span></div>' if north else ''}
  </div>
  {f'<div style="font-size:12px;color:#c0513f;margin-top:10px;">⚠ {macro_risk}</div>' if macro_risk else ''}
  <div class="diag-diagnosis">{diagnosis}</div>
</div>
'''
    return html


def diagnosis_sector_html(sector_json: dict) -> str:
    html = _section_title("📊", "板块环境")
    industry_trend = sector_json.get("industry_trend", "")
    industry_valuation = sector_json.get("industry_valuation", "")
    competitors = sector_json.get("competitors", [])
    target_rank = sector_json.get("target_rank", 0)
    target_rank_total = sector_json.get("target_rank_total", 0)
    rank_reason = sector_json.get("rank_reason", "")
    score = sector_json.get("sector_score", 3)
    diagnosis = sector_json.get("diagnosis", "")

    dots = "".join(
        f'<span class="diag-score-dot {"filled" if i < score else ""}"></span>'
        for i in range(5)
    )

    comp_rows = ""
    for c in competitors[:5]:
        comp_rows += f'''<tr>
          <td style="padding:8px 10px;font-weight:500;">{c.get("name","")}</td>
          <td style="padding:8px 10px;color:#4a7c3f;">{c.get("advantage","")}</td>
          <td style="padding:8px 10px;color:#c0513f;">{c.get("disadvantage","")}</td>
        </tr>'''

    rank_html = ""
    if target_rank and target_rank_total:
        rank_html = f'<div class="diag-card-row"><span class="diag-card-label">板块排名</span><span class="diag-card-value">第{target_rank}/{target_rank_total}名</span></div>'

    html += f'''<div class="diag-card" style="border-left-color:#8b7355;">
  <div style="font-size:14px;line-height:1.7;margin-bottom:12px;">{industry_trend}</div>
  <div class="diag-card-row"><span class="diag-card-label">行业估值</span><span class="diag-card-value">{industry_valuation}</span></div>
  {f'<div style="margin:12px 0;"><div style="font-size:13px;color:var(--text-secondary);margin-bottom:8px;">竞争对手对比</div><table style="width:100%;font-size:13px;border-collapse:collapse;"><thead><tr style="border-bottom:1px solid #f0ebe3;"><th style="padding:6px 10px;text-align:left;color:var(--text-secondary);font-weight:normal;">公司</th><th style="padding:6px 10px;text-align:left;color:var(--text-secondary);font-weight:normal;">优势</th><th style="padding:6px 10px;text-align:left;color:var(--text-secondary);font-weight:normal;">劣势</th></tr></thead><tbody>{comp_rows}</tbody></table></div>' if comp_rows else ''}
  {rank_html}
  {f'<div class="diag-card-row"><span class="diag-card-label">排名理由</span><span class="diag-card-value">{rank_reason}</span></div>' if rank_reason else ''}
  <div class="diag-card-row"><span class="diag-card-label">板块评分</span><div class="diag-score-bar">{dots}</div></div>
  <div class="diag-diagnosis">{diagnosis}</div>
</div>
'''
    return html


def diagnosis_conclusion_html(conclusion_data) -> str:
    if isinstance(conclusion_data, str):
        escaped = conclusion_data.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        return f'''<div class="diag-conclusion">
  <h2>综合诊断</h2>
  <div class="diag-conclusion-text">{escaped}</div>
</div>
'''

    conclusion = conclusion_data.get("conclusion", "")
    key_points = conclusion_data.get("key_points", [])
    score = conclusion_data.get("confidence_score", 3)
    reason = conclusion_data.get("confidence_reason", "")

    stars = "".join("★" if i < score else "☆" for i in range(5))
    if score >= 4:
        star_color = "#10b981"
        star_label = "高信心"
    elif score == 3:
        star_color = "#f59e0b"
        star_label = "中等信心"
    else:
        star_color = "#ef4444"
        star_label = "低信心"

    points_html = ""
    if key_points:
        points_html = '<ul class="diag-conclusion-points">' + "".join(
            f'<li>{p}</li>' for p in key_points
        ) + '</ul>'

    escaped_conclusion = conclusion.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    escaped_reason = reason.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    return f'''<div class="diag-conclusion">
  <h2>综合诊断</h2>
  <div class="diag-confidence">
    <span class="diag-confidence-stars" style="color:{star_color};">{stars}</span>
    <span class="diag-confidence-label" style="background:{star_color}1a;color:{star_color};">{star_label}</span>
  </div>
  <div class="diag-confidence-reason">{escaped_reason}</div>
  <div class="diag-conclusion-text">{escaped_conclusion}</div>
  {points_html}
</div>
'''


def diagnosis_html_footer() -> str:
    return '''<div class="diag-disclaimer">以上诊断由AI基于公开数据生成，仅供参考，不构成投资建议。投资有风险，决策需谨慎。</div>
</div>'''

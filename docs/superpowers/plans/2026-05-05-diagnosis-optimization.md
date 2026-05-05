# 交易诊断报告优化 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 优化交易诊断报告，增加加载进度条、复用个股分析报告、板块环境模块、信心指数、预设追问hints

**Architecture:** 后端 diagnosis_generator 新增进度标记 yield、报告查询/生成/纯文本提取、板块环境 LLM 调用、结论 JSON 化；前端解析进度标记和 hints 标记，渲染步骤进度条和可点击 hint 标签

**Tech Stack:** Python/FastAPI, asyncio, OpenAI SDK, akshare, vanilla JS, CSS

---

## File Structure

| File | Responsibility |
|------|---------------|
| `app/models/history.py` | 新增 `get_recent_report()` 按 stock_code + 2天查询 |
| `app/data/diagnosis_data.py` | 新增板块数据获取（行业K线） |
| `app/ai/diagnosis_prompts.py` | 各 prompt 增加 report_context、新增 sector_prompt、改造 conclusion_prompt |
| `app/report/diagnosis_template.py` | 新增 sector_html、改造 conclusion_html |
| `app/report/diagnosis_generator.py` | 核心重构：进度标记、报告复用、板块环境步骤、结论JSON |
| `app/static/js/diagnosis.js` | 进度组件、hints 解析渲染 |
| `app/static/css/diagnosis.css` | 进度条、hints、星级样式 |

---

### Task 1: 新增 history 查询函数

**Files:**
- Modify: `app/models/history.py`

- [ ] **Step 1: 新增 `get_recent_report()` 函数**

在 `app/models/history.py` 末尾添加：

```python
def get_recent_report(stock_code: str, days: int = 2) -> dict | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT * FROM analysis_history WHERE stock_code = ? AND created_at > datetime('now', ? || ' days') ORDER BY created_at DESC LIMIT 1",
        (stock_code, f"-{days}"),
    ).fetchone()
    conn.close()
    return dict(row) if row else None
```

- [ ] **Step 2: Commit**

```bash
git add app/models/history.py
git commit -m "feat(diagnosis): add get_recent_report query for 2-day cache lookup"
```

---

### Task 2: 新增板块数据获取

**Files:**
- Modify: `app/data/diagnosis_data.py`

- [ ] **Step 1: 在 `fetch_diagnosis_data()` 中新增板块数据获取**

在 `app/data/diagnosis_data.py` 顶部新增 import：

```python
from datetime import datetime, timedelta
import akshare as ak
```

在文件末尾新增函数：

```python
def _get_industry_data(stock_code: str) -> dict | None:
    try:
        stock_info = ak.stock_individual_info_em(symbol=stock_code)
        industry = None
        for _, row in stock_info.iterrows():
            if row.iloc[0] == "行业":
                industry = row.iloc[1]
                break
        if not industry:
            return None

        end_date = datetime.now().strftime("%Y%m%d")
        start_date = (datetime.now() - timedelta(days=30)).strftime("%Y%m%d")
        hist = ak.stock_board_industry_hist_em(
            symbol=industry, period="日k",
            start_date=start_date, end_date=end_date, adjust=""
        )
        change_pct = 0
        if hist is not None and not hist.empty and len(hist) >= 2:
            first_close = float(hist.iloc[0]["收盘"])
            last_close = float(hist.iloc[-1]["收盘"])
            change_pct = (last_close - first_close) / first_close * 100 if first_close else 0

        return {
            "industry_name": industry,
            "industry_kline": hist.tail(20).to_dict("records") if hist is not None and not hist.empty else [],
            "industry_change_pct": round(change_pct, 2),
        }
    except Exception:
        return None
```

- [ ] **Step 2: 在 `fetch_diagnosis_data` 的 tasks 中新增板块数据任务**

在 `tasks["latest_letter"]` 行之后添加：

```python
    tasks["sector_data"] = asyncio.to_thread(_get_industry_data, target_code)
```

- [ ] **Step 3: Commit**

```bash
git add app/data/diagnosis_data.py
git commit -m "feat(diagnosis): add industry/sector data fetching via akshare"
```

---

### Task 3: 改造 diagnosis_prompts.py

**Files:**
- Modify: `app/ai/diagnosis_prompts.py`

- [ ] **Step 1: 各维度 prompt 增加 report_context 参数**

修改 `value_diagnosis_prompt` 签名和内容：

```python
def value_diagnosis_prompt(stock_name: str, financials_str: str, valuation_str: str,
                           research_str: str, trade_intent_str: str,
                           report_context: str = "") -> list[dict]:
    context_section = ""
    if report_context:
        context_section = f"\n\n---\n以下是该股票的完整分析报告，供你参考（请从中提取与价值分析相关的信息辅助判断）：\n{report_context}"

    return [
        {"role": "system", "content": DIAGNOSIS_SYSTEM},
        {"role": "user", "content": f"""对"{stock_name}"进行股票价值诊断，输出JSON对象。

交易意图：{trade_intent_str}

财务数据：
{financials_str}

估值数据：
{valuation_str}

近期研报：
{research_str}{context_section}

输出格式（严格JSON对象）：
{{
  "valuation_level": "偏低/合理/偏高",
  "pe_info": "PE(TTM)数值及历史分位描述",
  "pb_info": "PB数值及历史分位描述",
  "dcf_range": "DCF参考价区间描述",
  "target_price_assessment": "目标价格相对估值的评估（一句话）",
  "research_consensus": "近期研报一致观点（一句话）",
  "core_logic": "当前市场对该股的核心投资逻辑（一句话）",
  "diagnosis": "综合价值诊断（50-100字，辩证分析，指出关键点）",
  "risk_point": "最大的价值风险点（一句话）"
}}

直接输出JSON对象。"""}
    ]
```

同样修改 `position_diagnosis_prompt`、`timing_diagnosis_prompt`、`market_diagnosis_prompt`，各自增加 `report_context: str = ""` 参数，在 user content 末尾追加 context_section（timing 和 market 的提示语改为"请从中提取与时机/市场分析相关的信息"）。

- [ ] **Step 2: 新增 sector_diagnosis_prompt**

在 `market_diagnosis_prompt` 之后添加：

```python
def sector_diagnosis_prompt(stock_name: str, industry_name: str, industry_data_str: str,
                            stock_info_str: str, trade_intent_str: str,
                            report_context: str = "") -> list[dict]:
    context_section = ""
    if report_context:
        context_section = f"\n\n---\n以下是该股票的完整分析报告，供你参考：\n{report_context}"

    return [
        {"role": "system", "content": DIAGNOSIS_SYSTEM},
        {"role": "user", "content": f"""请搜索"{stock_name}"所在的"{industry_name}"行业的最新动态和主要竞争对手信息，然后分析板块环境，输出JSON对象。

交易意图：{trade_intent_str}

公司信息：
{stock_info_str}

行业近期数据：
{industry_data_str}{context_section}

分析要求：
1. 分析该行业近期走势及原因
2. 判断行业整体估值水平
3. 识别3-5个主要竞争对手，对比核心优劣势
4. 给出该公司在板块中的投资价值排名

输出格式（严格JSON对象）：
{{
  "industry_trend": "行业近期走势描述及原因（50-80字）",
  "industry_valuation": "行业估值水平描述（一句话）",
  "competitors": [
    {{
      "name": "竞争对手名称",
      "ticker": "股票代码",
      "advantage": "核心优势（一句话）",
      "disadvantage": "核心劣势（一句话）"
    }}
  ],
  "target_rank": 2,
  "target_rank_total": 5,
  "rank_reason": "排名理由（一句话）",
  "sector_score": 1-5,
  "diagnosis": "从板块角度对这笔交易的诊断（50-100字）"
}}

字段说明：
- target_rank：目标公司在竞争对手中的投资价值排名（1=最值得投资）
- target_rank_total：参与排名的公司总数
- sector_score：1=行业环境很差不适合投资，3=中性，5=行业景气度高适合投资

直接输出JSON对象。"""}
    ]
```

- [ ] **Step 3: 改造 conclusion_prompt 为 JSON 输出**

替换现有的 `conclusion_prompt` 函数：

```python
def conclusion_prompt(trade_intent_str: str, value_analysis: str,
                      position_analysis: str, timing_analysis: str,
                      market_analysis: str, sector_analysis: str = "",
                      user_reason: str = "") -> list[dict]:
    reason_part = f"\n用户的交易理由：{user_reason}" if user_reason else ""
    sector_part = f"\n\n板块环境分析：\n{sector_analysis}" if sector_analysis else ""
    return [
        {"role": "system", "content": """你是"知行录"的AI交易诊断师。基于前面各维度的分析，给出综合诊断结论。

输出要求：
- 必须输出合法JSON对象
- 客观、辩证、有深度
- 不给"买/不买"的直接建议
- 指出最值得关注的2-3个点
- 如果有明显风险，直接指出
- 语气像一个理性的朋友在提醒你
- suggested_questions 必须与本次具体交易高度相关，从用户视角出发"""},
        {"role": "user", "content": f"""综合以下各维度分析，给出这笔交易的综合诊断结论。

交易意图：{trade_intent_str}{reason_part}

股票价值分析：
{value_analysis}

仓位管理分析：
{position_analysis}

交易时机分析：
{timing_analysis}

市场环境分析：
{market_analysis}{sector_part}

输出格式（严格JSON对象）：
{{
  "conclusion": "综合诊断结论（150-250字，先一句话概括，再列2-3个关键点，最后一句话总结）",
  "key_points": ["关键点1", "关键点2", "关键点3"],
  "confidence_score": 1-5,
  "confidence_reason": "信心评分理由（一句话）",
  "suggested_questions": [
    "与本次交易高度相关的追问问题1",
    "与本次交易高度相关的追问问题2",
    "与本次交易高度相关的追问问题3"
  ]
}}

字段说明：
- confidence_score：1=强烈不建议（多维度风险），2=多数维度不支持，3=支持和反对各半，4=大部分支持（少量风险），5=多维度强烈支持
- suggested_questions：从用户视角出发，看完整个分析后最可能追问的3个问题，覆盖不同角度（风险、操作建议、替代方案等），必须包含具体股票名称或数据

直接输出JSON对象。"""}
    ]
```

- [ ] **Step 4: Commit**

```bash
git add app/ai/diagnosis_prompts.py
git commit -m "feat(diagnosis): add report_context to prompts, sector prompt, JSON conclusion"
```

---

### Task 4: 新增板块环境 HTML 模板 + 改造结论模板

**Files:**
- Modify: `app/report/diagnosis_template.py`

- [ ] **Step 1: 新增 `diagnosis_sector_html()` 函数**

在 `diagnosis_market_html` 函数之后添加：

```python
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
```

- [ ] **Step 2: 改造 `diagnosis_conclusion_html()` 支持 JSON 输入和星级**

替换现有的 `diagnosis_conclusion_html` 函数：

```python
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
```

- [ ] **Step 3: Commit**

```bash
git add app/report/diagnosis_template.py
git commit -m "feat(diagnosis): add sector HTML template and confidence star rating in conclusion"
```

---

### Task 5: 重构 diagnosis_generator.py（核心）

**Files:**
- Modify: `app/report/diagnosis_generator.py`

- [ ] **Step 1: 新增 imports 和纯文本提取函数**

在文件顶部修改 imports：

```python
import asyncio
import json
import re
from datetime import datetime
from typing import AsyncGenerator

from app.data.diagnosis_data import fetch_diagnosis_data
from app.data.letter_data import get_market_overview
from app.ai.llm_client import chat, chat_with_search
from app.ai.diagnosis_prompts import (
    value_diagnosis_prompt, position_diagnosis_prompt,
    timing_diagnosis_prompt, market_diagnosis_prompt,
    sector_diagnosis_prompt, conclusion_prompt,
)
from app.report.diagnosis_template import (
    diagnosis_html_head, diagnosis_overview_html,
    diagnosis_value_html, diagnosis_position_html,
    diagnosis_timing_html, diagnosis_market_html,
    diagnosis_sector_html, diagnosis_conclusion_html,
    diagnosis_html_footer, DIRECTION_LABELS,
)
from app.report.letter_generator import _parse_json, _calc_portfolio_summary
from app.report.generator import generate_report
from app.models.history import get_recent_report, save_report
from app.data.stock_search import search_stock
```

在 `_build_trade_intent_str` 函数之前添加：

```python
def _extract_report_text(html_content: str) -> str:
    text = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', '\n', text)
    text = re.sub(r'&[a-zA-Z]+;', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


async def _get_or_generate_report(stock_code: str, stock_name: str, market: str) -> str:
    cached = await asyncio.to_thread(get_recent_report, stock_code, 2)
    if cached:
        return _extract_report_text(cached["html_content"])

    chunks = []
    async for chunk in generate_report(stock_code):
        chunks.append(chunk)
    full_html = "".join(chunks)

    try:
        await asyncio.to_thread(save_report, stock_code, stock_name, full_html, market)
    except Exception:
        pass

    return _extract_report_text(full_html)
```

- [ ] **Step 2: 重写 `generate_diagnosis()` 主函数**

替换整个 `generate_diagnosis` 函数：

```python
async def generate_diagnosis(trade_intent: dict, holdings: list[dict]) -> AsyncGenerator[str, None]:
    date_str = datetime.now().strftime("%Y年%m月%d日")
    yield diagnosis_html_head(date_str)

    # Progress: loading report
    yield "<!-- PROGRESS:loading_report -->"
    stock_code = trade_intent["code"]
    stock_name = trade_intent["name"]
    market = trade_intent.get("market", "A")
    report_context = ""
    try:
        report_context = await _get_or_generate_report(stock_code, stock_name, market)
    except Exception:
        pass

    # Progress: fetching data
    yield "<!-- PROGRESS:fetching_data -->"
    data = await fetch_diagnosis_data(trade_intent, holdings)

    target_quote = data.get("target_quote") or {}
    holdings_quotes = data.get("holdings_quotes") or {}
    profiles = data.get("holdings_profiles") or {}

    yield diagnosis_overview_html(trade_intent, holdings, target_quote, holdings_quotes, profiles)

    trade_str = _build_trade_intent_str(trade_intent)
    financials_str = _build_financials_str(data)
    valuation_str = _build_valuation_str(data)
    research_str = _build_research_str(data)
    kline_str = _build_kline_str(data)
    detail_str = _build_detail_str(data)
    news_str = _build_news_str(data)
    market_str = _build_market_str(data)
    portfolio_str = _build_portfolio_str(holdings, holdings_quotes, profiles)

    # Card: Value diagnosis
    yield "<!-- PROGRESS:value -->"
    value_analysis = ""
    try:
        raw = await asyncio.to_thread(
            chat, value_diagnosis_prompt(trade_intent["name"], financials_str, valuation_str, research_str, trade_str, report_context)
        )
        value_json = _parse_json(raw)
        value_analysis = raw
    except Exception:
        value_json = {"valuation_level": "未知", "diagnosis": "价值分析暂时无法生成"}
    yield diagnosis_value_html(value_json, trade_intent["code"])

    # Card: Position diagnosis
    yield "<!-- PROGRESS:position -->"
    post_trade_str = f"交易后组合（假设执行{trade_str}）:\n{portfolio_str}\n+ 本次交易"
    position_analysis = ""
    try:
        raw = await asyncio.to_thread(
            chat, position_diagnosis_prompt(trade_str, portfolio_str, post_trade_str, report_context)
        )
        position_json = _parse_json(raw)
        position_analysis = raw
    except Exception:
        position_json = {"diagnosis": "仓位分析暂时无法生成", "diversification_score": 3}
    yield diagnosis_position_html(position_json)

    # Card: Timing diagnosis
    yield "<!-- PROGRESS:timing -->"
    timing_analysis = ""
    try:
        raw = await asyncio.to_thread(
            chat_with_search, timing_diagnosis_prompt(trade_intent["name"], kline_str, detail_str, news_str, trade_str, report_context)
        )
        timing_json = _parse_json(raw)
        timing_analysis = raw
    except Exception:
        timing_json = {"signals": [], "timing_score": 3, "diagnosis": "时机分析暂时无法生成"}
    yield diagnosis_timing_html(timing_json)

    # Card: Market diagnosis
    yield "<!-- PROGRESS:market -->"
    market_analysis = ""
    try:
        raw = await asyncio.to_thread(
            chat_with_search, market_diagnosis_prompt(market_str, portfolio_str, trade_str, report_context)
        )
        market_json = _parse_json(raw)
        market_analysis = raw
    except Exception:
        market_json = {"sentiment_score": 50, "sentiment_label": "中性", "diagnosis": "市场分析暂时无法生成"}
    yield diagnosis_market_html(market_json)

    # Card: Sector diagnosis
    yield "<!-- PROGRESS:sector -->"
    sector_analysis = ""
    sector_data = data.get("sector_data") or {}
    if sector_data:
        industry_name = sector_data.get("industry_name", "")
        industry_data_str = f"行业：{industry_name}\n近30日涨跌幅：{sector_data.get('industry_change_pct', 0):+.2f}%"
        stock_info = data.get("stock_info")
        stock_info_str = f"公司：{trade_intent['name']}，行业：{industry_name}"
        if stock_info and hasattr(stock_info, 'to_string'):
            stock_info_str += f"\n{stock_info.to_string()[:500]}"
    else:
        industry_name = profiles.get(stock_code, {}).get("industry", "未知") if profiles else "未知"
        industry_data_str = f"行业：{industry_name}\n（行业详细数据暂不可用）"
        stock_info_str = f"公司：{trade_intent['name']}，行业：{industry_name}"

    try:
        raw = await asyncio.to_thread(
            chat_with_search, sector_diagnosis_prompt(
                trade_intent["name"], industry_name, industry_data_str,
                stock_info_str, trade_str, report_context
            )
        )
        sector_json = _parse_json(raw)
        sector_analysis = raw
    except Exception:
        sector_json = {"industry_trend": "暂无数据", "diagnosis": "板块分析暂时无法生成", "sector_score": 3, "competitors": []}
    yield diagnosis_sector_html(sector_json)

    # Conclusion
    yield "<!-- PROGRESS:conclusion -->"
    user_reason = trade_intent.get("reason", "")
    conclusion_data = None
    try:
        raw = await asyncio.to_thread(
            chat, conclusion_prompt(trade_str, value_analysis, position_analysis,
                                    timing_analysis, market_analysis, sector_analysis, user_reason)
        )
        conclusion_data = _parse_json(raw)
    except Exception:
        pass

    if conclusion_data and isinstance(conclusion_data, dict) and "conclusion" in conclusion_data:
        yield diagnosis_conclusion_html(conclusion_data)
        hints = conclusion_data.get("suggested_questions", [])
        if hints and isinstance(hints, list):
            yield f'<!-- HINTS:{json.dumps(hints, ensure_ascii=False)} -->'
    else:
        fallback_text = raw if 'raw' in dir() else "综合诊断暂时无法生成，请稍后重试。"
        yield diagnosis_conclusion_html(fallback_text)

    yield diagnosis_html_footer()
```

- [ ] **Step 3: Commit**

```bash
git add app/report/diagnosis_generator.py
git commit -m "feat(diagnosis): full generator rewrite with progress, report context, sector, confidence"
```

---

### Task 6: 前端进度组件和 Hints 渲染

**Files:**
- Modify: `app/static/js/diagnosis.js`

- [ ] **Step 1: 重写 `renderGenerating()` 方法，增加进度解析和 hints**

替换 `renderGenerating` 方法：

```javascript
async renderGenerating() {
  const app = document.getElementById('app');
  const raw = sessionStorage.getItem('diag_trade_intent');
  if (!raw) { Router.navigate('/diagnosis'); return; }
  const tradeIntent = JSON.parse(raw);
  const holdings = Store.getHeldStocks().map(s => ({
    code: s.code, name: s.name, shares: s.shares,
    cost_price: s.cost_price, market: s.market || 'A'
  }));

  const dirLabel = DIRECTION_LABELS[tradeIntent.direction] || '买入';

  const STEPS = [
    {id: 'loading_report', label: '加载分析报告'},
    {id: 'fetching_data', label: '获取市场数据'},
    {id: 'value', label: '价值诊断'},
    {id: 'position', label: '仓位诊断'},
    {id: 'timing', label: '择时诊断'},
    {id: 'market', label: '市场诊断'},
    {id: 'sector', label: '板块环境'},
    {id: 'conclusion', label: '综合判断'},
  ];

  app.innerHTML = `
    <div style="max-width:720px;margin:0 auto;padding:20px 16px;">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;">
        <span style="color:var(--accent-gold);cursor:pointer;font-size:14px;" onclick="Router.navigate('/diagnosis')">← 返回</span>
      </div>
      <div id="diag-progress" class="diag-progress">
        <div class="diag-progress-title">交易诊断生成中</div>
        <div class="diag-progress-subtitle">${dirLabel} ${tradeIntent.name} ${tradeIntent.shares}股</div>
        <div class="diag-progress-steps" id="diag-progress-steps">
          ${STEPS.map(s => `<div class="diag-step pending" id="diag-step-${s.id}"><span class="diag-step-icon">○</span><span>${s.label}</span></div>`).join('')}
        </div>
      </div>
      <div id="diag-report-content" style="display:none;"></div>
      <div id="diag-chat-container" style="display:none;">
        <div class="diag-chat-area">
          <h3>对这个诊断有疑问？继续问我</h3>
          <div id="diag-hints"></div>
          <div class="diag-chat-messages" id="diag-chat-messages"></div>
          <div class="diag-chat-input-row">
            <input type="text" class="diag-chat-input" id="diag-chat-input" placeholder="输入你的问题..." onkeydown="if(event.key==='Enter')Diagnosis._sendChat()">
            <button class="diag-chat-send" onclick="Diagnosis._sendChat()">发送</button>
          </div>
        </div>
      </div>
    </div>`;

  this._chatHistory = [];
  this._currentDiagnosisId = null;
  this._hints = [];
  let firstCardShown = false;

  const updateProgress = (stepId) => {
    STEPS.forEach(s => {
      const el = document.getElementById(`diag-step-${s.id}`);
      if (!el) return;
      const idx = STEPS.findIndex(x => x.id === stepId);
      const myIdx = STEPS.findIndex(x => x.id === s.id);
      if (myIdx < idx) {
        el.className = 'diag-step completed';
        el.querySelector('.diag-step-icon').textContent = '✓';
      } else if (myIdx === idx) {
        el.className = 'diag-step active';
        el.querySelector('.diag-step-icon').innerHTML = '<span class="diag-spinner"></span>';
      }
    });
  };

  try {
    const resp = await fetch('/api/diagnosis/generate', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({trade_intent: tradeIntent, holdings})
    });
    const reader = resp.body.getReader();
    const decoder = new TextDecoder();
    let html = '';
    const contentEl = document.getElementById('diag-report-content');
    const progressEl = document.getElementById('diag-progress');

    while (true) {
      const {done, value} = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value, {stream: true});
      html += chunk;

      // Parse progress markers
      const progressMatch = chunk.match(/<!-- PROGRESS:(\w+) -->/g);
      if (progressMatch) {
        progressMatch.forEach(m => {
          const id = m.match(/PROGRESS:(\w+)/)[1];
          updateProgress(id);
        });
      }

      // Parse hints marker
      const hintsMatch = html.match(/<!-- HINTS:(.*?) -->/);
      if (hintsMatch) {
        try { this._hints = JSON.parse(hintsMatch[1]); } catch {}
      }

      // Show content (strip progress/hints markers for display)
      const displayHtml = html.replace(/<!-- PROGRESS:\w+ -->/g, '').replace(/<!-- HINTS:.*? -->/g, '');
      if (displayHtml.includes('diag-card') && !firstCardShown) {
        firstCardShown = true;
        progressEl.classList.add('diag-progress-collapsed');
        contentEl.style.display = 'block';
      }
      contentEl.innerHTML = displayHtml;
    }

    // All done
    progressEl.style.display = 'none';
    contentEl.style.display = 'block';
    document.getElementById('diag-chat-container').style.display = 'block';

    // Render hints
    if (this._hints.length > 0) {
      this._renderHints();
    }

    const histResp = await fetch('/api/diagnosis/history');
    const histData = await histResp.json();
    if (histData.length > 0) {
      this._currentDiagnosisId = histData[0].id;
    }
  } catch (e) {
    document.getElementById('diag-progress').style.display = 'none';
    document.getElementById('diag-report-content').style.display = 'block';
    document.getElementById('diag-report-content').innerHTML =
      '<p class="text-secondary" style="text-align:center;margin-top:60px;">诊断生成失败，请重试</p>';
  }
},
```

- [ ] **Step 2: 新增 `_renderHints()` 方法**

在 `_sendChat` 方法之前添加：

```javascript
_renderHints() {
  const container = document.getElementById('diag-hints');
  if (!container || !this._hints.length) return;
  container.innerHTML = `
    <div class="diag-hints-wrapper">
      <div class="diag-hints-label">你可能想问：</div>
      ${this._hints.map(q => `<div class="diag-hint-item" onclick="Diagnosis._clickHint(this, '${q.replace(/'/g, "\\'")}')">${q}</div>`).join('')}
    </div>`;
},

_clickHint(el, question) {
  document.getElementById('diag-hints').style.display = 'none';
  document.getElementById('diag-chat-input').value = question;
  this._sendChat();
},
```

- [ ] **Step 3: Commit**

```bash
git add app/static/js/diagnosis.js
git commit -m "feat(diagnosis): add progress stepper UI and clickable hint questions"
```

---

### Task 7: CSS 样式（进度条、星级、Hints）

**Files:**
- Modify: `app/static/css/diagnosis.css`

- [ ] **Step 1: 在文件末尾追加新样式**

```css
/* Progress stepper */
.diag-progress {
  text-align: center;
  padding: 32px 0;
}

.diag-progress-title {
  font-size: 18px;
  font-family: var(--font-serif, 'Noto Serif SC', serif);
  color: var(--accent-green, #2C3E2D);
  margin-bottom: 4px;
}

.diag-progress-subtitle {
  font-size: 14px;
  color: var(--text-secondary, #6B6B6B);
  margin-bottom: 24px;
}

.diag-progress-steps {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  max-width: 280px;
  margin: 0 auto;
  gap: 10px;
}

.diag-step {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  color: var(--text-secondary, #6B6B6B);
  transition: all 0.3s;
}

.diag-step.completed {
  color: #10b981;
}

.diag-step.completed .diag-step-icon {
  color: #10b981;
  font-weight: bold;
}

.diag-step.active {
  color: var(--text-primary, #2A2A2A);
  font-weight: 500;
}

.diag-step-icon {
  width: 18px;
  text-align: center;
  font-size: 13px;
}

.diag-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid var(--accent-gold, #C9A961);
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.diag-progress-collapsed {
  padding: 12px 0;
}

.diag-progress-collapsed .diag-progress-steps {
  flex-direction: row;
  flex-wrap: wrap;
  max-width: 100%;
  gap: 6px;
  justify-content: center;
}

.diag-progress-collapsed .diag-progress-title,
.diag-progress-collapsed .diag-progress-subtitle {
  display: none;
}

.diag-progress-collapsed .diag-step {
  font-size: 12px;
  gap: 4px;
}

/* Confidence stars */
.diag-confidence {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.diag-confidence-stars {
  font-size: 22px;
  letter-spacing: 2px;
}

.diag-confidence-label {
  font-size: 13px;
  padding: 3px 10px;
  border-radius: 10px;
  font-weight: 500;
}

.diag-confidence-reason {
  font-size: 13px;
  color: var(--text-secondary, #6B6B6B);
  margin-bottom: 16px;
}

.diag-conclusion-points {
  list-style: none;
  padding: 0;
  margin: 12px 0 0;
}

.diag-conclusion-points li {
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary, #2A2A2A);
  padding: 4px 0 4px 16px;
  position: relative;
}

.diag-conclusion-points li::before {
  content: "•";
  position: absolute;
  left: 0;
  color: var(--accent-gold, #C9A961);
}

/* Hints */
.diag-hints-wrapper {
  margin-bottom: 16px;
}

.diag-hints-label {
  font-size: 13px;
  color: var(--text-secondary, #6B6B6B);
  margin-bottom: 8px;
}

.diag-hint-item {
  display: block;
  width: 100%;
  padding: 10px 14px;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--accent-green, #2C3E2D);
  background: #faf7f2;
  border: 1px solid var(--border, #e0d8cc);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  text-align: left;
}

.diag-hint-item:hover {
  background: #f0ebe3;
  border-color: var(--accent-gold, #C9A961);
}
```

- [ ] **Step 2: Commit**

```bash
git add app/static/css/diagnosis.css
git commit -m "feat(diagnosis): add CSS for progress stepper, confidence stars, and hint buttons"
```

---

### Task 8: 验证和修复

- [ ] **Step 1: 启动开发服务器验证**

```bash
python3 run.py
```

在浏览器中测试：
1. 进入交易诊断页面，选择一只股票，填写表单，点击"开始诊断"
2. 验证进度条逐步更新
3. 验证卡片逐步出现后进度条收起
4. 验证新增的"板块环境"卡片正常渲染
5. 验证结论卡片显示星级和信心标签
6. 验证聊天区域上方出现 3 个 hint 按钮
7. 点击 hint 按钮验证自动发送消息
8. 验证生成的个股分析报告出现在历史分析列表中

- [ ] **Step 2: 修复发现的问题**

根据测试结果修复任何 bug。

- [ ] **Step 3: Final commit**

```bash
git add -A
git commit -m "fix(diagnosis): address issues found during manual testing"
```

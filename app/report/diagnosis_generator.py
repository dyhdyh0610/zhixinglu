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


def _build_trade_intent_str(trade_intent: dict) -> str:
    direction = DIRECTION_LABELS.get(trade_intent.get("direction", "buy"), "买入")
    name = trade_intent.get("name", "")
    code = trade_intent.get("code", "")
    shares = trade_intent.get("shares", 0)
    target_price = trade_intent.get("target_price")
    price_str = f"，目标价¥{target_price:.2f}" if target_price else ""
    return f"{direction} {name}({code}) {shares}股{price_str}"


def _build_financials_str(data: dict) -> str:
    fs = data.get("financial_summary")
    if fs is None or (hasattr(fs, 'empty') and fs.empty):
        return "暂无财务数据"
    lines = []
    latest = fs.iloc[-1]
    for col in ["营业总收入", "净利润", "销售毛利率", "净资产收益率",
                "营业总收入同比增长率", "净利润同比增长率"]:
        v = latest.get(col, "")
        if v:
            lines.append(f"{col}: {v}")
    return "\n".join(lines) if lines else "暂无财务数据"


def _build_valuation_str(data: dict) -> str:
    val_data = data.get("valuation") or {}
    lines = []
    for key, display in [("pe", "PE(TTM)"), ("pb", "PB")]:
        df = val_data.get(key)
        if df is None or df.empty:
            continue
        series = df["value"]
        current = float(series.iloc[-1])
        hist_min = float(series.min())
        hist_max = float(series.max())
        percentile = (series < current).sum() / len(series) * 100
        lines.append(f"{display}: {current:.1f}, 历史区间[{hist_min:.1f}, {hist_max:.1f}], 当前{percentile:.0f}%分位")
    return "\n".join(lines) if lines else "暂无估值数据"


def _build_research_str(data: dict) -> str:
    reports = data.get("research")
    if reports is None or (hasattr(reports, 'empty') and reports.empty):
        return "暂无研报数据"
    lines = []
    for _, row in reports.head(3).iterrows():
        title = str(row.get("报告名称", row.iloc[0] if len(row) > 0 else ""))
        org = str(row.get("机构", ""))
        rating = str(row.get("东财评级", ""))
        lines.append(f"- {title}（{org}）{f'评级:{rating}' if rating and rating != 'nan' else ''}")
    return "\n".join(lines)


def _build_kline_str(data: dict) -> str:
    kline = data.get("kline_30d")
    if kline is None or (hasattr(kline, 'empty') and kline.empty):
        return "暂无K线数据"
    closes = kline["close"].tolist()
    highs = kline["high"].tolist()
    lows = kline["low"].tolist()
    volumes = kline["volume"].tolist() if "volume" in kline.columns else []
    change = (closes[-1] - closes[0]) / closes[0] * 100 if closes[0] else 0
    lines = [
        f"30日涨跌幅: {change:+.1f}%",
        f"最高价: {max(highs):.2f}, 最低价: {min(lows):.2f}",
        f"最新收盘: {closes[-1]:.2f}",
    ]
    if volumes and len(volumes) >= 5:
        avg_vol = sum(volumes[-5:]) / 5
        prev_avg = sum(volumes[-10:-5]) / 5 if len(volumes) >= 10 else avg_vol
        vol_change = (avg_vol - prev_avg) / prev_avg * 100 if prev_avg > 0 else 0
        lines.append(f"近5日成交量变化: {vol_change:+.1f}%")
    return "\n".join(lines)


def _build_detail_str(data: dict) -> str:
    detail = data.get("stock_detail") or {}
    lines = []
    for ma in ["MA5", "MA10", "MA20"]:
        if ma in detail:
            lines.append(f"{ma}: ¥{detail[ma]:.2f}")
    if "主力净流入" in detail:
        lines.append(f"主力净流入: {detail['主力净流入']/10000:.0f}万")
    if "成交量变化" in detail:
        lines.append(f"成交量变化: {detail['成交量变化']:+.1f}%")
    return "\n".join(lines) if lines else "暂无技术指标"


def _build_news_str(data: dict) -> str:
    news = data.get("news")
    if news is None or (hasattr(news, 'empty') and news.empty):
        return "暂无近期新闻"
    lines = []
    for _, row in news.head(10).iterrows():
        title = row.get("新闻标题", "")
        date = row.get("发布时间", "")
        if title:
            lines.append(f"- [{date}] {title}")
    return "\n".join(lines) if lines else "暂无近期新闻"


def _build_market_str(data: dict) -> str:
    market = data.get("market_overview") or {}
    lines = []
    for idx in ["上证指数", "深证成指", "创业板指", "沪深300"]:
        d = market.get(idx)
        if d:
            lines.append(f"{idx}: {d.get('最新价', 'N/A')} ({d.get('涨跌幅', 'N/A')}%)")
    north = market.get("北向资金")
    if north:
        lines.append(f"北向资金净流入: {north.get('净流入', 'N/A')}亿")
    top = market.get("领涨板块", [])
    if top:
        lines.append("领涨板块: " + ", ".join(f"{b['板块名称']}({b['涨跌幅']}%)" for b in top[:3]))
    return "\n".join(lines) if lines else "市场数据暂不可用"


def _build_portfolio_str(holdings: list[dict], quotes: dict, profiles: dict) -> str:
    if not holdings:
        return "用户当前无持仓"
    lines = []
    total = 0
    for h in holdings:
        q = quotes.get(h["code"], {}) if quotes else {}
        p = q.get("price", 0)
        total += p * h["shares"]
    for h in holdings:
        q = quotes.get(h["code"], {}) if quotes else {}
        p = q.get("price", 0)
        mv = p * h["shares"]
        pct = (mv / total * 100) if total > 0 else 0
        prof = profiles.get(h["code"], {}) if profiles else {}
        industry = prof.get("industry", "")
        lines.append(f"- {h['name']}({h['code']}): {h['shares']}股, 市值¥{mv:,.0f}, 占比{pct:.1f}%, 行业:{industry}")
    return "\n".join(lines)


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
    raw = ""
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
        fallback_text = raw if raw else "综合诊断暂时无法生成，请稍后重试。"
        yield diagnosis_conclusion_html(fallback_text)

    yield diagnosis_html_footer()

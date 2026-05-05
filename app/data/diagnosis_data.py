import asyncio
from datetime import datetime, timedelta

import akshare as ak

from app.data.portfolio_data import get_batch_quotes, get_stock_profiles
from app.data.financial_data import (
    get_financial_summary, get_stock_info, get_dividend_yield,
)
from app.data.valuation_data import get_valuation_history
from app.data.market_data import get_stock_kline
from app.data.news_data import get_stock_news, get_research_reports, get_profit_forecast
from app.data.letter_data import get_market_overview, get_stock_detail
from app.models.letter import get_latest_letter


async def fetch_diagnosis_data(trade_intent: dict, holdings: list[dict]) -> dict:
    target_code = trade_intent["code"]
    target_market = trade_intent.get("market", "A")

    tasks = {
        "target_quote": asyncio.to_thread(get_batch_quotes, [target_code], target_market),
        "financial_summary": asyncio.to_thread(get_financial_summary, target_code, target_market),
        "stock_info": asyncio.to_thread(get_stock_info, target_code, target_market),
        "valuation": asyncio.to_thread(get_valuation_history, target_code, target_market),
        "research": asyncio.to_thread(get_research_reports, target_code, target_market),
        "profit_forecast": asyncio.to_thread(get_profit_forecast, target_code, target_market),
        "dividend_yield": asyncio.to_thread(get_dividend_yield, target_code, target_market),
        "kline_30d": asyncio.to_thread(get_stock_kline, target_code, 30, target_market),
        "stock_detail": asyncio.to_thread(get_stock_detail, target_code, target_market),
        "news": asyncio.to_thread(get_stock_news, target_code, target_market),
        "market_overview": asyncio.to_thread(get_market_overview),
    }

    if holdings:
        a_codes = [h["code"] for h in holdings if h.get("market", "A") != "HK"]
        hk_codes = [h["code"] for h in holdings if h.get("market", "A") == "HK"]
        if a_codes:
            tasks["holdings_quotes_a"] = asyncio.to_thread(get_batch_quotes, a_codes, "A")
            tasks["holdings_profiles_a"] = asyncio.to_thread(get_stock_profiles, a_codes, "A")
        if hk_codes:
            tasks["holdings_quotes_hk"] = asyncio.to_thread(get_batch_quotes, hk_codes, "HK")
            tasks["holdings_profiles_hk"] = asyncio.to_thread(get_stock_profiles, hk_codes, "HK")

    tasks["latest_letter"] = asyncio.to_thread(get_latest_letter)

    if target_market == "HK":
        tasks["sector_data"] = asyncio.to_thread(_get_hk_industry_data, target_code)
    else:
        tasks["sector_data"] = asyncio.to_thread(_get_industry_data, target_code)

    keys = list(tasks.keys())
    results = await asyncio.gather(*tasks.values(), return_exceptions=True)

    data = {}
    for key, result in zip(keys, results):
        data[key] = None if isinstance(result, Exception) else result

    # Merge split holdings data
    data["holdings_quotes"] = {
        **(data.pop("holdings_quotes_a", None) or {}),
        **(data.pop("holdings_quotes_hk", None) or {}),
    }
    data["holdings_profiles"] = {
        **(data.pop("holdings_profiles_a", None) or {}),
        **(data.pop("holdings_profiles_hk", None) or {}),
    }

    data["_target_code"] = target_code
    data["_target_market"] = target_market
    return data


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


def _get_hk_industry_data(stock_code: str) -> dict | None:
    """港股行业数据：从 yfinance 获取行业分类，无板块K线。"""
    try:
        from app.data.financial_data import _yf_info_safe
        info = _yf_info_safe(stock_code)
        industry = info.get("industry", "")
        sector = info.get("sector", "")
        if industry or sector:
            return {
                "industry_name": industry or sector,
                "industry_kline": [],
                "industry_change_pct": 0,
            }
    except Exception:
        pass
    return None

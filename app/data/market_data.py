import akshare as ak
import pandas as pd
from datetime import datetime, timedelta

_kline_cache: dict[str, pd.DataFrame] = {}


def _get_kline_tx(symbol: str) -> pd.DataFrame:
    """获取K线数据（腾讯数据源，不依赖mini_racer）。"""
    if symbol in _kline_cache:
        return _kline_cache[symbol]

    prefix = "sh" if symbol.startswith("6") else "sz"
    end = datetime.now().strftime("%Y%m%d")
    start = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
    df = ak.stock_zh_a_hist_tx(symbol=f"{prefix}{symbol}", start_date=start, end_date=end)
    df["date"] = pd.to_datetime(df["date"])
    _kline_cache[symbol] = df
    return df


def get_stock_kline(symbol: str, days: int = 30) -> pd.DataFrame:
    """获取近N个交易日的K线数据。"""
    df = _get_kline_tx(symbol)
    return df.tail(days).reset_index(drop=True)


def get_realtime_quote(symbol: str) -> dict:
    """获取股票最新行情。"""
    try:
        df = _get_kline_tx(symbol)
        if df.empty:
            return {}
        latest = df.iloc[-1]
        return {
            "最新价": float(latest["close"]),
            "开盘": float(latest["open"]),
            "最高": float(latest["high"]),
            "最低": float(latest["low"]),
            "成交量": float(latest.get("amount", 0)),
            "日期": str(latest["date"]),
        }
    except Exception:
        return {}

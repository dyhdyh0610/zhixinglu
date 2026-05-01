import akshare as ak
import pandas as pd


def get_valuation_history(symbol: str) -> dict:
    """获取PE/PB历史数据（百度数据源）。"""
    result = {}
    for indicator, key in [("市盈率(TTM)", "pe"), ("市净率", "pb")]:
        try:
            df = ak.stock_zh_valuation_baidu(symbol=symbol, indicator=indicator, period="全部")
            df["date"] = pd.to_datetime(df["date"])
            df = df.dropna(subset=["value"])
            df["value"] = pd.to_numeric(df["value"], errors="coerce")
            df = df.dropna(subset=["value"])
            result[key] = df
        except Exception:
            result[key] = pd.DataFrame()
    return result

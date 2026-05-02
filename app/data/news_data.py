import akshare as ak
import pandas as pd


def get_stock_news(symbol: str) -> pd.DataFrame:
    """获取个股近期新闻。"""
    try:
        df = ak.stock_news_em(symbol=symbol)
        return df.head(30)
    except Exception:
        return pd.DataFrame()


def get_research_reports(symbol: str) -> pd.DataFrame:
    """获取个股近期研报。"""
    try:
        df = ak.stock_research_report_em(symbol=symbol)
        return df.head(10)
    except Exception:
        return pd.DataFrame()


def get_stock_announcements(symbol: str) -> pd.DataFrame:
    """获取个股公告（用于财报附录链接）。"""
    try:
        df = ak.stock_notice_report(symbol=symbol)
        return df.head(20)
    except Exception:
        return pd.DataFrame()


def get_profit_forecast(symbol: str) -> dict:
    """获取个股盈利预测数据（同花顺+东方财富）。"""
    result = {}

    try:
        result["eps"] = ak.stock_profit_forecast_ths(symbol=symbol, indicator="预测年报每股收益")
    except Exception:
        result["eps"] = pd.DataFrame()

    try:
        result["net_profit"] = ak.stock_profit_forecast_ths(symbol=symbol, indicator="预测年报净利润")
    except Exception:
        result["net_profit"] = pd.DataFrame()

    try:
        em_df = ak.stock_profit_forecast_em(symbol="")
        stock_row = em_df[em_df["代码"] == symbol]
        result["ratings"] = stock_row.iloc[0].to_dict() if not stock_row.empty else {}
    except Exception:
        result["ratings"] = {}

    return result

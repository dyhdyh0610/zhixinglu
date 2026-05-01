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

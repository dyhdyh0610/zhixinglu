import akshare as ak
import pandas as pd


def get_financial_summary(symbol: str) -> pd.DataFrame:
    """获取综合财务摘要（同花顺数据源），包含ROE、毛利率、增速等。"""
    df = ak.stock_financial_abstract_ths(symbol=symbol)
    return df


def get_cash_flow_sheet(symbol: str) -> pd.DataFrame:
    """获取现金流量表数据（新浪数据源）。"""
    df = ak.stock_financial_report_sina(stock=symbol, symbol="现金流量表")
    return df


def get_profit_sheet(symbol: str) -> pd.DataFrame:
    """获取利润表数据（新浪数据源）。"""
    df = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
    return df


def get_dividend_yield(symbol: str) -> pd.DataFrame:
    """获取个股历史分红率（同花顺数据源）。返回含 报告期、股息率 列的 DataFrame。"""
    try:
        df = ak.stock_fhps_detail_ths(symbol=symbol)
    except Exception:
        return pd.DataFrame()

    rows = []
    for _, row in df.iterrows():
        period = str(row.get("报告期", ""))
        rate = str(row.get("税前分红率", ""))
        if rate == "--" or rate.strip() == "":
            continue
        rate_val = rate.replace("%", "").strip()
        try:
            rate_num = float(rate_val)
        except ValueError:
            continue

        if "年报" in period:
            year = period.replace("年报", "").strip()
            rows.append({"报告期": f"{year}-12-31", "股息率": rate_num})
        elif "中报" in period:
            year = period.replace("中报", "").strip()
            rows.append({"报告期": f"{year}-06-30", "股息率": rate_num})

    return pd.DataFrame(rows) if rows else pd.DataFrame()


def get_stock_info(symbol: str) -> dict:
    """获取个股基本信息。"""
    info = {}
    try:
        df = get_financial_summary(symbol)
        if not df.empty:
            latest = df.iloc[-1]
            info["每股净资产"] = latest.get("每股净资产", "")
            info["净资产收益率"] = latest.get("净资产收益率", "")
            info["销售毛利率"] = latest.get("销售毛利率", "")
            info["营业总收入"] = latest.get("营业总收入", "")
            info["净利润"] = latest.get("净利润", "")
    except Exception:
        pass

    try:
        from app.data.market_data import get_realtime_quote
        quote = get_realtime_quote(symbol)
        if quote:
            price = quote.get("最新价", 0)
            shares = quote.get("流通股本", 0)
            if price and shares:
                info["总市值"] = price * shares
                info["最新价"] = price
    except Exception:
        pass

    return info

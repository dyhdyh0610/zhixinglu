import akshare as ak
import pandas as pd
import logging
import sys
from typing import Optional

logger = logging.getLogger(__name__)


def _get_industry_name(symbol: str) -> Optional[str]:
    """获取股票所属行业名称。"""
    try:
        stock_info = ak.stock_individual_info_em(symbol=symbol)
        for _, row in stock_info.iterrows():
            item = row.get("item")
            value = row.get("value")
            if item == "行业":
                return value
    except Exception:
        logger.warning("Failed to get industry name for %s", symbol, exc_info=True)
    return None


def _get_industry_cons(industry_name: str) -> Optional[pd.DataFrame]:
    """获取行业成分股列表，返回包含代码、名称、市值等列的 DataFrame。"""
    try:
        df = ak.stock_board_industry_cons_em(symbol=industry_name)
        if df is None or df.empty:
            return None
        return df
    except Exception:
        logger.warning("Failed to get industry constituents for %s", industry_name, exc_info=True)
    return None


def _get_realtime_peers(peer_codes: list[str]) -> pd.DataFrame:
    """获取一批股票的实时行情（含PE/PB/总市值）。"""
    try:
        all_df = ak.stock_zh_a_spot_em()
        if all_df is None or all_df.empty:
            return pd.DataFrame()
        # 筛选出目标代码
        mask = all_df["代码"].isin(peer_codes)
        return all_df[mask]
    except Exception:
        logger.warning("Failed to get realtime quotes for peers", exc_info=True)
    return pd.DataFrame()


def get_peer_companies(symbol: str) -> str:
    """获取同行业 3-5 个主要竞争对手的信息。

    返回格式化的 markdown 字符串，包含：公司名称、代码、PE、PB、总市值。
    如果获取失败，返回空字符串（静默降级）。
    """
    try:
        industry = _get_industry_name(symbol)
        if not industry:
            return ""

        cons_df = _get_industry_cons(industry)
        if cons_df is None or cons_df.empty:
            return ""

        # 按总市值排序，排除自身
        if "代码" in cons_df.columns:
            cons_df = cons_df[cons_df["代码"] != symbol]
        elif "序号" in cons_df.columns:
            # 有些版本用序号列
            pass

        # 总市值排序（降序）
        if "总市值" in cons_df.columns:
            cons_df["总市值_num"] = pd.to_numeric(cons_df["总市值"], errors="coerce")
            cons_df = cons_df.dropna(subset=["总市值_num"]).sort_values("总市值_num", ascending=False)
        elif "最新价" in cons_df.columns:
            cons_df["最新价_num"] = pd.to_numeric(cons_df["最新价"], errors="coerce")
            cons_df = cons_df.dropna(subset=["最新价_num"]).sort_values("最新价_num", ascending=False)
        else:
            return ""

        # 取前 5 个
        top5 = cons_df.head(5)

        # 获取这些股票的实时行情（PE/PB）
        peer_codes = top5["代码"].tolist() if "代码" in top5.columns else []
        if not peer_codes:
            return ""

        realtime_df = _get_realtime_peers(peer_codes)

        # 构建结果
        lines = ["| 公司名称 | 代码 | PE(TTM) | PB | 总市值 |", "|---|---|---|---|---|"]
        for _, row in top5.iterrows():
            code = str(row.get("代码", ""))
            name = str(row.get("名称", row.get("股票名称", "")))
            # 优先用实时行情中的 PE/PB
            rt_row = realtime_df[realtime_df["代码"] == code]
            if not rt_row.empty:
                rt = rt_row.iloc[0]
                pe = str(rt.get("市盈率-动态", "--"))
                pb = str(rt.get("市净率", "--"))
                mv = str(rt.get("总市值", row.get("总市值", "--")))
            else:
                pe = str(row.get("市盈率-动态", row.get("PE", "--")))
                pb = str(row.get("市净率", row.get("PB", "--")))
                mv = str(row.get("总市值", "--"))

            lines.append(f"| {name} | {code} | {pe} | {pb} | {mv} |")

        return "\n".join(lines)
    except Exception:
        print(f"[WARNING] get_peer_companies failed for {symbol}", file=sys.stderr)
        return ""


def get_industry_median(symbol: str, metric: str = "pe") -> Optional[float]:
    """获取行业 PE/PB/ROE 中位数。

    metric 支持 "pe"、"pb"、"roe"。
    获取失败返回 None。
    """
    try:
        industry = _get_industry_name(symbol)
        if not industry:
            return None

        cons_df = _get_industry_cons(industry)
        if cons_df is None or cons_df.empty:
            return None

        # 排除自身
        if "代码" in cons_df.columns:
            cons_df = cons_df[cons_df["代码"] != symbol]

        peer_codes = cons_df["代码"].tolist() if "代码" in cons_df.columns else []
        if not peer_codes:
            return None

        realtime_df = _get_realtime_peers(peer_codes)
        if realtime_df is None or realtime_df.empty:
            return None

        # 映射列名
        col_map = {
            "pe": "市盈率-动态",
            "pb": "市净率",
            "roe": None,  # ROE 不在实时行情中
        }

        if metric == "roe":
            # ROE 需要从财务摘要获取，这里简化处理：尝试用实时行情中的 ROE 列
            # akshare stock_zh_a_spot_em 一般不含 ROE，返回 None
            # 可改用财务数据，但为避免过多调用，此处返回 None
            return None

        col = col_map.get(metric)
        if not col or col not in realtime_df.columns:
            return None

        values = pd.to_numeric(realtime_df[col], errors="coerce").dropna()
        if values.empty:
            return None

        return float(values.median())
    except Exception:
        print(f"[WARNING] get_industry_median failed for {symbol} metric={metric}", file=sys.stderr)
        return None

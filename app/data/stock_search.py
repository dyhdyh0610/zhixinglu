import akshare as ak
import pandas as pd

_stock_list_cache: pd.DataFrame | None = None


def _get_stock_list() -> pd.DataFrame:
    global _stock_list_cache
    if _stock_list_cache is None:
        _stock_list_cache = ak.stock_info_a_code_name()
    return _stock_list_cache


def search_stock(query: str) -> list[dict]:
    """根据股票代码或名称模糊搜索，返回匹配结果列表。"""
    df = _get_stock_list()
    query = query.strip()
    if not query:
        return []

    results = []

    if query.isdigit():
        exact = df[df["code"] == query]
        if not exact.empty:
            results.extend(exact.to_dict("records"))
        partial = df[(df["code"].str.contains(query)) & (~df["code"].isin(exact["code"]))]
        results.extend(partial.head(10).to_dict("records"))
    else:
        matched = df[df["name"].str.contains(query, na=False)]
        results.extend(matched.head(10).to_dict("records"))

    return results[:10]

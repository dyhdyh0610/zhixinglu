from types import SimpleNamespace

from valueinvest.valuation.graham import GrahamNumber, GrahamFormula
from valueinvest.valuation.ddm import DDM
from valueinvest.valuation.growth import GARP
from valueinvest.valuation.dcf import ReverseDCF


DEFAULT_WACC = 0.10
DEFAULT_TERMINAL_GROWTH = 0.025
DEFAULT_AAA_YIELD = 4.0


def _parse_number(val):
    if val is None or str(val).strip() in ("", "--", "nan"):
        return None
    s = str(val).replace("%", "").replace(",", "").strip()
    if "亿" in s:
        s = s.replace("亿", "")
        try:
            return float(s) * 1e8
        except ValueError:
            return None
    if "万" in s:
        s = s.replace("万", "")
        try:
            return float(s) * 1e4
        except ValueError:
            return None
    try:
        return float(s)
    except ValueError:
        return None


def _extract_params(data: dict) -> dict:
    """从已有 akshare 数据中提取估值所需的全部参数。"""
    info = data.get("info") or {}
    fs = data.get("financial_summary")
    cashflow = data.get("cashflow")
    dividend_df = data.get("dividend_yield")
    quote = data.get("quote") or {}

    current_price = None
    try:
        current_price = float(quote.get("最新价", 0)) or None
    except (ValueError, TypeError):
        pass
    if not current_price:
        p = _parse_number(info.get("最新价"))
        if p and p > 0:
            current_price = p

    bvps = _parse_number(info.get("每股净资产"))

    total_shares = None
    try:
        mv = info.get("总市值")
        if mv and current_price and current_price > 0:
            mv_val = _parse_number(mv) if not isinstance(mv, (int, float)) else mv
            if mv_val and mv_val > 0:
                total_shares = mv_val / current_price
    except (ValueError, TypeError):
        pass

    if total_shares is None and current_price and current_price > 0:
        try:
            import akshare as ak
            symbol = data.get("_symbol", "")
            if symbol:
                mv_df = ak.stock_zh_valuation_baidu(symbol=symbol, indicator="总市值", period="近一年")
                if mv_df is not None and not mv_df.empty:
                    total_mv = float(mv_df.iloc[-1]["value"]) * 1e8
                    if total_mv > 0:
                        total_shares = total_mv / current_price
        except Exception:
            pass

    eps = None
    net_profit = _parse_number(info.get("净利润"))
    if net_profit and total_shares and total_shares > 0:
        eps = net_profit / total_shares
    if eps is None and fs is not None and not fs.empty:
        for col in fs.columns:
            if "每股收益" in str(col):
                val = _parse_number(fs.iloc[-1].get(col))
                if val:
                    eps = val
                    break

    growth_rates = []
    if fs is not None and not fs.empty and "净利润同比增长率" in fs.columns:
        for v in fs.tail(5)["净利润同比增长率"].tolist():
            n = _parse_number(v)
            if n is not None:
                growth_rates.append(n / 100 if abs(n) > 1 else n)
    if growth_rates:
        if len(growth_rates) >= 3:
            weights = list(range(1, len(growth_rates) + 1))
            total_w = sum(weights)
            avg_growth = sum(r * w for r, w in zip(growth_rates, weights)) / total_w
        else:
            avg_growth = sum(growth_rates) / len(growth_rates)
        avg_growth = max(min(avg_growth, 0.30), -0.10)
    else:
        avg_growth = None

    dividend_per_share = None
    dividend_growth_rate = None
    if dividend_df is not None and not dividend_df.empty and current_price:
        latest_yield = _parse_number(dividend_df.iloc[-1].get("股息率"))
        if latest_yield and latest_yield > 0:
            yield_decimal = latest_yield / 100 if latest_yield > 1 else latest_yield
            dividend_per_share = current_price * yield_decimal
        if len(dividend_df) >= 2:
            yields = []
            for _, row in dividend_df.iterrows():
                y = _parse_number(row.get("股息率"))
                if y and y > 0:
                    yields.append(y)
            if len(yields) >= 2:
                growth_vals = []
                for i in range(1, len(yields)):
                    if yields[i - 1] > 0:
                        growth_vals.append((yields[i] - yields[i - 1]) / yields[i - 1])
                if growth_vals:
                    dividend_growth_rate = sum(growth_vals) / len(growth_vals)
                    dividend_growth_rate = max(min(dividend_growth_rate, 0.15), -0.05)

    fcf = None
    if cashflow is not None and not cashflow.empty:
        operating_cf = None
        capex = None
        for col in cashflow.columns:
            if "经营活动产生的现金流量净额" in str(col):
                vals = cashflow[col].dropna().tolist()
                if vals:
                    try:
                        operating_cf = float(vals[-1])
                    except (ValueError, TypeError):
                        pass
                break
        for col in cashflow.columns:
            col_str = str(col)
            if "购建固定资产" in col_str or "购买固定资产" in col_str:
                vals = cashflow[col].dropna().tolist()
                if vals:
                    try:
                        capex = abs(float(vals[-1]))
                    except (ValueError, TypeError):
                        pass
                break
        if operating_cf is not None:
            fcf = operating_cf - (capex or 0)

    net_debt = 0.0

    return {
        "current_price": current_price,
        "eps": eps,
        "bvps": bvps,
        "growth_rate": avg_growth,
        "dividend_per_share": dividend_per_share,
        "dividend_growth_rate": dividend_growth_rate,
        "fcf": fcf,
        "total_shares": total_shares,
        "net_debt": net_debt,
        "wacc": DEFAULT_WACC,
        "terminal_growth": DEFAULT_TERMINAL_GROWTH,
        "aaa_yield": DEFAULT_AAA_YIELD,
    }


def _run_graham_number(params: dict) -> dict | None:
    eps = params.get("eps")
    bvps = params.get("bvps")
    price = params.get("current_price")
    if not eps or eps <= 0 or not bvps or bvps <= 0 or not price:
        return None
    stock = SimpleNamespace(eps=eps, bvps=bvps, current_price=price)
    try:
        result = GrahamNumber().calculate(stock)
        if result.fair_value and result.fair_value > 0:
            return {
                "method": "格雷厄姆数",
                "fair_value": result.fair_value,
                "premium_discount": result.premium_discount,
                "assessment": result.assessment,
            }
    except Exception:
        pass
    return None


def _run_ddm(params: dict) -> dict | None:
    dps = params.get("dividend_per_share")
    dg = params.get("dividend_growth_rate")
    price = params.get("current_price")
    wacc = params.get("wacc", DEFAULT_WACC)
    if not dps or dps <= 0 or dg is None or not price:
        return None
    stock = SimpleNamespace(
        dividend_per_share=dps,
        dividend_growth_rate=dg * 100 if abs(dg) < 1 else dg,
        cost_of_capital=wacc * 100 if wacc < 1 else wacc,
        current_price=price,
        payout_ratio=None,
    )
    try:
        result = DDM().calculate(stock)
        if result.fair_value and result.fair_value > 0:
            return {
                "method": "DDM（戈登增长）",
                "fair_value": result.fair_value,
                "premium_discount": result.premium_discount,
                "assessment": result.assessment,
            }
    except Exception:
        pass
    return None


def _run_garp(params: dict) -> dict | None:
    eps = params.get("eps")
    price = params.get("current_price")
    growth = params.get("growth_rate")
    if not eps or eps <= 0 or not price or growth is None or growth <= 0:
        return None
    stock = SimpleNamespace(
        eps=eps,
        current_price=price,
        growth_rate=growth * 100 if abs(growth) < 1 else growth,
    )
    try:
        result = GARP().calculate(stock)
        if result.fair_value and result.fair_value > 0:
            return {
                "method": "盖亚普",
                "fair_value": result.fair_value,
                "premium_discount": result.premium_discount,
                "assessment": result.assessment,
            }
    except Exception:
        pass
    return None


def _run_reverse_dcf(params: dict) -> dict | None:
    fcf = params.get("fcf")
    shares = params.get("total_shares")
    price = params.get("current_price")
    net_debt = params.get("net_debt", 0)
    wacc = params.get("wacc", DEFAULT_WACC)
    tg = params.get("terminal_growth", DEFAULT_TERMINAL_GROWTH)
    if not fcf or fcf <= 0 or not shares or shares <= 0 or not price:
        return None
    stock = SimpleNamespace(
        fcf=fcf,
        shares_outstanding=shares,
        current_price=price,
        net_debt=net_debt,
        discount_rate=wacc * 100 if wacc < 1 else wacc,
        terminal_growth=tg * 100 if tg < 1 else tg,
    )
    try:
        result = ReverseDCF().calculate(stock)
        implied_growth = result.details.get("implied_growth_1_5", None)
        note = ""
        if implied_growth is not None:
            note = f"市场隐含增长率 {implied_growth:.1f}%"
        return {
            "method": "反向DCF",
            "fair_value": price,
            "premium_discount": 0.0,
            "assessment": "定价",
            "note": note,
        }
    except Exception:
        pass
    return None


def _run_graham_formula(params: dict) -> dict | None:
    eps = params.get("eps")
    price = params.get("current_price")
    growth = params.get("growth_rate")
    aaa_yield = params.get("aaa_yield", DEFAULT_AAA_YIELD)
    if not eps or eps <= 0 or not price or growth is None:
        return None
    stock = SimpleNamespace(
        eps=eps,
        growth_rate=growth * 100 if abs(growth) < 1 else growth,
        aaa_corporate_yield=aaa_yield,
        current_price=price,
    )
    try:
        result = GrahamFormula().calculate(stock)
        if result.fair_value and result.fair_value > 0:
            return {
                "method": "格雷厄姆公式",
                "fair_value": result.fair_value,
                "premium_discount": result.premium_discount,
                "assessment": result.assessment,
            }
    except Exception:
        pass
    return None


def run_valuation_summary(data: dict) -> list[dict]:
    """运行 5 种估值方法，返回结果列表。每个元素包含 method, fair_value, premium_discount, assessment。"""
    params = _extract_params(data)
    if not params.get("current_price"):
        return []

    runners = [
        _run_graham_number,
        _run_ddm,
        _run_garp,
        _run_reverse_dcf,
        _run_graham_formula,
    ]

    results = []
    for runner in runners:
        try:
            result = runner(params)
            if result:
                results.append(result)
        except Exception:
            continue

    return results

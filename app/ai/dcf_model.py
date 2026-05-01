import pandas as pd


def calculate_dcf(
    free_cash_flows: list[float],
    revenue_growth_rates: list[float],
    current_price: float,
    total_shares: float,
    wacc: float = 0.10,
    terminal_growth: float = 0.025,
) -> dict:
    """
    基于自由现金流折现模型计算内在价值。
    返回乐观/中性/悲观三档估值结果，包含详细计算步骤。
    """
    if not free_cash_flows or total_shares <= 0:
        return {"error": "数据不足，无法计算DCF"}

    latest_fcf = free_cash_flows[-1]
    avg_growth = sum(revenue_growth_rates) / len(revenue_growth_rates) if revenue_growth_rates else 0.05

    scenarios = {
        "乐观": avg_growth * 1.3,
        "中性": avg_growth,
        "悲观": avg_growth * 0.6,
    }

    results = {}
    for label, growth in scenarios.items():
        growth = max(min(growth, 0.30), -0.10)
        projected_fcfs = []
        discount_factors = []
        present_values = []
        fcf = latest_fcf
        for year in range(1, 6):
            fcf = fcf * (1 + growth)
            discount = (1 + wacc) ** year
            pv = fcf / discount
            projected_fcfs.append(round(fcf, 2))
            discount_factors.append(round(discount, 4))
            present_values.append(round(pv, 2))

        terminal_value = (fcf * (1 + terminal_growth)) / (wacc - terminal_growth)
        terminal_pv = terminal_value / ((1 + wacc) ** 5)

        enterprise_value = sum(present_values) + terminal_pv
        per_share = enterprise_value / total_shares

        deviation = (per_share - current_price) / current_price * 100 if current_price > 0 else 0

        results[label] = {
            "内在价值": round(per_share, 2),
            "偏离度": round(deviation, 1),
            "增速假设": round(growth * 100, 1),
            "projected_fcfs": projected_fcfs,
            "discount_factors": discount_factors,
            "present_values": present_values,
            "terminal_value": round(terminal_value, 2),
            "terminal_pv": round(terminal_pv, 2),
            "enterprise_value": round(enterprise_value, 2),
        }

    mid = results["中性"]
    results["判断"] = "被低估" if mid["偏离度"] > 0 else "被高估"
    results["判断幅度"] = abs(mid["偏离度"])
    results["当前股价"] = current_price
    results["WACC"] = f"{wacc*100:.1f}%"
    results["永续增长率"] = f"{terminal_growth*100:.1f}%"
    results["latest_fcf"] = latest_fcf
    results["avg_growth"] = avg_growth
    results["total_shares"] = total_shares
    results["wacc_raw"] = wacc
    results["terminal_growth_raw"] = terminal_growth

    return results

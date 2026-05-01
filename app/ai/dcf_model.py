def calculate_dcf(
    free_cash_flows: list[float],
    revenue_growth_rates: list[float],
    current_price: float,
    total_shares: float,
    net_debt: float = 0.0,
    wacc: float = 0.10,
    terminal_growth: float = 0.025,
) -> dict:
    """
    DCF两阶段折现模型。

    参数:
      free_cash_flows: 历史自由现金流列表（单位：元），按时间正序排列
      revenue_growth_rates: 历史营收增长率列表（小数形式，如0.15表示15%）
      current_price: 当前股价
      total_shares: 总股本（股）
      net_debt: 净负债（有息负债 - 现金及等价物），正值表示净负债，负值表示净现金
      wacc: 加权平均资本成本
      terminal_growth: 永续增长率
    """
    if not free_cash_flows or total_shares <= 0:
        return {"error": "数据不足，无法计算DCF"}

    if wacc <= terminal_growth:
        return {"error": "WACC必须大于永续增长率"}

    positive_fcfs = [f for f in free_cash_flows if f > 0]
    if not positive_fcfs:
        return {"error": "历史自由现金流均为负，DCF模型不适用"}

    if len(free_cash_flows) >= 3:
        recent = free_cash_flows[-3:]
        weights = [0.2, 0.3, 0.5]
        base_fcf = sum(f * w for f, w in zip(recent, weights))
    else:
        base_fcf = free_cash_flows[-1]

    if base_fcf <= 0:
        base_fcf = sum(positive_fcfs) / len(positive_fcfs)

    if revenue_growth_rates:
        valid_rates = [r for r in revenue_growth_rates if -0.5 < r < 1.0]
        if valid_rates:
            if len(valid_rates) >= 3:
                weights_g = list(range(1, len(valid_rates) + 1))
                total_w = sum(weights_g)
                avg_growth = sum(r * w for r, w in zip(valid_rates, weights_g)) / total_w
            else:
                avg_growth = sum(valid_rates) / len(valid_rates)
        else:
            avg_growth = 0.05
    else:
        avg_growth = 0.05

    projection_years = 5
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
        fcf = base_fcf
        for year in range(1, projection_years + 1):
            fcf = fcf * (1 + growth)
            discount = (1 + wacc) ** year
            pv = fcf / discount
            projected_fcfs.append(round(fcf, 2))
            discount_factors.append(round(discount, 4))
            present_values.append(round(pv, 2))

        terminal_value = (fcf * (1 + terminal_growth)) / (wacc - terminal_growth)
        terminal_pv = terminal_value / ((1 + wacc) ** projection_years)

        enterprise_value = sum(present_values) + terminal_pv
        equity_value = enterprise_value - net_debt
        per_share = equity_value / total_shares

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
            "equity_value": round(equity_value, 2),
        }

    mid = results["中性"]
    results["判断"] = "被低估" if mid["偏离度"] > 0 else "被高估"
    results["判断幅度"] = abs(mid["偏离度"])
    results["当前股价"] = current_price
    results["WACC"] = f"{wacc*100:.1f}%"
    results["永续增长率"] = f"{terminal_growth*100:.1f}%"
    results["base_fcf"] = base_fcf
    results["avg_growth"] = avg_growth
    results["total_shares"] = total_shares
    results["net_debt"] = net_debt
    results["wacc_raw"] = wacc
    results["terminal_growth_raw"] = terminal_growth

    return results

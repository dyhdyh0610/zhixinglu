def calculate_dcf(
    free_cash_flows: list[float],
    revenue_growth_rates: list[float],
    current_price: float,
    total_shares: float,
    net_debt: float = 0.0,
    wacc: float = 0.10,
    terminal_growth: float = 0.025,
    growth_rate_1_5: float | None = None,
    growth_rate_6_10: float | None = None,
) -> dict:
    """
    DCF两阶段折现模型（10年预测期）。

    参数:
      free_cash_flows: 历史自由现金流列表（单位：元），按时间正序排列
      revenue_growth_rates: 历史营收增长率列表（小数形式，如0.15表示15%）
      current_price: 当前股价
      total_shares: 总股本（股）
      net_debt: 净负债（有息负债 - 现金及等价物）
      wacc: 加权平均资本成本
      terminal_growth: 永续增长率
      growth_rate_1_5: 第1-5年增长率（小数），None则从历史数据推导
      growth_rate_6_10: 第6-10年增长率（小数），None则取第一阶段的一半
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

    g1 = growth_rate_1_5 if growth_rate_1_5 is not None else avg_growth
    g2 = growth_rate_6_10 if growth_rate_6_10 is not None else max(avg_growth * 0.5, terminal_growth)

    scenarios = {
        "乐观": (g1 * 1.3, g2 * 1.3),
        "中性": (g1, g2),
        "悲观": (g1 * 0.6, g2 * 0.6),
    }

    results = {}
    for label, (sg1, sg2) in scenarios.items():
        sg1 = max(min(sg1, 0.30), -0.10)
        sg2 = max(min(sg2, 0.20), -0.05)

        projected_fcfs = []
        discount_factors = []
        present_values = []
        fcf = base_fcf
        total_pv = 0

        for year in range(1, 11):
            if year <= 5:
                fcf = fcf * (1 + sg1)
            else:
                fcf = fcf * (1 + sg2)
            df = (1 + wacc) ** year
            pv = fcf / df
            total_pv += pv
            projected_fcfs.append(round(fcf, 2))
            discount_factors.append(round(df, 4))
            present_values.append(round(pv, 2))

        fcf_year_10 = fcf
        terminal_value = (fcf_year_10 * (1 + terminal_growth)) / (wacc - terminal_growth)
        terminal_pv = terminal_value / ((1 + wacc) ** 10)

        enterprise_value = total_pv + terminal_pv
        equity_value = enterprise_value - net_debt
        per_share = equity_value / total_shares

        deviation = (per_share - current_price) / current_price * 100 if current_price > 0 else 0

        tv_pct = (terminal_pv / enterprise_value) * 100 if enterprise_value > 0 else 0

        results[label] = {
            "内在价值": round(per_share, 2),
            "偏离度": round(deviation, 1),
            "增速假设_1_5": round(sg1 * 100, 1),
            "增速假设_6_10": round(sg2 * 100, 1),
            "增速假设": round(sg1 * 100, 1),
            "projected_fcfs": projected_fcfs,
            "discount_factors": discount_factors,
            "present_values": present_values,
            "terminal_value": round(terminal_value, 2),
            "terminal_pv": round(terminal_pv, 2),
            "enterprise_value": round(enterprise_value, 2),
            "equity_value": round(equity_value, 2),
            "terminal_value_pct": round(tv_pct, 1),
        }

    sensitivity_low = _run_sensitivity(
        base_fcf, total_shares, net_debt,
        g1 - 0.02, g2 - 0.01, terminal_growth - 0.005, wacc + 0.02,
    )
    sensitivity_high = _run_sensitivity(
        base_fcf, total_shares, net_debt,
        g1 + 0.02, g2 + 0.01, terminal_growth + 0.005, wacc - 0.02,
    )

    mid = results["中性"]
    results["判断"] = "被低估" if mid["偏离度"] > 0 else "被高估"
    results["判断幅度"] = abs(mid["偏离度"])
    results["当前股价"] = current_price
    results["WACC"] = f"{wacc*100:.1f}%"
    results["永续增长率"] = f"{terminal_growth*100:.1f}%"
    results["base_fcf"] = base_fcf
    results["avg_growth"] = avg_growth
    results["growth_1_5"] = g1
    results["growth_6_10"] = g2
    results["total_shares"] = total_shares
    results["net_debt"] = net_debt
    results["wacc_raw"] = wacc
    results["terminal_growth_raw"] = terminal_growth
    results["sensitivity_low"] = round(sensitivity_low, 2)
    results["sensitivity_high"] = round(sensitivity_high, 2)

    return results


def _run_sensitivity(
    base_fcf: float, shares: float, net_debt: float,
    g1: float, g2: float, g_term: float, r: float,
) -> float:
    if r <= g_term or base_fcf <= 0:
        return 0.0

    fcf = base_fcf
    total_pv = 0.0
    for year in range(1, 11):
        if year <= 5:
            fcf *= (1 + g1)
        else:
            fcf *= (1 + g2)
        total_pv += fcf / ((1 + r) ** year)

    terminal_value = (fcf * (1 + g_term)) / (r - g_term)
    terminal_pv = terminal_value / ((1 + r) ** 10)

    equity_value = total_pv + terminal_pv - net_debt
    return equity_value / shares if shares > 0 else 0.0

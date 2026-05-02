# 估值汇总模块实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在"估值坐标"模块（Module 4）最前面增加一个估值汇总表格，使用 valueinvest 库的 5 种经典估值方法自动计算公允价值。

**Architecture:** 新建 `app/ai/valuation_models.py` 封装估值计算逻辑，从已有 akshare 数据中提取参数，调用 valueinvest 库的 5 个估值类，返回结构化结果。在 `generator.py` 的 `_generate_module4` 开头渲染 HTML 表格。

**Tech Stack:** valueinvest (Python 估值库), akshare (已有), SimpleNamespace (构造 stock 对象)

---

## File Structure

| File | Action | Responsibility |
|------|--------|---------------|
| `requirements.txt` | Modify | 添加 valueinvest 依赖 |
| `app/ai/valuation_models.py` | Create | 封装 5 种估值计算，提取参数，返回结果列表 |
| `app/report/generator.py` | Modify | 在 `_generate_module4` 开头调用估值汇总并渲染表格 |

---

### Task 1: 添加 valueinvest 依赖

**Files:**
- Modify: `requirements.txt`

- [ ] **Step 1: 添加 valueinvest 到 requirements.txt**

在 `requirements.txt` 末尾添加：

```
valueinvest>=1.3.0
```

- [ ] **Step 2: 安装依赖**

Run: `cd /Users/xuxixi/Desktop/zhixinglu && pip install valueinvest>=1.3.0`
Expected: 安装成功，无报错

- [ ] **Step 3: 验证导入**

Run: `python3 -c "from valueinvest.valuation.graham import GrahamNumber, GrahamFormula; from valueinvest.valuation.ddm import DDM; from valueinvest.valuation.growth import GARP; from valueinvest.valuation.dcf import ReverseDCF; print('OK')"`
Expected: 输出 `OK`

- [ ] **Step 4: Commit**

```bash
git add requirements.txt
git commit -m "deps: add valueinvest for valuation summary module"
```

---

### Task 2: 创建估值计算模块 `app/ai/valuation_models.py`

**Files:**
- Create: `app/ai/valuation_models.py`

- [ ] **Step 1: 创建 valuation_models.py**

```python
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
```

- [ ] **Step 2: 验证模块可导入**

Run: `cd /Users/xuxixi/Desktop/zhixinglu && python3 -c "from app.ai.valuation_models import run_valuation_summary; print('OK')"`
Expected: 输出 `OK`

- [ ] **Step 3: Commit**

```bash
git add app/ai/valuation_models.py
git commit -m "feat: add valuation summary module with 5 classic methods"
```

---

### Task 3: 在 generator.py 中集成估值汇总表格

**Files:**
- Modify: `app/report/generator.py:1-10` (imports)
- Modify: `app/report/generator.py:479-526` (`_generate_module4` function)

- [ ] **Step 1: 添加 import**

在 `generator.py` 顶部的 import 区域，在 `from app.ai.dcf_model import calculate_dcf` 之后添加：

```python
from app.ai.valuation_models import run_valuation_summary
```

- [ ] **Step 2: 添加估值表格渲染函数**

在 `_generate_module4` 函数之前（`_build_dcf_section` 函数之后，约第 478 行），添加：

```python
def _build_valuation_summary_table(data: dict) -> str:
    results = run_valuation_summary(data)
    if not results:
        return ""

    rows = ""
    note = ""
    for r in results:
        fair_val = f"¥{r['fair_value']:.2f}"
        pd_val = r["premium_discount"]
        pd_str = f"{pd_val:+.1f}%"

        assessment = r["assessment"]
        if pd_val < -10:
            css_class = "down"
            if "Overvalued" in assessment or "overvalued" in assessment:
                assessment = "估值过高"
        elif pd_val > 10:
            css_class = "up"
            if "Undervalued" in assessment or "undervalued" in assessment:
                assessment = "被低估"
        else:
            css_class = ""
            if assessment == "定价":
                pass
            elif "Fair" in assessment or "fair" in assessment:
                assessment = "定价合理"

        if r.get("note"):
            note = r["note"]

        rows += f'<tr><td><strong>{r["method"]}</strong></td><td>{fair_val}</td><td>{pd_str}</td><td class="{css_class}">{assessment}</td></tr>\n'

    table = f'''<div class="indicator-card">
  <h3 style="font-family:var(--font-serif);margin-bottom:12px;">估值汇总</h3>
  <table class="fin-table">
    <thead><tr><th>方法</th><th>公允价值</th><th>溢价/折价</th><th>评估</th></tr></thead>
    <tbody>{rows}</tbody>
  </table>
  {f'<p class="data-label" style="margin-top:8px;">{note}</p>' if note else ''}
  <div class="disclaimer" style="margin-top:12px;">以上估值基于经典模型和公开财务数据自动计算，仅供参考。不同方法适用于不同类型的公司。</div>
</div>'''
    return table
```

- [ ] **Step 3: 修改 `_generate_module4` 在开头插入估值汇总表格**

将 `_generate_module4` 函数修改为在 `content_parts = []` 之后、PE/PB 循环之前插入估值汇总表格：

```python
async def _generate_module4(stock_name: str, data: dict) -> str:
    val_data = data.get("valuation") or {}
    content_parts = []

    valuation_table = _build_valuation_summary_table(data)
    if valuation_table:
        content_parts.append(valuation_table)

    for key, display in [("pe", "PE(TTM)"), ("pb", "PB")]:
        # ... 原有代码不变 ...
```

只需在 `content_parts = []` 和 `for key, display in ...` 之间插入 3 行代码。

- [ ] **Step 4: 验证服务启动**

Run: `cd /Users/xuxixi/Desktop/zhixinglu && timeout 10 python3 -c "from app.report.generator import generate_report; print('OK')" || true`
Expected: 输出 `OK`（验证导入链完整）

- [ ] **Step 5: Commit**

```bash
git add app/report/generator.py
git commit -m "feat: integrate valuation summary table into Module 4"
```

---

### Task 4: 端到端验证

- [ ] **Step 1: 启动开发服务器**

Run: `cd /Users/xuxixi/Desktop/zhixinglu && python3 run.py &`

- [ ] **Step 2: 在浏览器中测试**

打开 http://0.0.0.0:5001，搜索一只股票（如 "贵州茅台" 或 "000858"），等待报告生成完成。

验证：
1. Module 4（估值坐标）最前面出现估值汇总表格
2. 表格包含 4 列：方法、公允价值、溢价/折价、评估
3. 至少有格雷厄姆数、盖亚普、格雷厄姆公式 3 行（这些只需 EPS 和 BVPS，大多数股票都有）
4. 如果该股票有分红，DDM 行也应出现
5. 如果有现金流数据，反向 DCF 行也应出现
6. 评估列颜色正确：被低估绿色、估值过高红色
7. 表格下方有免责声明
8. 原有的 PE/PB 分位数内容仍然正常显示在表格下方

- [ ] **Step 3: 测试不分红股票**

搜索一只不分红的股票，验证 DDM 行被跳过，其他方法正常显示。

- [ ] **Step 4: 最终 Commit**

如果有任何修复，提交：

```bash
git add -A
git commit -m "fix: adjust valuation summary for edge cases"
```

# 估值汇总模块设计

## 概述

在"估值坐标"（Module 4）部分最前面增加一个估值汇总表格，使用 valueinvest 开源库的 5 种经典估值方法计算公允价值，展示方法名、公允价值、溢价/折价、评估结论。

## 估值方法

| 方法 | valueinvest 类 | 核心公式 |
|------|---------------|----------|
| 格雷厄姆数 | `GrahamNumber` | `sqrt(22.5 * EPS * BVPS)` |
| DDM（戈登增长） | `DDM` | `D1 / (r - g)` |
| 盖亚普 (GARP) | `GARP` | `EPS * (1+g)^n * target_pe / (1+r)^n` |
| 反向 DCF | `ReverseDCF` | 二分搜索隐含增长率 |
| 格雷厄姆公式 | `GrahamFormula` | `EPS * (8.5 + 2g) * 4.4 / Y` |

## 参数来源

所有参数从已有 akshare 数据自动推算，用户无需输入：

| 参数 | 来源 | 推算方式 |
|------|------|----------|
| EPS | `get_financial_summary` | 最近年报每股收益，或 净利润/总股本 |
| BVPS | `get_stock_info` → `每股净资产` | 直接取 |
| 当前股价 | `get_stock_info` → `最新价` | 直接取 |
| 增长率 | `get_financial_summary` → `净利润同比增长率` | 最近 3 年加权平均 |
| 每股分红 | `get_dividend_yield` + 股价 | 股息率 × 股价 |
| FCF | `get_cash_flow_sheet` | 经营现金流 - 资本支出 |
| 净负债 | 现有 DCF 模块逻辑 | 复用 |
| 总股本 | `get_stock_info` | 总市值 / 最新价 |
| WACC | 默认 10% | 与现有 DCF 一致 |
| AAA 债券收益率 | 默认 4.0% | 中国当前水平 |

## 架构

### 新增文件

- `app/ai/valuation_models.py` — 估值计算封装层

### 修改文件

- `app/report/generator.py` — 在 `_generate_module4` 开头插入估值汇总表格
- `requirements.txt` — 添加 `valueinvest` 依赖

### 数据流

```
已有 akshare 数据 (info, financial_summary, cashflow, dividend_yield)
    ↓
valuation_models.py: run_valuation_summary(data)
    ↓
调用 valueinvest 的 5 个估值类
    ↓
返回 list[dict]: {method, fair_value, premium_discount, assessment}
    ↓
generator.py: _generate_module4 开头渲染 HTML 表格
    ↓
接续现有 PE/PB 分位数内容
```

### 估值结果格式

每个方法返回：
- `method`: 方法名（中文）
- `fair_value`: 公允价值（元），格式 `¥XX.XX`
- `premium_discount`: 溢价/折价百分比，如 `-31.3%`、`+74.4%`
- `assessment`: 评估结论 — "估值过高"（溢价 < -10%）/ "被低估"（溢价 > +10%）/ "定价合理"（±10% 内）

反向 DCF 特殊处理：显示当前股价为公允价值，溢价 +0.0%，评估显示"定价"并在表格下方注明隐含增长率。

### 容错

某个方法因数据不足无法计算时（如不分红公司无法用 DDM），跳过该行，不影响其他方法。

## 表格样式

复用现有 `.fin-table` 样式，四列：方法、公允价值、溢价/折价、评估。

评估列颜色：
- 被低估 → 绿色 (`.up` 类)
- 估值过高 → 红色 (`.down` 类)
- 定价合理/定价 → 默认色

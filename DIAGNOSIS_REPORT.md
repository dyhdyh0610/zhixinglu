# 知行录 (zhixinglu) 全面代码诊断报告

> 诊断日期: 2026-05-13
> 项目路径: /Users/daniel/zhixinglu/
> 技术栈: FastAPI + uvicorn, Python 3.11+, akshare, OpenAI SDK

---

## 摘要

共发现 **28** 个问题，按严重程度分类：
- **Critical (严重)**: 5 个 — 可能导致服务崩溃或完全不可用
- **High (高危)**: 7 个 — 可能导致功能异常或数据错误
- **Medium (中等)**: 10 个 — 代码质量问题或潜在风险
- **Low (低危)**: 6 个 — 优化建议

---

## CRITICAL — 5 个

### C1. 代理环境变量未处理，akshare 请求可能被代理阻断

**文件**: `run.py` + `app/data/*.py`（所有 akshare 调用）

**问题**: 系统中存在代理环境变量（HTTP_PROXY/HTTPS_PROXY）时，akshare 的 HTTP 请求会被代理转发，导致连接超时或失败。虽然启动脚本中有 `unset` 操作，但：
- `run.py` 本身没有任何代理清理逻辑
- 如果通过其他方式启动（非 `run_noproxy.py`），代理仍然存在
- 子进程继承环境变量，`akshare` 内部使用 requests 会受代理影响

**影响**: 所有 akshare 数据获取（行情、财务、新闻、搜索等）全部失败，整个应用瘫痪。

**建议**: 在 `app/main.py` 的 lifespan 或 `run.py` 入口处强制清理代理环境变量：
```python
for var in ["HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY", "http_proxy", "https_proxy", "all_proxy"]:
    os.environ.pop(var, None)
os.environ["no_proxy"] = "*"
```

### C2. `llm_client.py` 缺少异常处理和超时设置

**文件**: `app/ai/llm_client.py` 第 14-47 行

**问题**:
1. `chat()` 函数没有任何 try/except，当 LLM API 超时、返回错误、网络异常时直接抛出异常
2. 没有设置 timeout 参数，默认可能等待数分钟
3. `chat_with_search()` 虽然捕获异常后 fallback 到 `chat()`，但 `chat()` 同样可能失败
4. 全局单例 `_client` 不可重新创建，一旦初始化后无法更换配置

**影响**: 任何一个 LLM 调用失败都会导致整个报告生成流程中断（上游 generator.py 虽然有 try/except，但如果 chat 抛出未处理异常，流式输出会断裂）。

**建议**: 
- 添加 timeout 参数（如 `timeout=120`）
- 在 `chat()` 中添加 try/except 返回空字符串或 None
- 考虑添加重试机制

### C3. `_get_industry_data` 列名硬编码依赖 akshare 返回格式

**文件**: `app/data/diagnosis_data.py` 第 74-103 行

**问题**:
```python
for _, row in stock_info.iterrows():
    if row.iloc[0] == "行业":  # 依赖第0列是名称
        industry = row.iloc[1]  # 依赖第1列是值
        break
```
使用 `iloc[0]` 和 `iloc[1]` 按位置访问，而非按列名访问。akshare 的 `stock_individual_info_em` 返回的 DataFrame 列名可能变化（历史上已多次变更），一旦列顺序变化就会匹配到错误数据。

**影响**: 行业板块分析模块获取到错误行业名称或 None，导致行业 K 线查询失败。

**建议**: 使用列名访问：`row.get("item") == "行业"` 和 `row.get("value")`。

### C4. `_get_individual_info` 同样存在列名位置依赖

**文件**: `app/data/portfolio_data.py` 第 162-183 行

**问题**:
```python
for _, row in df.iterrows():
    info[row["item"]] = row["value"]
```
虽然使用了列名 `row["item"]` 和 `row["value"]`，但如果 akshare 变更列名（如改为 `item_name`、`value_str` 等），此处会直接抛出 KeyError。

**影响**: 单股信息获取失败，导致 `get_stock_profiles` 和 `get_batch_quotes` 降级到腾讯财经。

**建议**: 添加 try/except KeyError 或动态检测列名。

### C5. `stock_search.py` 初始化时一次性加载全部 A 股列表

**文件**: `app/data/stock_search.py` 第 12-16 行

**问题**:
```python
def _get_stock_list() -> pd.DataFrame:
    global _stock_list_cache
    if _stock_list_cache is None:
        _stock_list_cache = ak.stock_info_a_code_name()
    return _stock_list_cache
```
首次调用时阻塞下载全部 A 股列表（约 5000+ 只股票），如果 akshare API 超时或网络慢，首个搜索请求会长时间阻塞。缓存无 TTL 永久有效，新上市股票永远搜不到。

**影响**: 
1. 首次搜索可能超时（实测在代理环境下已超时 60s）
2. 永远无法搜索到缓存后新上市的股票

**建议**: 添加 TTL（如每天刷新一次），或改为异步预加载。

---

## HIGH — 7 个

### H1. `_parse_json` 无 fallback 容错

**文件**: `app/report/letter_generator.py` 第 102-112 行

**问题**:
```python
def _parse_json(text: str):
    text = text.strip()
    if text.startswith("```"):
        # ... strip code fences
        text = "\n".join(lines)
    return json.loads(text)  # 没有 try/except！
```
`json.loads` 没有 try/except 包裹。如果 LLM 返回格式不正确的 JSON（经常发生），直接抛出 JSONDecodeError。

**影响**: 虽然调用方（如 letter_generator 第 184 行）有外层 try/except，但 `letter_generator.py` 第 208 行的 `_parse_json(raw)` 如果失败，会导致 news 部分降级为空数组，而不是使用 fallback。更严重的是 `diagnosis_generator.py` 第 234 行对 `_parse_json` 的调用，如果 raw 内容包含 markdown 文本（如 LLM 拒绝输出 JSON），JSON 解析失败后，value_analysis 虽然仍等于 raw，但 JSON 结构数据不可用。

**建议**: 在 `_parse_json` 内部添加 try/except，解析失败返回 None，由调用方决定 fallback。

### H2. `module_html` 编号与加载进度条不一致

**文件**: `app/report/html_template.py` 第 551-555 行 vs 第 596-609 行

**问题**: 前端加载进度条的 `labels` 对象映射的是 1-11：
```javascript
var labels = {1:'了解公司业务', 2:'分析商业模式', 3:'财务体检', ..., 11:'生成延展问题'};
```
但实际模块编号是 0-11（共 12 个模块），其中模块 0 是"操作建议"。进度条从模块 1 开始计数，但生成器从模块 0 开始 yield。这导致：
- 模块 0（操作建议）生成时，loaded=1，显示"了解公司业务"（错误标签）
- 模块 1 生成时，loaded=2，显示"分析商业模式"（正确但偏移）
- 最终模块 11 生成时，loaded=12，但 labels 没有 key 12，显示 undefined

**影响**: 加载进度条的进度文字与实际模块不匹配，用户体验差。

**建议**: 将 labels 改为从 0 开始，或调整 loaded 计数。

### H3. DCF gauge chart 内联 JS 与 chart_config.py 中的 gauge_chart 逻辑重复且不一致

**文件**: `app/report/generator.py` 第 452-543 行 vs `app/report/chart_config.py` 第 84-105 行

**问题**: 
1. DCF 估值的 gauge chart 是内联生成的（~90 行 JS），而通用 `gauge_chart()` 在 chart_config.py 中也有定义，两者功能重叠但实现不同
2. DCF gauge 的 min/max 使用 `pes.ps` 和 `opt.ps`（悲观/乐观估值），但如果 DCF 计算失败或数据不足，这两个值可能为 0 或负数，导致 ECharts 的 gauge min >= max 而崩溃
3. `_build_dcf_section` 中 JS 代码使用 Python f-string 格式化数值，如果 `dcf["wacc_raw"]` 等值为 None，f-string 会抛出 TypeError

**影响**: DCF 估值模块在数据不全时可能导致 JavaScript 运行时错误，图表不渲染。

**建议**: 在生成 gauge 配置前验证 min < max，对 None 值使用默认值。

### H4. `api_report` 路由中 `results[0]` 可能 IndexError

**文件**: `app/main.py` 第 62-65 行

**问题**:
```python
results = await asyncio.to_thread(search_stock, symbol)
stock_code = results[0]["code"] if results else symbol  # 三元运算符
```
虽然使用了 `if results else` 保护，但当 `results` 为空列表时，代码会 fallback 使用原始 symbol 作为 code 和 name。这意味着如果用户输入一个不存在的股票代码（如 "999999"），报告生成会使用 "999999" 作为代码和名称继续执行。后续的 `generate_report` 中 `_fetch_all_data` 会因为找不到股票数据而产生大量空数据。

**影响**: 生成一份全是"暂无数据"的报告，浪费 LLM 调用费用。

**建议**: 当 `results` 为空时直接返回 404 错误。

### H5. `api_mixed_strategy` 路由不保存历史记录

**文件**: `app/main.py` 第 398-410 行

**问题**: 与 `api_report`（第 60-78 行）不同，`api_mixed_strategy` 流式生成后没有保存结果到数据库。用户生成的混合策略报告无法回溯查看。

**影响**: 用户体验不一致，混合策略报告生成后无法通过历史记录查看。

**建议**: 添加与 `api_report` 类似的 save_report 逻辑。

### H6. diagnosis_generator 中 `_get_or_generate_report` 可能触发无限 LLM 调用

**文件**: `app/report/diagnosis_generator.py` 第 37-52 行

**问题**: 当没有缓存报告时，`_get_or_generate_report` 会调用 `generate_report()`（完整 12 模块报告生成），这需要调用约 15 次 LLM API。然后在诊断流程中再调用 6 次 LLM API（5 维度 + 结论）。一次诊断总共可能触发 20+ 次 LLM 调用。

**影响**: 诊断生成极其缓慢（可能 5-10 分钟），且 LLM 费用高昂。如果 LLM API 有 rate limit，可能触发限流。

**建议**: 限制 `_get_or_generate_report` 仅在必要时触发，或只提取关键模块数据而非完整报告。

### H7. `get_profit_forecast` 中 akshare API 调用可能返回空 DataFrame 导致后续 KeyError

**文件**: `app/data/news_data.py` 第 48-63 行

**问题**:
```python
result["eps"] = ak.stock_profit_forecast_ths(symbol=symbol, indicator="预测年报每股收益")
```
如果 akshare 返回的 DataFrame 列名不包含 "年度"、"预测机构数"、"最小值"、"均值"、"最大值"，后续 `_build_forecast_section`（generator.py 第 726 行）直接按列名访问会 KeyError。

**影响**: 盈利预测模块崩溃。

**建议**: 在访问列名前检查列是否存在，或使用 `.get()` 方法。

---

## MEDIUM — 10 个

### M1. `_retry` 函数不记录日志

**文件**: `app/data/portfolio_data.py` 第 26-33 行

**问题**: 重试逻辑不打印任何日志，无法知道何时发生了重试以及重试了多少次。

### M2. 全局缓存无大小限制，可能导致内存泄漏

**文件**: `app/data/portfolio_data.py` 第 7-20 行

**问题**: `_tencent_cache`、`_individual_cache`、`_profile_cache` 都是全局 dict，只通过 TTL 判断是否过期但从不清理过期条目。长时间运行后会累积大量过期缓存。

### M3. `_get_tencent_prefix` 无法处理非 6 开头的深圳股票

**文件**: `app/data/portfolio_data.py` 第 66-67 行

**问题**: `return "sh" if symbol.startswith("6") else "sz" + symbol` — 这只覆盖了 6 开头的上海股票和大部分深圳股票。但深圳创业板（30 开头）、北交所（8/4 开头）等也都被归类为 "sz"，腾讯 API 可能不返回这些数据。

### M4. `letter_generator.py` 中 `fetch_letter_data` 可能引发 KeyError

**文件**: `app/data/letter_data.py` 第 87 行

**问题**: `a_codes = [h["code"] for h in a_holdings]` — 如果 holdings 中的条目缺少 "code" 键，直接 KeyError。虽然前端会确保传入 code，但如果通过 API 直接调用缺少 code 的 holdings，会崩溃。

### M5. `_build_valuation_summary_table` 中 `run_valuation_summary` 异常未处理

**文件**: `app/report/generator.py` 第 547-548 行

**问题**: `results = run_valuation_summary(data)` 没有 try/except，如果 valuation 库抛出异常（如数据不足），整个模块 4 会崩溃。

### M6. `generate_report` 中模块 0-11 全部串行执行，没有并行优化

**文件**: `app/report/generator.py` 第 54-68 行

**问题**: 12 个模块完全串行生成，每个模块都要等 LLM 返回后才能继续。实际上模块 1-5 之间没有数据依赖，可以并行调用 LLM。

**影响**: 报告生成时间长（可能 3-8 分钟）。

### M7. `_generate_module11_questions` 中 LLM 输出解析过于宽松

**文件**: `app/report/generator.py` 第 1050-1061 行

**问题**: 如果 LLM 返回的内容不包含编号列表，会把整段文本作为单个问题：`questions = [f"<li>{text}</li>"]`。如果 LLM 返回的是 markdown 格式（包含 # 标题、**加粗等），HTML 中会出现未渲染的 markdown 标记。

### M8. ECharts CDN 使用 jsdelivr 可能不稳定

**文件**: `app/report/html_template.py` 第 9-10 行

**问题**: `cdn.jsdelivr.net` 在中国大陆的访问不稳定，可能导致 ECharts 和 marked.js 加载失败，图表和 markdown 渲染全部失效。

**建议**: 添加本地 fallback 或使用多个 CDN 来源。

### M9. `api_diagnosis_chat` 中 history 限制为 10 条但没有 token 计数

**文件**: `app/main.py` 第 345 行

**问题**: `for h in history[-10:]` — 如果历史消息很长，10 条消息仍可能超过 LLM 的上下文窗口限制。

### M10. `_mixed_strategy_form_html` 中 stock_name 未做 HTML 转义

**文件**: `app/report/generator.py` 第 968 行

**问题**: `var MIXED_STRATEGY_STOCK = "{stock_name}";` — 如果 stock_name 包含引号或其他特殊字符，可能导致 XSS 或 JS 语法错误。

**建议**: 使用 `json.dumps(stock_name)` 来正确转义。

---

## LOW — 6 个

### L1. `run.py` 使用 reload=True 不适合生产环境

**文件**: `run.py` 第 4 行

**问题**: `reload=True` 仅用于开发，生产环境应使用 `reload=False` 或通过 gunicorn 启动。

### L2. 没有配置 logging 级别和格式

**文件**: `app/main.py`

**问题**: 全局 logging 没有配置，uvicorn 默认日志格式不够详细，问题排查困难。

### L3. `_format_dict` 过滤了 falsy 值

**文件**: `app/ai/prompts.py` 第 11-12 行

**问题**: `if v` 会过滤掉 0、空字符串等。如果某个指标值为 0（如 PE 为 0），在 prompt 中不会显示，但 0 本身可能是有意义的信号。

### L4. 前端 `charts.js` 中 PE 分类逻辑与标签不符

**文件**: `app/static/js/charts.js` 第 129-138 行

**问题**: 标签写的是"PE分位<30%"，但实际代码用的是 `s.peTtm < 20`（PE 绝对值），而非历史分位。这是标签和逻辑不一致。

### L5. `store.js` 中 localStorage 无容量管理

**问题**: 当持仓较多时，localStorage 可能接近 5MB 限制，但没有清理机制。

### L6. `api_history` 返回全部历史记录无分页

**文件**: `app/main.py` 第 160-163 行

**问题**: 随着历史记录增多，一次性返回全部数据会越来越慢。

---

## 已知坑位检查结果

| 坑位 | 状态 | 详情 |
|------|------|------|
| akshare 列名变更 | ⚠️ 部分处理 | `_get_individual_info` 用了列名访问但无 fallback；`_get_industry_data` 用了位置访问（C3、C4） |
| 代理环境变量 | ❌ 未处理 | 启动脚本有 unset 但代码层无保护（C1） |
| module_html 编号 | ⚠️ 偏移问题 | 前端 labels 从 1 开始但模块从 0 开始（H2） |
| gauge chart 重叠 | ⚠️ 潜在问题 | DCF gauge min/max 可能相等或反转（H3） |

---

## 服务测试结果

- `GET /` — ✅ 200 OK
- `GET /api/search?q=600519` — ❌ 超时（60s），可能是 akshare 网络问题或代理问题
- 服务进程运行正常，但数据获取层不稳定

---

## 架构改进建议

1. **添加请求级超时**: 所有 akshare 和 LLM 调用都应设置明确的 timeout
2. **添加 circuit breaker**: 对 akshare API 和 LLM API 添加熔断器，避免级联失败
3. **异步预加载**: 股票列表、板块数据等应在 app 启动时异步预加载
4. **添加健康检查端点**: `/api/health` 检查 akshare 和 LLM 连接状态
5. **统一错误处理**: 创建自定义异常类，所有数据获取函数返回统一的 `(data, error)` 结构
6. **添加测试框架**: 当前无任何测试，建议至少添加单元测试覆盖数据解析逻辑
7. **考虑 API 网关限流**: 防止频繁调用消耗 LLM 额度

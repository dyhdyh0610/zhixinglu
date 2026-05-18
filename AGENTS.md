# 知行录 (zhixinglu) — Agent 上下文

> A 股 / 港股单股深度分析 + 持仓来信 + 交易诊断 Web 应用

## 项目信息

- **仓库**: `dyhdyh0610/zhixinglu`
- **当前位置**: `feat/local-wip` 分支
- **当前版本**: v1.2.0
- **启动**: `cd /Users/daniel/zhixinglu && python3 run.py`
- **端口**: `5001`
- **前端**: `http://localhost:5001`

## 技术栈

- **后端**: FastAPI + uvicorn (Python 3.11+)
- **数据源**: akshare (A 股), yfinance (港股)
- **AI**: 外部 LLM API (OpenAI 兼容接口) + VLM (视觉模型)
- **数据库**: SQLite (history.db, 自动初始化)
- **前端**: 原生 HTML/CSS/JS，单页应用
- **报告输出**: 流式 HTML 渲染

## 启动注意事项

**启动前必须 unset 代理变量**，否则 akshare 数据请求全部失败：
```bash
unset HTTP_PROXY HTTPS_PROXY ALL_PROXY http_proxy https_proxy all_proxy
python3 run.py
```

应用已在 `lifespan` 中自动清除代理变量，但启动脚本本身不受影响。

## 环境变量 (.env)

| 变量 | 说明 |
|------|------|
| `LLM_BASE_URL` | LLM API 地址，默认 `https://api.openai.com/v1` |
| `LLM_API_KEY` | LLM API Key |
| `LLM_MODEL` | LLM 模型名，默认 `claude-4.6-sonnet` |
| `VLM_BASE_URL` | VLM API 地址，默认同 LLM |
| `VLM_API_KEY` | VLM API Key，默认同 LLM |
| `VLM_MODEL` | VLM 模型名，默认 `gemini-3.1-pro` |

## 项目结构

```
zhixinglu/
├── run.py                      # 启动入口 (uvicorn)
├── qq_bot.py                   # QQ 机器人集成 (可选)
├── test_ws.py                  # WebSocket 测试
├── app/
│   ├── main.py                 # FastAPI 主应用，所有 API 路由
│   ├── config.py               # 环境变量配置
│   ├── ai/
│   │   ├── prompts.py          # 分析报告模块 prompts (模块 1-8 + 0 + trade_ref)
│   │   ├── diagnosis_prompts.py # 交易诊断 prompts
│   │   ├── letter_prompts.py   # 持仓来信 prompts
│   │   ├── llm_client.py       # LLM API 调用客户端
│   │   ├── vision_client.py    # VLM 截图解析客户端
│   │   ├── dcf_model.py        # DCF 估值模型
│   │   └── valuation_models.py # 估值模型工具
│   ├── data/
│   │   ├── stock_search.py     # 股票搜索 (A 股 + 港股)
│   │   ├── portfolio_data.py   # 批量行情 + 公司简介
│   │   ├── financial_data.py   # 财务数据 (利润表、指标、分红)
│   │   ├── industry_data.py    # 行业板块数据
│   │   ├── market_data.py      # K 线数据
│   │   ├── news_data.py        # 新闻 + 研报 + 盈利预测
│   │   ├── valuation_data.py   # 估值历史 (PE/PB/PS/PEG 分位)
│   │   ├── diagnosis_data.py   # 诊断模块数据聚合
│   │   ├── letter_data.py      # 来信模块数据 (大盘概览 + 个股)
│   │   └── portfolio_data.py   # 持仓批量行情
│   ├── report/
│   │   ├── generator.py        # 单股报告生成器 (模块编排 + 流式输出)
│   │   ├── html_template.py    # 报告 HTML 模板
│   │   ├── chart_config.py     # 图表配置
│   │   ├── diagnosis_generator.py  # 交易诊断报告生成
│   │   ├── diagnosis_template.py   # 诊断 HTML 模板
│   │   ├── letter_generator.py     # 持仓来信生成
│   │   └── letter_template.py      # 来信 HTML 模板
│   ├── models/
│   │   ├── history.py          # 报告历史 (SQLite CRUD)
│   │   ├── letter.py           # 来信记录 (SQLite CRUD)
│   │   └── diagnosis.py        # 诊断记录 (SQLite CRUD，含对话历史)
│   └── static/
│       ├── index.html          # 前端主页面
│       ├── css/common.css      # 样式
│       └── js/                 # 前端逻辑 (charts.js, mailbox.js 等)
```

## API 路由

### 单股深度报告
- `GET /api/search?q=` — 股票搜索
- `GET /api/report/{symbol}` — 流式生成报告 (HTML SSE)
- `POST /api/mixed-strategy/{symbol}` — 自定义混合策略分析

### 持仓行情
- `GET /api/quotes?symbols=&market=` — 批量行情
- `GET /api/stock-profiles?symbols=&market=` — 批量公司简介
- `POST /api/parse-screenshot` — 上传持仓截图，VLM 解析 + 反查代码

### 报告历史
- `GET /api/history` — 历史报告列表
- `GET /api/history/{report_id}` — 查看历史报告
- `DELETE /api/history/{report_id}` — 删除历史报告

### 持仓来信 (Letter)
- `POST /api/letter/generate` — 生成当日持仓来信
- `GET /api/letters` — 来信列表
- `GET /api/letter/latest` — 最新来信
- `GET /api/letter/{letter_id}` — 来信详情
- `PUT /api/letter/{letter_id}/read` — 标记已读
- `DELETE /api/letter/{letter_id}` — 删除

### 交易诊断 (Diagnosis)
- `POST /api/diagnosis/generate` — 生成交易诊断报告
- `POST /api/diagnosis/chat` — 诊断追问对话 (流式)
- `GET /api/diagnosis/history` — 诊断记录列表
- `GET /api/diagnosis/{diagnosis_id}` — 诊断详情
- `DELETE /api/diagnosis/{diagnosis_id}` — 删除

## 分析报告模块 (12 个)

报告由多个模块顺序编排，通过 LLM 流式生成 HTML：

| 模块 | 名称 | 说明 |
|------|------|------|
| 模块 0 | 投资建议 | 明确操作建议（价格区间、仓位、止损） |
| 模块 1 | 公司在做什么 | 不超过 200 字的人话介绍 |
| 模块 2 | 商业模式 | 收入来源、利润来源、竞争对手、竞争优势 |
| 模块 3 | 财务体检 | 多个财务指标的一句话解读（每个 ≤80 字） |
| 模块 4 | 估值坐标 | 多个估值指标解读（每个 ≤80 字） |
| 模块 5 | 市场分歧 | 研报摘要 + 盈利预测 + 多空分歧 |
| 模块 6 | 股价走势 | 90 日 K 线分析 + 新闻关联 |
| 模块 7 | *(预留)* | — |
| 模块 8 | 三种投资策略 + 混合策略 | 短/中/长线策略 + 杠铃/核心卫星/阶梯/攻守模板 |
| trade_ref | 交易参考 | 综合评估 + 交易区间 + 走势研判 |

> **注意**: 模块 1/3/4 有严格的字数约束（200 字 / 80 字），修改 prompt 时不要随意放开这些限制。

## 核心设计原则

1. **用日常语言**，禁用行业黑话，让散户能看懂
2. **基于数据客观陈述**，不给绝对买卖建议（模块 0 除外）
3. **引导用户思考**，不替用户做决策
4. **所有分析基于公开信息**，不编造数据
5. **语气克制、真诚**，像朋友说话，不打鸡血

## 开发规范

- Python 3.11+，使用 type hints
- 数据层 (`app/data/`) 同步调用 akshare/yfinance，通过 `asyncio.to_thread()` 在线程池执行
- 报告生成使用 `StreamingResponse` 流式输出 HTML
- 新增模块需要在 `app/ai/prompts.py` 添加 prompt 函数，在 `app/report/generator.py` 编排调用
- 数据库模型在 `app/models/` 中，使用 sqlite3 原生 API
- GitHub 推送使用 SSH 密钥认证

# 功能1：单股深度分析 — 技术设计文档

**日期**: 2026-05-01
**状态**: 待审核

---

## Context

知行录项目的第一个功能模块。目标是让用户输入一个A股股票代码/名称，在30秒内获得一份结构化的、有深度的分析报告（HTML页面），覆盖公司介绍、商业模式、财务体检、估值、市场分歧、走势分析等8个模块。这是用户的第一次产品接触，需要在5分钟内产生"啊哈时刻"。

---

## 1. 技术栈

| 层级 | 选型 | 理由 |
|------|------|------|
| Web框架 | FastAPI | 原生支持异步、SSE流式输出、性能好 |
| 金融数据 | akshare | 开源免费，覆盖A股行情/财务/估值/新闻 |
| AI模型 | Claude Sonnet 4.6 (via bilibili LLM Gateway) | OpenAI兼容接口，支持流式 |
| AI SDK | openai (Python) | 网关兼容OpenAI协议 |
| 图表 | ECharts 5.x (CDN) | 功能强大，中文生态好，支持K线图 |
| 前端 | 原生HTML + CSS + JS | 报告是自包含HTML，无需框架 |
| 流式传输 | SSE (Server-Sent Events) | 浏览器原生支持，实现简单 |

## 2. 项目结构

```
zhixinglu/
├── app/
│   ├── main.py                 # FastAPI入口，路由
│   ├── config.py               # 环境变量配置
│   ├── data/                   # 数据层
│   │   ├── stock_search.py     # 股票搜索（代码/名称模糊匹配）
│   │   ├── market_data.py      # 行情数据（K线、实时价格）
│   │   ├── financial_data.py   # 财务数据（报表、指标）
│   │   ├── valuation_data.py   # 估值数据（PE/PB/PS历史+行业）
│   │   └── news_data.py        # 新闻、研报、公告
│   ├── ai/                     # AI层
│   │   ├── llm_client.py       # LLM客户端封装
│   │   ├── prompts.py          # 8个模块的prompt模板
│   │   └── dcf_model.py        # DCF估值纯计算
│   ├── report/                 # 报告生成层
│   │   ├── generator.py        # 报告生成协调器（流式）
│   │   ├── html_template.py    # HTML骨架和CSS样式
│   │   └── chart_config.py     # ECharts图表配置生成
│   └── static/                 # 静态资源
│       └── index.html          # 搜索首页
├── .env                        # 环境变量（API key等）
├── requirements.txt
└── run.py                      # 启动脚本
```

## 3. 核心流程

```
用户输入股票代码/名称
        │
        ▼
  [股票搜索匹配] ─── 无结果 → 返回错误提示
        │
        ▼ 匹配成功
  [并行数据获取] ←── akshare多接口并发调用（asyncio.to_thread包装同步调用）
   ├── 基本信息
   ├── 财务指标（5年）
   ├── K线数据（30日+5年）
   ├── 估值数据（PE/PB/PS历史）
   ├── 行业同行列表+指标
   └── 近期新闻/公告
        │
        ▼ 数据就绪（约3-5秒）
  [逐模块生成] ←── SSE流式推送
   ├── 模块1: 公司介绍（Claude生成）
   ├── 模块2: 商业模式（Claude + 饼图数据）
   ├── 模块3: 财务体检（Claude解读 + DCF计算）
   ├── 模块4: 估值坐标（Claude解读 + 图表数据）
   ├── 模块5: 市场分歧（Claude归纳，数据来自新闻+WebSearch）
   ├── 模块6: 走势分析（Claude分析 + K线图数据）
   ├── 模块7: 财报附录（纯数据/链接）
   └── 模块8: 延展问题（Claude生成）
        │
        ▼
  前端逐模块渲染完成
```

## 4. 各模块详细设计

### 模块1: 这家公司在做什么

- **数据**: `stock_individual_info_em(symbol)` 获取公司基本信息（行业、主营业务）
- **AI**: Claude根据公司名称+行业+主营业务，生成≤150字的日常语言描述
- **图表**: 无
- **Prompt要点**: 禁用行业黑话，用类比和数字让普通人秒懂

### 模块2: 它怎么赚钱

- **数据**: 
  - `stock_profit_sheet_by_report_em(symbol)` 获取利润表（营收分业务）
  - `stock_financial_analysis_indicator(symbol)` 获取毛利率等
  - 行业同行通过 `stock_board_industry_cons_em` 获取
- **AI**: Claude分析收入构成、利润来源、竞争格局
- **图表**: ECharts饼图（收入构成占比）
- **Prompt要点**: 基于数据客观陈述，不评价好坏

### 模块3: 财务体检 + DCF估值

- **数据**:
  - `stock_financial_analysis_indicator(symbol)` → 营收增速、净利润增速、毛利率、ROE
  - `stock_cash_flow_sheet_by_report_em(symbol)` → 经营现金流、资本支出 → 自由现金流
  - 5年历史数据用于趋势图
  - 行业均值：取同行3-5家的相同指标均值
- **AI**: 每个指标一句话解读（客观+引导思考）
- **DCF计算**（纯代码，不依赖AI）:
  - 输入：近5年自由现金流、营收增速
  - 假设：乐观/中性/悲观三档增速、永续增长率2.5%、WACC=10%
  - 输出：每股内在价值（三档）、vs当前股价偏离度
- **图表**: 5个指标的5年折线图 + DCF标尺图

### 模块4: 估值坐标

- **数据**:
  - `stock_a_indicator_lg(symbol)` → PE/PB/PS的历史序列（5年）
  - 行业均值：同行股票的当前PE/PB/PS均值
- **AI**: 每个指标一句话解读
- **图表**: 滑块/位置图（当前值在历史区间的分位数）

### 模块5: 市场分歧

- **数据**:
  - `stock_news_em(symbol)` → 近30天新闻（主要数据源）
  - `stock_research_report_em(symbol)` → 近期研报
  - 如akshare新闻数据不足，后端通过 `httpx` 调用搜索引擎API补充（搜索"[股票名] 分析 观点"）
- **AI**: Claude归纳2-3条看多论点 + 2-3条看空论点
- **图表**: 无
- **Prompt要点**: 不站队，客观呈现分歧

### 模块6: 最近股价走势分析

- **数据**:
  - `stock_zh_a_hist(symbol, period="daily", start_date, end_date)` → 近30日K线
  - `stock_news_em(symbol)` → 同期新闻事件
- **AI**: Claude分析涨跌原因、利好利空因素、支撑压力位
- **图表**: ECharts K线图（标注关键事件节点）

### 模块7: 财报附录

- **数据**: `stock_notice_report(symbol)` 或 WebSearch获取巨潮资讯网链接
- **AI**: 无需AI
- **图表**: HTML表格（财报类型+日期+链接）

### 模块8: 你还想知道什么

- **数据**: 前7个模块的分析上下文
- **AI**: Claude基于公司具体情况生成3个个性化延展问题
- **图表**: 无（可点击的问题列表）

## 5. LLM接入配置

```python
# 使用OpenAI兼容接口，配置从.env加载
import openai

client = openai.OpenAI(
    base_url=os.getenv("LLM_BASE_URL"),   # http://llmapi.bilibili.co/v1
    api_key=os.getenv("LLM_API_KEY"),
)

# 调用Claude Sonnet 4.6
response = client.chat.completions.create(
    model=os.getenv("LLM_MODEL", "claude-4.6-sonnet"),
    messages=[...],
    stream=True,
)
```

**注意**: bilibili LLM Gateway上的模型名称为 `claude-4.6-sonnet`。

## 6. 前端设计

### 6.1 搜索首页
- 居中搜索框，文案"输入一个股票代码，看看不一样的分析"
- 米白背景 `#FAF7F2`，宋体标题
- 支持代码和名称输入，实时模糊搜索下拉提示

### 6.2 报告页面
- 响应式单列布局（移动端友好）
- Web端左侧模块目录导航 + 右侧内容
- 流式加载：每个模块有loading骨架屏，完成后淡入显示
- 设计规范严格遵循PRD：
  - 背景 `#FAF7F2`
  - 标题用思源宋体
  - 正文用思源黑体
  - 涨跌色：淡红 `#D97757` / 淡绿 `#7A9B6E`
  - 强调色：暖金 `#C9A961`
  - 图表简洁无装饰，细线+低饱和度色块

### 6.3 ECharts图表配置
- 饼图：收入构成（模块2）
- 折线图：5年财务指标趋势（模块3）
- 标尺图：DCF估值对比（模块3）+ 估值分位（模块4）
- K线图：30日走势+事件标注（模块6）
- 统一主题色：深墨绿系 + 暖金强调

## 7. 性能策略

| 目标 | 策略 |
|------|------|
| 首屏≤10秒 | 数据并行获取(3-5s) + 模块1-2生成(5s) |
| 完整≤30秒 | 8个模块串行生成，每个约3-4秒 |
| 流式体验 | SSE逐模块推送，用户边看边等 |
| 数据缓存 | 同一股票5分钟内重复请求走缓存 |

## 8. 错误处理

- 股票代码无匹配：友好提示"未找到，请检查代码或名称"
- akshare接口超时/失败：该模块显示"数据获取中，请稍后刷新"，不阻塞其他模块
- Claude API失败：重试1次，仍失败则显示"AI分析暂时不可用"
- 数据缺失（如新上市公司无5年数据）：自适应展示可用数据，标注"数据不足X年"

## 9. 免责声明

- 每个涉及预测/判断的模块底部加免责提示
- 报告底部固定声明："以上为分析框架，非投资建议。投资决策应基于自身研究和判断。"
- DCF模块特别标注："DCF估值基于模型假设，实际价值受多种因素影响，仅作为分析参考框架"

## 10. 验证方案

1. **启动验证**: `python run.py` 启动服务，浏览器访问 `http://localhost:8000`
2. **搜索验证**: 输入"600519"或"贵州茅台"，确认模糊搜索正常
3. **报告生成验证**: 确认8个模块逐一流式渲染，图表正确显示
4. **性能验证**: 首屏≤10秒，完整报告≤30秒
5. **响应式验证**: 缩小浏览器窗口，确认移动端布局正常
6. **错误验证**: 输入无效代码，确认错误提示友好

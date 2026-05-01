SYSTEM_PROMPT = """你是"知行录"的AI分析师。你的任务是为散户投资者生成高质量的单股深度分析报告。

核心原则：
1. 用日常语言，禁用行业黑话，让普通人能看懂
2. 基于数据客观陈述，不给买卖建议
3. 引导用户思考，而不是替用户做决策
4. 所有分析基于公开信息，不编造数据
5. 语气克制、真诚，像朋友说话，不打鸡血"""


def _format_dict(d: dict) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in d.items() if v)


def module1_prompt(stock_name: str, stock_info: dict) -> list[dict]:
    """模块1：这家公司在做什么（人话版）"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请用不超过150字的日常语言介绍"{stock_name}"这家公司在做什么。

公司信息：
{_format_dict(stock_info)}

要求：
- 完全用日常语言，禁用行业黑话
- 用类比和具体数字让普通人秒懂
- 说清楚它的主要产品/服务是什么，客户是谁
- 不要用"该公司"这种书面语，直接说公司名

直接输出介绍文字，不要加标题或前缀。"""}
    ]


def module2_prompt(stock_name: str, profit_data: str, indicators: str, peers_info: str) -> list[dict]:
    """模块2：它怎么赚钱（商业模式）"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请分析"{stock_name}"的商业模式。

利润表数据（最近年报）：
{profit_data}

财务指标：
{indicators}

主要竞争对手信息：
{peers_info}

请按以下结构输出（纯文字，不要markdown标记）：

1. 收入来源：这家公司的钱主要从哪几块业务来的，各占多少比例
2. 利润来源：哪块业务最赚钱，整体利润率水平如何
3. 主要竞争对手：列出2-3个主要对手
4. 竞争优势：基于公开信息客观陈述，不评价好坏

用日常语言，简洁明了。"""}
    ]


def module3_indicator_prompt(stock_name: str, indicator_name: str, current_value: str,
                              trend_data: str, peer_avg: str) -> list[dict]:
    """模块3：财务体检 — 单个指标的一句话解读"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请用一句话解读"{stock_name}"的{indicator_name}。

当前值：{current_value}
近5年趋势：{trend_data}
同行均值：{peer_avg}

要求：
- 一句话，不超过80字
- 客观陈述趋势 + 结合公司业务特点和行业背景，解释数据变化的可能原因
- 用因果关系说明，不要只描述数字

直接输出这句话。"""}
    ]


def module4_prompt(stock_name: str, indicator_name: str, current_value: str,
                   hist_range: str, percentile: str, peer_avg: str) -> list[dict]:
    """模块4：估值坐标 — 单个估值指标解读"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请用一句话解读"{stock_name}"的{indicator_name}估值水平。

当前值：{current_value}
历史5年区间：{hist_range}
当前所处分位：{percentile}
同行均值：{peer_avg}

要求：一句话，不超过80字，客观陈述 + 引导思考。直接输出。"""}
    ]


def module5_prompt(stock_name: str, news_text: str, report_text: str) -> list[dict]:
    """模块5：市场分歧"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""基于以下近30天的公开信息，归纳市场对"{stock_name}"的分歧。

近期新闻：
{news_text}

近期研报摘要：
{report_text}

请输出：
看多核心论点（2-3条，每条一句话）
看空核心论点（2-3条，每条一句话）

要求：
- 不站队，不判断对错
- 客观呈现市场不同声音
- 每条论点要有具体依据，不要泛泛而谈
- 每条论点必须标注信息来源和发布日期，格式：论点内容（来源：xxx，日期：yyyy-mm-dd）
- 来源要具体到新闻标题或研报机构名称
- 格式：先列看多，再列看空，用数字编号

直接输出，不要加额外标题。"""}
    ]


def module6_prompt(stock_name: str, kline_summary: str, news_text: str) -> list[dict]:
    """模块6：最近股价走势分析"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""请分析"{stock_name}"近90个交易日的股价走势。

K线数据摘要：
{kline_summary}

同期新闻事件：
{news_text}

请按以下结构输出：

1. 走势概述：区间涨跌幅、最高价、最低价、成交量变化趋势（一句话）
2. 涨跌原因：结合同期新闻事件，分析主要涨跌原因（2-3条，标注日期）
3. 利好因素：可能推动股价上行的催化剂（2-3条）
4. 利空因素：可能导致股价下行的风险点（2-3条）
5. 关键价位：近期支撑位和压力位参考

用日常语言，简洁明了。直接输出，不要加额外标题。"""}
    ]


def module_trade_ref_prompt(stock_name: str, full_context: str) -> list[dict]:
    """模块：交易参考 — 综合所有数据给出交易参考"""
    return [
        {"role": "system", "content": """你是"知行录"的AI分析师。你的任务是基于全面的数据分析，为投资者提供交易参考信息。

核心原则：
1. 所有分析基于公开数据和量化指标，不编造数据
2. 明确标注每个结论的数据依据
3. 给出具体的价格区间和条件判断
4. 语气客观专业，不打鸡血也不制造恐慌
5. 必须强调这是分析参考，不构成投资建议"""},
        {"role": "user", "content": f"""基于以下对"{stock_name}"的完整分析数据，给出综合交易参考。

分析数据汇总：
{full_context}

请按以下结构输出：

1. 综合评估：用2-3句话概括这只股票当前的整体状态（估值水平、基本面趋势、市场情绪）

2. 合理买入区间：
   - 给出具体的价格区间（结合DCF估值、技术面支撑位、估值分位）
   - 说明依据

3. 合理卖出区间：
   - 给出具体的价格区间（结合DCF估值、技术面压力位、历史估值上限）
   - 说明依据

4. 后续走势研判：
   - 短期（1-3个月）可能走势及关键催化剂
   - 中期（3-12个月）可能走势及核心变量
   - 需要关注的风险信号

5. 关键条件：列出2-3个可能改变上述判断的关键条件

用日常语言，简洁明了。直接输出，不要加额外标题。"""}
    ]


def module8_prompt(stock_name: str, report_context: str) -> list[dict]:
    """模块8：延展问题"""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"""基于以下对"{stock_name}"的分析报告内容，生成3个用户可能感兴趣的延展问题。

报告摘要：
{report_context}

要求：
- 问题要基于该公司的具体情况个性化生成
- 覆盖用户可能关心但报告未深入展开的方向
- 每个问题一句话，要有思考深度
- 用数字编号，每行一个问题

直接输出3个问题。"""}
    ]

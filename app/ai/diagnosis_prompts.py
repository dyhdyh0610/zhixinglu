from app.ai.letter_prompts import ANALYST_SYSTEM

DIAGNOSIS_SYSTEM = """你是"知行录"的AI交易诊断师。你的任务是对用户即将执行的交易进行系统性分析，帮助用户看到可能忽略的维度。

核心原则：
1. 辩证分析，既看利好也看风险
2. 基于数据客观陈述，不给"买/不买"的直接建议
3. 指出用户可能忽略的盲点
4. 语气克制、真诚，像一个理性的朋友
5. 所有分析基于公开信息，不编造数据
6. 输出必须是合法JSON，不要包含任何其他文字"""


def value_diagnosis_prompt(stock_name: str, financials_str: str, valuation_str: str,
                           research_str: str, trade_intent_str: str,
                           report_context: str = "") -> list[dict]:
    context_section = ""
    if report_context:
        context_section = f"\n\n---\n以下是该股票的完整分析报告，供你参考（请从中提取与价值分析相关的信息辅助判断）：\n{report_context}"

    return [
        {"role": "system", "content": DIAGNOSIS_SYSTEM},
        {"role": "user", "content": f"""对"{stock_name}"进行股票价值诊断，输出JSON对象。

交易意图：{trade_intent_str}

财务数据：
{financials_str}

估值数据：
{valuation_str}

近期研报：
{research_str}{context_section}

输出格式（严格JSON对象）：
{{
  "valuation_level": "偏低/合理/偏高",
  "pe_info": "PE(TTM)数值及历史分位描述",
  "pb_info": "PB数值及历史分位描述",
  "dcf_range": "DCF参考价区间描述",
  "target_price_assessment": "目标价格相对估值的评估（一句话）",
  "research_consensus": "近期研报一致观点（一句话）",
  "core_logic": "当前市场对该股的核心投资逻辑（一句话）",
  "diagnosis": "综合价值诊断（50-100字，辩证分析，指出关键点）",
  "risk_point": "最大的价值风险点（一句话）"
}}

直接输出JSON对象。"""}
    ]


def position_diagnosis_prompt(trade_intent_str: str, current_portfolio_str: str,
                              post_trade_portfolio_str: str,
                              report_context: str = "") -> list[dict]:
    context_section = ""
    if report_context:
        context_section = f"\n\n---\n以下是该股票的完整分析报告，供你参考（请从中提取与仓位分析相关的信息辅助判断）：\n{report_context}"

    return [
        {"role": "system", "content": DIAGNOSIS_SYSTEM},
        {"role": "user", "content": f"""分析这笔交易对组合仓位的影响，输出JSON对象。

交易意图：{trade_intent_str}

当前组合：
{current_portfolio_str}

交易后组合：
{post_trade_portfolio_str}{context_section}

输出格式（严格JSON对象）：
{{
  "position_change": "仓位占比变化描述（如 23.4% → 31.2%）",
  "industry_concentration": "行业集中度变化描述",
  "top3_concentration": "前3大持仓集中度变化",
  "correlation_risk": "与现有持仓的相关性风险（如同行业、同板块）",
  "diversification_score": 1-5,
  "diagnosis": "综合仓位诊断（50-100字，指出集中度风险或分散化建议）",
  "suggestion": "一句话建议"
}}

字段说明：
- diversification_score：1=极度集中有风险，3=适中，5=分散良好
- 如果用户无其他持仓，仅评估单一持仓的风险

直接输出JSON对象。"""}
    ]


def timing_diagnosis_prompt(stock_name: str, kline_str: str, detail_str: str,
                            news_str: str, trade_intent_str: str,
                            report_context: str = "") -> list[dict]:
    context_section = ""
    if report_context:
        context_section = f"\n\n---\n以下是该股票的完整分析报告，供你参考（请从中提取与时机分析相关的信息辅助判断）：\n{report_context}"

    return [
        {"role": "system", "content": DIAGNOSIS_SYSTEM},
        {"role": "user", "content": f"""请先搜索"{stock_name}"最近一周的重要消息，然后分析这笔交易的时机，输出JSON对象。

交易意图：{trade_intent_str}

近30日K线摘要：
{kline_str}

技术指标：
{detail_str}

近期新闻：
{news_str}{context_section}

输出格式（严格JSON对象）：
{{
  "signals": ["信号标签1", "信号标签2"],
  "trend_description": "当前趋势描述（一句话）",
  "support_price": 0.0,
  "resistance_price": 0.0,
  "volume_analysis": "成交量分析（一句话）",
  "catalyst": "近期可能的催化剂事件（一句话）",
  "risk_event": "近期可能的风险事件（一句话）",
  "timing_score": 1-5,
  "diagnosis": "综合时机诊断（50-100字，辩证分析当前是否是好的交易时机）"
}}

字段说明：
- signals：从以下标签中选取1-3个：突破MA20、跌破MA20、放量、缩量、主力流入、主力流出、超买、超卖、创新高、创新低、均线多头、均线空头
- timing_score：1=时机很差，3=中性，5=时机很好
- support_price/resistance_price：基于技术面的支撑位和压力位

直接输出JSON对象。"""}
    ]


def market_diagnosis_prompt(market_str: str, portfolio_str: str,
                            trade_intent_str: str,
                            report_context: str = "") -> list[dict]:
    context_section = ""
    if report_context:
        context_section = f"\n\n---\n以下是该股票的完整分析报告，供你参考（请从中提取与市场分析相关的信息辅助判断）：\n{report_context}"

    return [
        {"role": "system", "content": DIAGNOSIS_SYSTEM},
        {"role": "user", "content": f"""请搜索今日A股市场最新动态，然后分析当前市场环境对这笔交易的影响，输出JSON对象。

交易意图：{trade_intent_str}

市场数据：
{market_str}

组合概况：{portfolio_str}{context_section}

输出格式（严格JSON对象）：
{{
  "sentiment_score": 65,
  "sentiment_label": "偏暖",
  "market_summary": "一句话总结今日市场（25-40字）",
  "sector_status": "目标股票所在板块今日表现",
  "north_flow": "北向资金动向描述",
  "macro_risk": "当前宏观风险提示（一句话）",
  "diagnosis": "市场环境对这笔交易的影响评估（50-80字）"
}}

字段说明：
- sentiment_score：0-100，0=极度恐慌，50=中性，100=极度贪婪
- sentiment_label：恐慌/偏冷/中性/偏暖/贪婪，五选一

直接输出JSON对象。"""}
    ]


def sector_diagnosis_prompt(stock_name: str, industry_name: str, industry_data_str: str,
                            stock_info_str: str, trade_intent_str: str,
                            report_context: str = "") -> list[dict]:
    context_section = ""
    if report_context:
        context_section = f"\n\n---\n以下是该股票的完整分析报告，供你参考：\n{report_context}"

    return [
        {"role": "system", "content": DIAGNOSIS_SYSTEM},
        {"role": "user", "content": f"""请搜索"{stock_name}"所在的"{industry_name}"行业的最新动态和主要竞争对手信息，然后分析板块环境，输出JSON对象。

交易意图：{trade_intent_str}

公司信息：
{stock_info_str}

行业近期数据：
{industry_data_str}{context_section}

分析要求：
1. 分析该行业近期走势及原因
2. 判断行业整体估值水平
3. 识别3-5个主要竞争对手，对比核心优劣势
4. 给出该公司在板块中的投资价值排名

输出格式（严格JSON对象）：
{{
  "industry_trend": "行业近期走势描述及原因（50-80字）",
  "industry_valuation": "行业估值水平描述（一句话）",
  "competitors": [
    {{
      "name": "竞争对手名称",
      "ticker": "股票代码",
      "advantage": "核心优势（一句话）",
      "disadvantage": "核心劣势（一句话）"
    }}
  ],
  "target_rank": 2,
  "target_rank_total": 5,
  "rank_reason": "排名理由（一句话）",
  "sector_score": 1-5,
  "diagnosis": "从板块角度对这笔交易的诊断（50-100字）"
}}

字段说明：
- target_rank：目标公司在竞争对手中的投资价值排名（1=最值得投资）
- target_rank_total：参与排名的公司总数
- sector_score：1=行业环境很差不适合投资，3=中性，5=行业景气度高适合投资

直接输出JSON对象。"""}
    ]


def conclusion_prompt(trade_intent_str: str, value_analysis: str,
                      position_analysis: str, timing_analysis: str,
                      market_analysis: str, sector_analysis: str = "",
                      user_reason: str = "") -> list[dict]:
    reason_part = f"\n用户的交易理由：{user_reason}" if user_reason else ""
    sector_part = f"\n\n板块环境分析：\n{sector_analysis}" if sector_analysis else ""
    return [
        {"role": "system", "content": """你是"知行录"的AI交易诊断师。基于前面各维度的分析，给出综合诊断结论。

输出要求：
- 必须输出合法JSON对象
- 客观、辩证、有深度
- 不给"买/不买"的直接建议
- 指出最值得关注的2-3个点
- 如果有明显风险，直接指出
- 语气像一个理性的朋友在提醒你
- suggested_questions 必须与本次具体交易高度相关，从用户视角出发"""},
        {"role": "user", "content": f"""综合以下各维度分析，给出这笔交易的综合诊断结论。

交易意图：{trade_intent_str}{reason_part}

股票价值分析：
{value_analysis}

仓位管理分析：
{position_analysis}

交易时机分析：
{timing_analysis}

市场环境分析：
{market_analysis}{sector_part}

输出格式（严格JSON对象）：
{{
  "conclusion": "综合诊断结论（150-250字，先一句话概括，再列2-3个关键点，最后一句话总结）",
  "key_points": ["关键点1", "关键点2", "关键点3"],
  "confidence_score": 1-5,
  "confidence_reason": "信心评分理由（一句话）",
  "suggested_questions": [
    "与本次交易高度相关的追问问题1",
    "与本次交易高度相关的追问问题2",
    "与本次交易高度相关的追问问题3"
  ]
}}

字段说明：
- confidence_score：1=强烈不建议（多维度风险），2=多数维度不支持，3=支持和反对各半，4=大部分支持（少量风险），5=多维度强烈支持
- suggested_questions：从用户视角出发，看完整个分析后最可能追问的3个问题，覆盖不同角度（风险、操作建议、替代方案等），必须包含具体股票名称或数据

直接输出JSON对象。"""}
    ]


def chat_system_prompt(diagnosis_summary: str, holdings_str: str,
                       market_str: str) -> str:
    return f"""你是"知行录"的AI交易诊断师，正在和用户讨论一笔交易诊断的结果。

之前的诊断摘要：
{diagnosis_summary}

用户当前持仓：
{holdings_str}

市场概况：
{market_str}

回答原则：
- 基于已有的诊断数据和公开信息回答
- 如果用户问到新的假设（如调整价格），基于逻辑推理给出分析
- 保持客观辩证，不给直接的买卖建议
- 简洁有力，每次回答不超过200字
- 用中文回答"""

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

知行录 (zhixinglu) — AI-powered single-stock deep analysis report generator for retail investors. A FastAPI web app that fetches Chinese A-share market data via akshare, runs it through 10 sequential LLM analysis modules, and streams the resulting HTML report to the browser.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run dev server (http://0.0.0.0:5001, hot reload)
python3 run.py
```

No test framework or linter is configured.

## Environment

Requires a `.env` file with:
- `LLM_BASE_URL` — OpenAI-compatible API endpoint
- `LLM_API_KEY` — API key
- `LLM_MODEL` — model name (default: `claude-4.6-sonnet`)

Config is loaded in `app/config.py` via python-dotenv.

## Architecture

**Entry point**: `run.py` → `app/main.py` (FastAPI + uvicorn)

**API endpoints**:
- `GET /api/search?keyword=` — stock symbol/name search
- `GET /api/report/{symbol}` — streams HTML report via `StreamingResponse`

**Data flow**: User searches stock → selects one → server fetches 11 data sources concurrently via `asyncio.to_thread()` (akshare is sync) → 10 report modules run sequentially, each calling the LLM → HTML chunks streamed to client for progressive rendering.

**Three layers**:

| Layer | Path | Role |
|-------|------|------|
| Data | `app/data/` | Fetches financial statements, K-line, valuations, news, research reports from akshare. `market_data.py` caches K-line in memory. |
| AI | `app/ai/` | `llm_client.py` wraps OpenAI SDK for the configured endpoint. `prompts.py` holds 10 Chinese system prompts (one per module). `dcf_model.py` runs a two-stage DCF valuation (weighted FCF, net debt adjustment). |
| Report | `app/report/` | `generator.py` orchestrates the 10 modules and yields HTML. `html_template.py` provides CSS/HTML structure. `chart_config.py` generates ECharts configs. |

**10 report modules** (in `generator.py`): company overview → business model → financial health + DCF → valuation percentiles → analyst forecasts → market divergence → price trend + technicals → financial reports index → trading reference → key reflection questions.

**Frontend**: `app/static/index.html` — vanilla HTML/JS with ECharts. The DCF section includes client-side JS for interactive parameter adjustment (WACC, growth rates).

## Key Patterns

- All akshare calls are blocking and wrapped in `asyncio.to_thread()`.
- LLM calls go through `app/ai/llm_client.py` which uses the OpenAI SDK pointed at the configured base URL.
- Report generation is a single async generator; each module appends HTML and yields it as a chunk.
- No database — all data is fetched on-demand per request.
- Prompts are in Chinese and written for a retail investor audience ("人话版").

请用中文来和我交互，包括回答问题，提问问题等，我的英语水平不太好
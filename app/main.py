import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import os

from app.data.stock_search import search_stock
from app.report.generator import generate_report

app = FastAPI(title="知行录 - 单股深度分析")

static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", response_class=HTMLResponse)
async def index():
    with open(os.path.join(static_dir, "index.html"), "r", encoding="utf-8") as f:
        return f.read()


@app.get("/api/search")
async def api_search(q: str = ""):
    results = await asyncio.to_thread(search_stock, q)
    return JSONResponse(results)


@app.get("/api/report/{symbol}")
async def api_report(symbol: str):
    async def stream():
        async for chunk in generate_report(symbol):
            yield chunk
    return StreamingResponse(stream(), media_type="text/html; charset=utf-8")

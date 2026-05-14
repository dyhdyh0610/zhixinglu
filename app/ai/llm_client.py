import time
import openai
from app.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

_client: openai.OpenAI | None = None


def get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    return _client


def chat(messages: list[dict], temperature: float = 0.7) -> str:
    """同步调用LLM，返回完整文本。带超时和指数退避重试。"""
    client = get_client()
    max_retries = 2
    for attempt in range(max_retries + 1):
        try:
            resp = client.chat.completions.create(
                model=LLM_MODEL, messages=messages, temperature=temperature, timeout=120
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            print(f"[LLM chat] 调用失败 (attempt {attempt + 1}/{max_retries + 1}): {e}")
            if attempt < max_retries:
                delay = 2 ** (attempt + 1)  # 2s, 4s
                print(f"[LLM chat] {delay}s 后重试...")
                time.sleep(delay)
    print("[LLM chat] 所有重试均失败，返回空字符串")
    return ""


def chat_with_search(messages: list[dict], temperature: float = 0.7) -> str:
    """同步调用LLM。DashScope 的 web_search 工具返回 tool_calls 且无 content，
    且不带工具的调用容易超时，因此直接走普通 chat，基于传入的完整数据生成分析。"""
    return chat(messages, temperature)


def chat_stream(messages: list[dict], temperature: float = 0.7):
    """流式调用LLM，yield每个文本片段。带异常处理。"""
    client = get_client()
    try:
        stream = client.chat.completions.create(
            model=LLM_MODEL, messages=messages, temperature=temperature, stream=True, timeout=120
        )
        for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                yield delta.content
    except Exception as e:
        print(f"[LLM chat_stream] 调用失败: {e}")
        yield f"\n\n[错误: LLM调用失败 - {e}]\n"

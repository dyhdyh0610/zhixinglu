import openai
from app.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL

_client: openai.OpenAI | None = None


def get_client() -> openai.OpenAI:
    global _client
    if _client is None:
        _client = openai.OpenAI(base_url=LLM_BASE_URL, api_key=LLM_API_KEY)
    return _client


def chat(messages: list[dict], temperature: float = 0.7) -> str:
    """同步调用LLM，返回完整文本。"""
    client = get_client()
    resp = client.chat.completions.create(
        model=LLM_MODEL, messages=messages, temperature=temperature
    )
    return resp.choices[0].message.content


def chat_with_search(messages: list[dict], temperature: float = 0.7) -> str:
    """同步调用LLM并启用web search工具，返回完整文本。"""
    client = get_client()
    try:
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=temperature,
            tools=[{"type": "web_search_20250305"}],
        )
        return resp.choices[0].message.content or ""
    except Exception:
        return chat(messages, temperature)


def chat_stream(messages: list[dict], temperature: float = 0.7):
    """流式调用LLM，yield每个文本片段。"""
    client = get_client()
    stream = client.chat.completions.create(
        model=LLM_MODEL, messages=messages, temperature=temperature, stream=True
    )
    for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content

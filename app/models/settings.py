import sqlite3
import os
from datetime import datetime

_DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "history.db")


def _get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_settings_db():
    conn = _get_conn()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def get_setting(key: str) -> str | None:
    conn = _get_conn()
    row = conn.execute(
        "SELECT value FROM user_settings WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    return row["value"] if row else None


def set_setting(key: str, value: str):
    now = datetime.now().isoformat()
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO user_settings (key, value, updated_at) VALUES (?, ?, ?)",
        (key, value, now),
    )
    conn.commit()
    conn.close()


def get_all_settings() -> dict:
    conn = _get_conn()
    rows = conn.execute("SELECT key, value FROM user_settings").fetchall()
    conn.close()
    return {row["key"]: row["value"] for row in rows}


def get_llm_config() -> dict:
    """获取 LLM 配置。用户设置优先，无则返回 None（由调用方 fallback 到环境变量）。"""
    base_url = get_setting("llm_base_url")
    api_key = get_setting("llm_api_key")
    model = get_setting("llm_model")

    if not api_key:
        return None

    return {
        "base_url": base_url,
        "api_key": api_key,
        "model": model,
    }


def delete_setting(key: str):
    conn = _get_conn()
    conn.execute("DELETE FROM user_settings WHERE key = ?", (key,))
    conn.commit()
    conn.close()

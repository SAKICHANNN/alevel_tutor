"""
SQLite database for conversation persistence, grading records, error logging, and cost tracking.

Architecture:
  - WAL mode + busy_timeout for safe concurrent access
  - All writes go through a single threading.Lock queue
  - 6 tables: users, conversations, messages, grading_results, error_logs, cost_logs
  - Single user (desktop app pilot), auto-creates on first use
"""
import json
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from agent.config import DATA_DIR

DB_PATH = DATA_DIR / "tutor.db"

# Module-level connection and lock
_conn: Optional[sqlite3.Connection] = None
_lock = threading.Lock()
_initialized = False


def _get_conn() -> sqlite3.Connection:
    """Get or create the SQLite connection with WAL mode."""
    global _conn, _initialized
    if _conn is not None:
        return _conn
    with _lock:
        if _conn is not None:
            return _conn
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        _conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.execute("PRAGMA busy_timeout=5000")
        _conn.execute("PRAGMA foreign_keys=ON")
        _conn.row_factory = sqlite3.Row
        _initialized = True
    return _conn


def _migrate():
    """Idempotent migration. Creates tables if they don't exist."""
    conn = _get_conn()
    with _lock:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL DEFAULT 'local_user',
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            settings TEXT DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS conversations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL DEFAULT 1,
            subject_code TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now')),
            title TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user','assistant','system','tool')),
            content TEXT NOT NULL,
            tool_calls TEXT,
            tool_call_id TEXT,
            citation_chips TEXT,
            token_count INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE TABLE IF NOT EXISTS grading_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER NOT NULL,
            message_id INTEGER,
            question TEXT NOT NULL,
            mark_scheme TEXT,
            student_answer TEXT NOT NULL,
            score_awarded REAL NOT NULL,
            score_max REAL NOT NULL,
            confidence REAL,
            verdict TEXT,
            rubric_correctness REAL,
            rubric_method REAL,
            rubric_representation REAL,
            rubric_communication REAL,
            strengths TEXT,
            mistakes TEXT,
            misconception_tags TEXT,
            next_step TEXT,
            citations TEXT,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (conversation_id) REFERENCES conversations(id),
            FOREIGN KEY (message_id) REFERENCES messages(id)
        );

        CREATE TABLE IF NOT EXISTS error_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            error_type TEXT NOT NULL,
            error_source TEXT NOT NULL,
            error_message TEXT NOT NULL,
            subject_code TEXT,
            misconception_tags TEXT,
            payload_snippet TEXT,
            stack_trace TEXT,
            resolved BOOLEAN DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (conversation_id) REFERENCES conversations(id)
        );

        CREATE TABLE IF NOT EXISTS cost_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            conversation_id INTEGER,
            message_id INTEGER,
            model_key TEXT NOT NULL,
            model_name TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            reasoning_tokens INTEGER DEFAULT 0,
            total_tokens INTEGER DEFAULT 0,
            estimated_cost_usd REAL DEFAULT 0.0,
            estimated_cost_cny REAL DEFAULT 0.0,
            latency_ms INTEGER,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (conversation_id) REFERENCES conversations(id),
            FOREIGN KEY (message_id) REFERENCES messages(id)
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_grading_conv ON grading_results(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_error_created ON error_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_cost_created ON cost_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_cost_model ON cost_logs(model_key, created_at);
        """)
        conn.commit()
    _ensure_user()


def _ensure_user():
    conn = _get_conn()
    with _lock:
        conn.execute("INSERT OR IGNORE INTO users (id, username) VALUES (1, 'local_user')")
        conn.commit()


def init_db():
    """Initialize the database. Call once at app startup. Idempotent."""
    _get_conn()
    _migrate()
    return DB_PATH


# ═══════════════════════════════════════════════════════════
# Conversations
# ═══════════════════════════════════════════════════════════

def create_conversation(subject_code: Optional[str] = None, title: Optional[str] = None) -> int:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            "INSERT INTO conversations (user_id, subject_code, title) VALUES (1, ?, ?)",
            (subject_code, title)
        )
        conn.commit()
        return cur.lastrowid


def update_conversation(conv_id: int, **kwargs):
    allowed = {"subject_code", "title"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return
    updates["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [conv_id]
    conn = _get_conn()
    with _lock:
        conn.execute(f"UPDATE conversations SET {set_clause} WHERE id = ?", values)
        conn.commit()


def get_conversation(conv_id: int) -> Optional[dict]:
    conn = _get_conn()
    row = conn.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,)).fetchone()
    return dict(row) if row else None


def list_conversations(limit: int = 20) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,)
    ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
# Messages
# ═══════════════════════════════════════════════════════════

def save_message(conversation_id: int, role: str, content: str,
                 tool_calls: Optional[list] = None,
                 tool_call_id: Optional[str] = None,
                 citation_chips: Optional[list] = None,
                 token_count: Optional[int] = None) -> int:
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            """INSERT INTO messages (conversation_id, role, content, tool_calls, tool_call_id, citation_chips, token_count)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                conversation_id, role, content,
                json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
                tool_call_id,
                json.dumps(citation_chips, ensure_ascii=False) if citation_chips else None,
                token_count,
            )
        )
        conn.execute(
            "UPDATE conversations SET updated_at = datetime('now') WHERE id = ?",
            (conversation_id,)
        )
        conn.commit()
        return cur.lastrowid


def get_messages(conversation_id: int, limit: int = 50) -> list:
    conn = _get_conn()
    rows = conn.execute(
        "SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC LIMIT ?",
        (conversation_id, limit)
    ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
# Grading Results
# ═══════════════════════════════════════════════════════════

def save_grading_result(conversation_id: int, grading: dict,
                        question: str = "", mark_scheme: str = "",
                        student_answer: str = "", message_id: Optional[int] = None) -> int:
    rubric = grading.get("rubric", {})
    conn = _get_conn()
    with _lock:
        cur = conn.execute(
            """INSERT INTO grading_results
               (conversation_id, message_id, question, mark_scheme, student_answer,
                score_awarded, score_max, confidence, verdict,
                rubric_correctness, rubric_method, rubric_representation, rubric_communication,
                strengths, mistakes, misconception_tags, next_step, citations)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                conversation_id, message_id, question, mark_scheme, student_answer,
                grading.get("score_awarded", 0),
                grading.get("score_max", 0),
                grading.get("confidence", 0.0),
                grading.get("verdict", ""),
                rubric.get("correctness"),
                rubric.get("method"),
                rubric.get("representation"),
                rubric.get("communication"),
                json.dumps(grading.get("strengths", []), ensure_ascii=False),
                json.dumps(grading.get("mistakes", []), ensure_ascii=False),
                json.dumps(grading.get("misconception_tags", []), ensure_ascii=False),
                grading.get("next_step", ""),
                json.dumps(grading.get("citations", []), ensure_ascii=False),
            )
        )
        conn.commit()
        return cur.lastrowid


# ═══════════════════════════════════════════════════════════
# Error Logs (batch-write friendly)
# ═══════════════════════════════════════════════════════════

VALID_ERROR_TYPES = {"api_call", "grading_fail", "tool_fail", "parse_fail",
                     "timeout", "vision_fail", "embed_fail", "db_fail",
                     "unknown"}

VALID_CONCEPT_TAGS = {"concept", "method", "algebra", "units", "diagram_reading",
                      "essay_structure", "translation", "carelessness", "system_error"}


def log_error(error_type: str, error_source: str, error_message: str,
              conversation_id: Optional[int] = None,
              subject_code: Optional[str] = None,
              misconception_tags: Optional[list] = None,
              payload_snippet: Optional[str] = None,
              stack_trace: Optional[str] = None):
    """Log an error. Validates types, writes immediately (errors are rare)."""
    if error_type not in VALID_ERROR_TYPES:
        error_type = "unknown"
    if misconception_tags:
        misconception_tags = [t for t in misconception_tags if t in VALID_CONCEPT_TAGS]

    conn = _get_conn()
    with _lock:
        conn.execute(
            """INSERT INTO error_logs
               (conversation_id, error_type, error_source, error_message,
                subject_code, misconception_tags, payload_snippet, stack_trace)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                conversation_id, error_type, error_source, error_message,
                subject_code,
                json.dumps(misconception_tags, ensure_ascii=False) if misconception_tags else None,
                payload_snippet[:500] if payload_snippet else None,
                stack_trace[:2000] if stack_trace else None,
            )
        )
        conn.commit()


def get_recent_errors(error_type: Optional[str] = None, limit: int = 20) -> list:
    conn = _get_conn()
    if error_type:
        rows = conn.execute(
            "SELECT * FROM error_logs WHERE error_type = ? ORDER BY created_at DESC LIMIT ?",
            (error_type, limit)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM error_logs ORDER BY created_at DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
# Cost Logs
# ═══════════════════════════════════════════════════════════

# Pricing table (per 1M tokens, USD)
# Updated 2025-06: DeepSeek V4-Flash pricing
PRICING = {
    "deepseek-v4-flash": {"prompt": 0.14, "completion": 0.28},
    "glm-4v-plus": {"prompt": 0.72, "completion": 0.72},       # ~¥5/M
    "qwen-vl-max": {"prompt": 0.42, "completion": 1.26},        # ~$3/$9 per 1M
    "qwen/qwen3-vl-8b": {"prompt": 0.0, "completion": 0.0},     # local, free
}
USD_TO_CNY = 7.25


def log_cost(model_key: str, model_name: str,
             prompt_tokens: int = 0,
             completion_tokens: int = 0,
             reasoning_tokens: int = 0,
             latency_ms: int = 0,
             conversation_id: Optional[int] = None,
             message_id: Optional[int] = None):
    total = prompt_tokens + completion_tokens  # completion_tokens already includes reasoning
    pricing = PRICING.get(model_name, {"prompt": 0.14, "completion": 0.28})
    cost_usd = (prompt_tokens / 1_000_000 * pricing["prompt"] +
                completion_tokens / 1_000_000 * pricing["completion"])
    cost_cny = round(cost_usd * USD_TO_CNY, 4)
    cost_usd = round(cost_usd, 6)

    conn = _get_conn()
    with _lock:
        conn.execute(
            """INSERT INTO cost_logs
               (conversation_id, message_id, model_key, model_name,
                prompt_tokens, completion_tokens, reasoning_tokens, total_tokens,
                estimated_cost_usd, estimated_cost_cny, latency_ms)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                conversation_id, message_id, model_key, model_name,
                prompt_tokens, completion_tokens, reasoning_tokens, total,
                cost_usd, cost_cny, latency_ms,
            )
        )
        conn.commit()


def get_total_cost(days: int = 30) -> dict:
    conn = _get_conn()
    row = conn.execute(
        """SELECT COALESCE(SUM(prompt_tokens),0) as prompt,
                  COALESCE(SUM(completion_tokens),0) as completion,
                  COALESCE(SUM(reasoning_tokens),0) as reasoning,
                  COALESCE(SUM(total_tokens),0) as total_tokens,
                  COALESCE(SUM(estimated_cost_usd),0) as cost_usd,
                  COALESCE(SUM(estimated_cost_cny),0) as cost_cny,
                  COUNT(*) as calls
           FROM cost_logs
           WHERE created_at >= datetime('now', ?)""",
        (f"-{days} days",)
    ).fetchone()
    return dict(row) if row else {}


def get_daily_costs(days: int = 7) -> list:
    conn = _get_conn()
    rows = conn.execute(
        """SELECT date(created_at) as day,
                  SUM(estimated_cost_cny) as cost_cny,
                  SUM(total_tokens) as tokens,
                  COUNT(*) as calls
           FROM cost_logs
           WHERE created_at >= datetime('now', ?)
           GROUP BY day ORDER BY day DESC""",
        (f"-{days} days",)
    ).fetchall()
    return [dict(r) for r in rows]


# ═══════════════════════════════════════════════════════════
# BudgetGuard
# ═══════════════════════════════════════════════════════════

# Default budget: ¥50/month, ¥2/day
DEFAULT_MONTHLY_BUDGET_CNY = float(os.getenv("BUDGET_MONTHLY_CNY", "50"))
DEFAULT_DAILY_BUDGET_CNY = float(os.getenv("BUDGET_DAILY_CNY", "2"))


def check_budget() -> tuple[bool, str]:
    """Check if we're within budget. Returns (ok, reason)."""
    monthly = get_total_cost(days=30)
    # Daily budget: use today's date, not past 24 hours
    daily = _get_today_cost()

    monthly_cost = monthly.get("cost_cny", 0) or 0
    daily_cost = daily.get("cost_cny", 0) or 0

    if monthly_cost > DEFAULT_MONTHLY_BUDGET_CNY:
        return False, (
            f"月度预算超限: ¥{monthly_cost:.2f} > ¥{DEFAULT_MONTHLY_BUDGET_CNY:.0f}。"
            f"本月 API 调用已被限制。"
        )
    if daily_cost > DEFAULT_DAILY_BUDGET_CNY:
        return False, (
            f"每日预算超限: ¥{daily_cost:.2f} > ¥{DEFAULT_DAILY_BUDGET_CNY:.0f}。"
            f"请明天再试。"
        )
    return True, f"预算正常: 月 ¥{monthly_cost:.2f}/{DEFAULT_MONTHLY_BUDGET_CNY:.0f}, 日 ¥{daily_cost:.2f}/{DEFAULT_DAILY_BUDGET_CNY:.0f}"


def _get_today_cost() -> dict:
    conn = _get_conn()
    row = conn.execute(
        """SELECT COALESCE(SUM(estimated_cost_cny),0) as cost_cny
           FROM cost_logs WHERE date(created_at) = date('now')"""
    ).fetchone()
    return dict(row) if row else {}


# ═══════════════════════════════════════════════════════════
# Cleanup / Close
# ═══════════════════════════════════════════════════════════

def close_db():
    global _conn
    with _lock:
        if _conn:
            _conn.close()
            _conn = None


# Auto-init on import (idempotent), but don't disrupt if DB not needed
try:
    init_db()
except Exception:
    pass

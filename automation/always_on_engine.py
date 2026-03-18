#!/usr/bin/env python3
"""
ROOMAN Always-On Background Automation Engine

Autonomous background engine for lead tracking, KPI collection,
and scheduled AI tasks.

Usage:
    python3 automation/always_on_engine.py init-db
    python3 automation/always_on_engine.py add-lead --name "..." --email "..." --source website --offer "..." --value 1999
    python3 automation/always_on_engine.py add-revenue --source stripe --type invoice_paid --amount 499
    python3 automation/always_on_engine.py run-once --task all --topic "cyber security" --niche "managed security" --geo AU
    python3 automation/always_on_engine.py run-daemon --timezone Australia/Brisbane --topic "cyber security" --niche "managed security" --geo AU
    python3 automation/always_on_engine.py kpi-today
"""

import argparse
import json
import os
import signal
import sqlite3
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    requests = None  # type: ignore

# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "automation" / "rooman_engine.db"
LOG_PATH = ROOT / "automation" / "engine.log"

# ─── Database ─────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS leads (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    email       TEXT    NOT NULL,
    source      TEXT    DEFAULT '',
    offer       TEXT    DEFAULT '',
    value       REAL    DEFAULT 0,
    status      TEXT    DEFAULT 'new',
    notes       TEXT    DEFAULT '',
    created_at  TEXT    NOT NULL,
    updated_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS revenue_events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source      TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,
    amount      REAL    NOT NULL,
    notes       TEXT    DEFAULT '',
    created_at  TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS kpi_snapshots (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT    NOT NULL UNIQUE,
    total_leads     INTEGER DEFAULT 0,
    new_leads       INTEGER DEFAULT 0,
    total_revenue   REAL    DEFAULT 0,
    daily_revenue   REAL    DEFAULT 0,
    tasks_run       INTEGER DEFAULT 0,
    snapshot_json   TEXT    DEFAULT '{}',
    created_at      TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS task_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    task        TEXT    NOT NULL,
    status      TEXT    NOT NULL,
    output      TEXT    DEFAULT '',
    error       TEXT    DEFAULT '',
    started_at  TEXT    NOT NULL,
    finished_at TEXT
);
"""


def get_connection() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(SCHEMA)
    print(f"[init-db] Database initialised at {DB_PATH}")


# ─── Logging ──────────────────────────────────────────────────────────────────

def log(msg: str) -> None:
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_PATH, "a") as f:
            f.write(line + "\n")
    except OSError:
        pass


# ─── Lead Management ──────────────────────────────────────────────────────────

def add_lead(name: str, email: str, source: str, offer: str, value: float) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO leads (name, email, source, offer, value, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, email, source, offer, value, now, now),
        )
    log(f"[add-lead] Added lead: {name} <{email}> source={source} offer='{offer}' value={value}")


# ─── Revenue Events ───────────────────────────────────────────────────────────

def add_revenue(source: str, event_type: str, amount: float, notes: str = "") -> None:
    now = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO revenue_events (source, event_type, amount, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (source, event_type, amount, notes, now),
        )
    log(f"[add-revenue] Recorded {event_type} from {source}: ${amount:.2f}")


# ─── KPI Snapshot ─────────────────────────────────────────────────────────────

def _build_kpi_snapshot(date_str: str) -> dict:
    with get_connection() as conn:
        total_leads = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        new_leads = conn.execute(
            "SELECT COUNT(*) FROM leads WHERE date(created_at) = ?", (date_str,)
        ).fetchone()[0]
        total_revenue = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM revenue_events").fetchone()[0]
        daily_revenue = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) FROM revenue_events WHERE date(created_at) = ?",
            (date_str,),
        ).fetchone()[0]
        tasks_run = conn.execute(
            "SELECT COUNT(*) FROM task_log WHERE date(started_at) = ? AND status = 'ok'",
            (date_str,),
        ).fetchone()[0]

    return {
        "date": date_str,
        "total_leads": total_leads,
        "new_leads": new_leads,
        "total_revenue": float(total_revenue),
        "daily_revenue": float(daily_revenue),
        "tasks_run": tasks_run,
    }


def kpi_today() -> None:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snap = _build_kpi_snapshot(date_str)
    with get_connection() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO kpi_snapshots "
            "(date, total_leads, new_leads, total_revenue, daily_revenue, tasks_run, snapshot_json, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                snap["date"],
                snap["total_leads"],
                snap["new_leads"],
                snap["total_revenue"],
                snap["daily_revenue"],
                snap["tasks_run"],
                json.dumps(snap),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    print(json.dumps(snap, indent=2))


# ─── AI Task Runner ───────────────────────────────────────────────────────────

def _get_deepseek_key() -> str:
    return os.environ.get("DEEPSEEK_API_KEY", "")


def _call_deepseek(prompt: str, max_tokens: int = 800) -> str:
    key = _get_deepseek_key()
    if not key:
        return "[no DEEPSEEK_API_KEY set — skipping AI call]"
    if requests is None:
        return "[requests library not installed — skipping AI call]"
    try:
        resp = requests.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7,
            },
            timeout=60,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        return f"[AI call failed: {exc}]"


def _run_task(name: str, prompt: str) -> str:
    started = datetime.now(timezone.utc).isoformat()
    log(f"[task] Starting: {name}")
    output = _call_deepseek(prompt)
    finished = datetime.now(timezone.utc).isoformat()
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO task_log (task, status, output, started_at, finished_at) VALUES (?, ?, ?, ?, ?)",
            (name, "ok", output[:4000], started, finished),
        )
    log(f"[task] Done: {name} ({len(output)} chars)")
    return output


# ─── Automation Tasks ─────────────────────────────────────────────────────────

def task_trend_brief(topic: str, niche: str, geo: str) -> str:
    prompt = (
        f"Write a short 3-bullet trend brief for '{topic}' in the '{niche}' niche, "
        f"targeting the {geo} market. Include one actionable insight for content or outreach this week."
    )
    return _run_task("trend_brief", prompt)


def task_lead_followup_drafts() -> str:
    with get_connection() as conn:
        leads = conn.execute(
            "SELECT name, offer FROM leads WHERE status = 'new' LIMIT 5"
        ).fetchall()
    if not leads:
        log("[task] No new leads to follow up on.")
        return "No new leads."
    names = ", ".join(f"{r['name']} ({r['offer']})" for r in leads)
    prompt = (
        f"Write one short, personalized follow-up email for each of these new leads: {names}. "
        "Keep each under 80 words. Focus on their offer and next step."
    )
    return _run_task("lead_followup_drafts", prompt)


def task_kpi_summary() -> str:
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snap = _build_kpi_snapshot(date_str)
    prompt = (
        f"Today's KPI snapshot: {json.dumps(snap)}. "
        "Write a 3-sentence operator summary: what's working, what's lagging, and one priority action."
    )
    return _run_task("kpi_summary", prompt)


TASK_REGISTRY = {
    "trend_brief": lambda ctx: task_trend_brief(ctx["topic"], ctx["niche"], ctx["geo"]),
    "lead_followup": lambda ctx: task_lead_followup_drafts(),
    "kpi_summary": lambda ctx: task_kpi_summary(),
}


def run_once(task: str, topic: str, niche: str, geo: str) -> None:
    ctx = {"topic": topic, "niche": niche, "geo": geo}
    if task == "all":
        for name, fn in TASK_REGISTRY.items():
            try:
                fn(ctx)
            except Exception as exc:
                log(f"[run-once] Task '{name}' failed: {exc}")
    elif task in TASK_REGISTRY:
        try:
            TASK_REGISTRY[task](ctx)
        except Exception as exc:
            log(f"[run-once] Task '{task}' failed: {exc}")
    else:
        print(f"Unknown task '{task}'. Available: {', '.join(TASK_REGISTRY)} or 'all'")
        sys.exit(1)


# ─── Daemon ───────────────────────────────────────────────────────────────────

_RUNNING = True


def _handle_signal(sig, frame):  # noqa: ARG001
    global _RUNNING
    log("[daemon] Shutdown signal received. Exiting…")
    _RUNNING = False


def _local_now(tz_name: str) -> datetime:
    """Return the current datetime in the given IANA timezone (falls back to UTC)."""
    try:
        from zoneinfo import ZoneInfo  # Python 3.9+
        return datetime.now(ZoneInfo(tz_name))
    except Exception:
        return datetime.now(timezone.utc)


def run_daemon(tz_name: str, topic: str, niche: str, geo: str) -> None:
    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    log(f"[daemon] Started. tz={tz_name} topic='{topic}' niche='{niche}' geo={geo}")

    # Track last run dates (keyed by local date in tz_name)
    last_run: dict[str, str] = {}
    INTERVAL_SECONDS = 3600  # check every hour

    while _RUNNING:
        now = _local_now(tz_name)
        today = now.strftime("%Y-%m-%d")
        hour = now.hour

        # Run trend brief once per day at 07:00 local time
        if hour == 7 and last_run.get("trend_brief") != today:
            try:
                task_trend_brief(topic, niche, geo)
                last_run["trend_brief"] = today
            except Exception as exc:
                log(f"[daemon] trend_brief error: {exc}")

        # Run lead follow-ups once per day at 09:00 local time
        if hour == 9 and last_run.get("lead_followup") != today:
            try:
                task_lead_followup_drafts()
                last_run["lead_followup"] = today
            except Exception as exc:
                log(f"[daemon] lead_followup error: {exc}")

        # Run KPI summary once per day at 17:00 local time
        if hour == 17 and last_run.get("kpi_summary") != today:
            try:
                task_kpi_summary()
                kpi_today()
                last_run["kpi_summary"] = today
            except Exception as exc:
                log(f"[daemon] kpi_summary error: {exc}")

        time.sleep(INTERVAL_SECONDS)

    log("[daemon] Stopped.")


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="always_on_engine",
        description="ROOMAN Always-On Background Automation Engine",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("init-db", help="Initialise the SQLite database")

    p_lead = sub.add_parser("add-lead", help="Add a new lead")
    p_lead.add_argument("--name", required=True)
    p_lead.add_argument("--email", required=True)
    p_lead.add_argument("--source", default="")
    p_lead.add_argument("--offer", default="")
    p_lead.add_argument("--value", type=float, default=0.0)

    p_rev = sub.add_parser("add-revenue", help="Record a revenue event")
    p_rev.add_argument("--source", required=True)
    p_rev.add_argument("--type", required=True, dest="event_type")
    p_rev.add_argument("--amount", type=float, required=True)
    p_rev.add_argument("--notes", default="")

    p_once = sub.add_parser("run-once", help="Run automation tasks once")
    p_once.add_argument("--task", default="all", help="Task name or 'all'")
    p_once.add_argument("--topic", default="business automation")
    p_once.add_argument("--niche", default="")
    p_once.add_argument("--geo", default="US")

    p_daemon = sub.add_parser("run-daemon", help="Start autonomous background daemon")
    p_daemon.add_argument("--timezone", default="UTC", dest="tz_name")
    p_daemon.add_argument("--topic", default="business automation")
    p_daemon.add_argument("--niche", default="")
    p_daemon.add_argument("--geo", default="US")

    sub.add_parser("kpi-today", help="Print today's KPI snapshot")

    args = parser.parse_args()

    if args.command == "init-db":
        init_db()
    elif args.command == "add-lead":
        add_lead(args.name, args.email, args.source, args.offer, args.value)
    elif args.command == "add-revenue":
        add_revenue(args.source, args.event_type, args.amount, args.notes)
    elif args.command == "run-once":
        run_once(args.task, args.topic, args.niche, args.geo)
    elif args.command == "run-daemon":
        run_daemon(args.tz_name, args.topic, args.niche, args.geo)
    elif args.command == "kpi-today":
        kpi_today()


if __name__ == "__main__":
    main()

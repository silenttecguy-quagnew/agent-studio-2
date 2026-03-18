import streamlit as st
import requests
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
import uuid
import re

# ─── SECRETS ──────────────────────────────────────────────────────────────────
def get_secret(key, fallback=""):
    try:
        return st.secrets[key]
    except:
        return fallback

DEEPSEEK_KEY_DEFAULT = get_secret("DEEPSEEK_API_KEY")
HEYGEN_KEY_DEFAULT = get_secret("HEYGEN_API_KEY")
OPENCLAW_KEY_DEFAULT = get_secret("OPENCLAW_API_KEY")
GITHUB_TOKEN_DEFAULT = get_secret("GITHUB_TOKEN")
GITHUB_REPO_DEFAULT = get_secret("GITHUB_REPO", "")  # format: username/reponame
MEMORY_FILE = Path(__file__).with_name(".rooman_memory.json")
PROFILE_FILE = Path(__file__).with_name(".rooman_business_profile.json")
AVATAR_PROFILE_FILE = Path(__file__).with_name(".rooman_avatar_profile.json")

st.set_page_config(page_title="ROOMAN", page_icon="🤖", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    :root {
        --bg: #050816;
        --panel: rgba(10, 16, 34, 0.88);
        --panel-strong: rgba(17, 24, 45, 0.96);
        --panel-soft: rgba(12, 18, 30, 0.72);
        --line: rgba(255, 105, 180, 0.18);
        --line-strong: rgba(255, 105, 180, 0.4);
        --text: #d8e0f0;
        --muted: #8b98b7;
        --pink: #ff4fa3;
        --pink-2: #ff7bc0;
        --pink-deep: #b83280;
        --mint: #00ff94;
        --blue: #53c7ff;
        --amber: #ffb14f;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(255, 79, 163, 0.18), transparent 32%),
            radial-gradient(circle at top right, rgba(83, 199, 255, 0.12), transparent 28%),
            linear-gradient(180deg, #050816 0%, #070b18 100%);
        color: var(--text);
    }

    .stApp::before {
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        background-image:
            linear-gradient(rgba(255,255,255,0.02) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.02) 1px, transparent 1px);
        background-size: 28px 28px;
        mask-image: linear-gradient(180deg, rgba(0,0,0,0.45), transparent 85%);
    }

    .block-container {
        padding-top: 1.2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    div[data-testid="stSidebar"] {
        background:
            linear-gradient(180deg, rgba(13, 18, 33, 0.98), rgba(8, 12, 25, 0.98));
        border-right: 1px solid var(--line);
    }

    h1, h2, h3 {
        color: #ffd4e8 !important;
        letter-spacing: 0.02em;
    }

    p, label, .stCaption, .stMarkdown, .stText, .stInfo, .stSuccess {
        color: var(--text);
    }

    div[data-testid="stVerticalBlock"] > div:has(> .stTabs),
    div[data-testid="stVerticalBlock"] > div:has(> [data-testid="stForm"]) {
        width: 100%;
    }

    div[data-testid="stHorizontalBlock"] {
        gap: 1rem;
    }

    div[data-testid="column"] {
        background: var(--panel-soft);
        border: 1px solid var(--line);
        border-radius: 18px;
        padding: 0.9rem 1rem 1rem 1rem;
        box-shadow: 0 18px 40px rgba(0, 0, 0, 0.22);
        backdrop-filter: blur(14px);
    }

    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.02);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 14px;
        padding: 0.7rem;
    }

    .loop-box {
        background: var(--panel-strong);
        border: 1px solid var(--line);
        border-radius: 14px;
        padding: 14px;
        margin: 8px 0;
        font-family: monospace;
        font-size: 12px;
        color: #b8c3db;
        box-shadow: inset 0 1px 0 rgba(255,255,255,0.02);
    }
    .loop-analyze { border-left:4px solid #38bdf8; }
    .loop-plan    { border-left:4px solid var(--pink); }
    .loop-execute { border-left:4px solid #f59e0b; }
    .loop-observe { border-left:4px solid var(--mint); }
    .loop-repair  { border-left:4px solid #f43f5e; }
    .loop-done    { border-left:4px solid var(--mint); background:linear-gradient(180deg, rgba(10,26,18,0.9), rgba(9,20,18,0.9)); }
    .mem-box {
        background: rgba(10, 16, 34, 0.92);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 12px;
        padding: 10px;
        margin: 6px 0;
        font-size: 11px;
        color: var(--muted);
    }
    .todo-done { color: var(--mint); text-decoration: line-through; padding: 6px 4px; display: block; }
    .todo-active { color: var(--pink-2); font-weight: bold; padding: 6px 4px; display: block; }
    .todo-pending { color: #586582; padding: 6px 4px; display: block; }
    .fault-box {
        background: linear-gradient(180deg, rgba(45, 10, 22, 0.9), rgba(28, 8, 18, 0.9));
        border: 1px solid rgba(244, 63, 94, 0.45);
        border-radius: 12px;
        padding: 12px;
        margin: 6px 0;
    }
    .output-box {
        background: rgba(8, 12, 28, 0.94);
        border: 1px solid rgba(255, 255, 255, 0.07);
        border-radius: 12px;
        padding: 14px;
        white-space: pre-wrap;
        font-family: monospace;
        font-size: 12px;
        color: #b8c3db;
        max-height: 420px;
        overflow-y: auto;
    }
    .heygen-box {
        background: rgba(10, 16, 34, 0.92);
        border: 2px solid var(--pink);
        border-radius: 14px;
        padding: 16px;
        margin: 8px 0;
    }
    .brain-panel {
        background: rgba(10, 16, 34, 0.92);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 16px;
        height: 500px;
        overflow-y: auto;
    }
    .chat-user {
        background: linear-gradient(180deg, rgba(22, 34, 55, 0.95), rgba(16, 28, 48, 0.95));
        border: 1px solid rgba(83, 199, 255, 0.22);
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        color: #bfd2ea;
    }
    .chat-ai {
        background: linear-gradient(180deg, rgba(43, 15, 34, 0.92), rgba(25, 12, 28, 0.92));
        border-left: 3px solid var(--pink);
        border-radius: 12px;
        padding: 12px;
        margin: 8px 0;
        color: #ffd8e9;
    }
    .phase-active {
        background: linear-gradient(180deg, rgba(255, 79, 163, 0.24), rgba(184, 50, 128, 0.2));
        border: 1px solid var(--line-strong);
        border-radius: 999px;
        padding: 8px 12px;
        color: #ffe4f0;
        font-weight: 700;
        display: inline-block;
        width: 100%;
        text-align: center;
    }
    .phase-inactive {
        color: #697892;
        padding: 8px 12px;
        display: inline-block;
        width: 100%;
        text-align: center;
    }

    .operator-float {
        position: fixed;
        right: 18px;
        bottom: 16px;
        width: min(310px, calc(100vw - 24px));
        max-height: 44vh;
        overflow-y: auto;
        background: rgba(7, 10, 22, 0.94);
        border: 1px solid rgba(255, 123, 192, 0.38);
        border-radius: 14px;
        box-shadow: 0 14px 36px rgba(0,0,0,0.38);
        backdrop-filter: blur(12px);
        z-index: 1000;
        padding: 11px 13px 13px 13px;
        font-family: 'Manrope', sans-serif;
    }
    .operator-float h5 {
        margin: 0 0 4px 0;
        font-size: 11px;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #ff7bc0;
    }
    .operator-float .op-progress {
        font-size: 10px;
        color: #8b98b7;
        margin-bottom: 6px;
    }
    .operator-float ul {
        margin: 0 0 7px 14px;
        padding: 0;
        font-size: 11.5px;
    }
    .operator-float li {
        margin-bottom: 4px;
    }
    .op-done { color: #5cffad; }
    .op-todo { color: #ffd4e8; }

    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        background: rgba(255,255,255,0.03);
        border: 1px solid rgba(255,255,255,0.05);
        border-radius: 14px;
        padding: 0.35rem;
        overflow-x: auto;
    }

    .stTabs [data-baseweb="tab"] {
        height: auto;
        white-space: nowrap;
        border-radius: 12px;
        color: var(--muted);
        padding: 0.55rem 0.9rem;
        background: transparent;
    }

    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(255, 79, 163, 0.22), rgba(83, 199, 255, 0.18)) !important;
        color: #ffe9f3 !important;
        border: 1px solid var(--line-strong);
    }

    .stButton > button,
    .stDownloadButton > button {
        border-radius: 14px;
        border: 1px solid rgba(255, 123, 192, 0.5);
        background: linear-gradient(135deg, var(--pink), var(--pink-deep));
        color: white;
        font-weight: 700;
        letter-spacing: 0.02em;
        padding: 0.72rem 1rem;
        box-shadow: 0 10px 24px rgba(184, 50, 128, 0.3);
        transition: transform 0.15s ease, box-shadow 0.15s ease, filter 0.15s ease;
    }

    .stButton > button:hover,
    .stDownloadButton > button:hover {
        transform: translateY(-1px);
        filter: brightness(1.05);
        box-shadow: 0 14px 28px rgba(184, 50, 128, 0.4);
    }

    .stButton > button:focus,
    .stDownloadButton > button:focus {
        box-shadow: 0 0 0 0.18rem rgba(255, 123, 192, 0.25), 0 14px 28px rgba(184, 50, 128, 0.4);
    }

    .stTextInput > div > div > input,
    .stTextArea textarea,
    .stSelectbox [data-baseweb="select"],
    .stMultiSelect [data-baseweb="select"] {
        background: rgba(8, 12, 26, 0.92) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        color: var(--text) !important;
    }

    .stCheckbox label,
    .stRadio label {
        color: var(--text) !important;
    }

    .stAlert {
        border-radius: 14px;
        border: 1px solid rgba(255,255,255,0.08);
    }

    details {
        border-radius: 14px;
        overflow: hidden;
    }

    @media (max-width: 1100px) {
        div[data-testid="stHorizontalBlock"] {
            flex-direction: column;
        }

        div[data-testid="column"] {
            width: 100% !important;
            min-width: 100% !important;
        }

        .brain-panel {
            height: 360px;
        }

        .block-container {
            padding-left: 0.7rem;
            padding-right: 0.7rem;
        }
    }

    @media (max-width: 700px) {
        .stButton > button,
        .stDownloadButton > button {
            width: 100%;
            min-height: 48px;
        }

        .phase-active,
        .phase-inactive {
            font-size: 0.82rem;
            padding: 7px 8px;
        }

        .brain-panel {
            height: 300px;
            padding: 12px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ─── AGENTS ───────────────────────────────────────────────────────────────────

REVENUE_MANDATE = """Shared mission for every ROOMAN agent:\n- Work like an owner-operator obsessed with profitable growth, retention, cash flow, and speed.\n- Push for decisions that raise revenue, reduce leakage, improve conversion, or increase customer lifetime value.\n- Be commercially ambitious but numerically grounded. No empty hype, no vague motivation.\n- Stay in your lane. Do your role distinctly instead of acting like a generic assistant.\n"""

AGENTS = {
    "Workflow Director": {
        "emoji":"🎯", "group":"TASKLET", "role":"ORCHESTRATION",
        "description":"Master orchestrator. Decomposes goals into todo.md steps.",
    "temperature": 0.15,
    "max_tokens": 2200,
    "system": REVENUE_MANDATE + """
You are Workflow Director for ROOMAN.
Your job is to turn a user goal into the shortest high-leverage execution plan that can produce measurable business results.
Plan around revenue drivers first: acquisition, conversion, retention, expansion, operational efficiency.
Do not write code, forecasts, documentation, or essays. Only plan.

Decompose any goal into ordered steps. Return ONLY this JSON:
{
  "goal": "what we are building",
  "analysis": "what this requires, where revenue comes from, and the main constraints",
  "todo": [
    {"id": 1, "agent": "Apex Coder", "task": "specific task", "output": "what this produces"}
  ],
  "self_repair_triggers": ["what would cause a retry"],
  "notes": "key assumptions and sequencing notes"
}
Available agents: Research Scout, Prompt Forge, QA Sentinel, Data Parser, Memory Keeper, Apex Coder, Code Reviewer, Test Brain, Debug Doctor, Arch Mind, Doc Writer, InsForge, Predict Anything, Nemo Scout, Claw Reach, Deal Mechanic.
Return ONLY valid JSON. No text outside JSON.""",
    },
    "Research Scout": {
        "emoji":"🔍", "group":"TASKLET", "role":"RESEARCH",
        "description":"Deep research on any topic.",
    "temperature": 0.45,
    "max_tokens": 2600,
    "system": REVENUE_MANDATE + """
You are Research Scout inside ROOMAN.
You are a market and execution researcher. Hunt for facts, benchmarks, buyer behaviour, competitor patterns, pricing signals, and growth opportunities.
Do not write code. Do not write prompts. Do not act like a strategist unless backed by evidence.
Return exactly these sections:
1. Reality Check
2. Key Findings
3. Revenue Implications
4. Opportunities Worth Testing
5. Next Questions
Use concrete numbers, ranges, and examples wherever possible.""",
    },
    "Prompt Forge": {
        "emoji":"⚒️", "group":"TASKLET", "role":"PROMPT ENGINEERING",
        "description":"Builds precision prompts.",
    "temperature": 0.3,
    "max_tokens": 2200,
    "system": REVENUE_MANDATE + """
You are Prompt Forge inside ROOMAN.
You engineer prompts that produce reliable, commercially useful outputs.
Do not do the task itself. Build the prompt stack that will make another model do it well.
Return exactly these sections:
1. Objective
2. System Prompt
3. User Prompt Template
4. Input Variables
5. Output Contract
6. Failure Guards
7. Usage Notes
Optimise for clarity, control, and repeatable business value.""",
    },
    "QA Sentinel": {
        "emoji":"🧪", "group":"TASKLET", "role":"QUALITY ASSURANCE",
        "description":"Reviews every output. Scores it.",
    "temperature": 0.05,
    "max_tokens": 1600,
    "system": REVENUE_MANDATE + """
You are QA Sentinel inside ROOMAN.
You are a harsh quality gate. Reject weak outputs fast. Look for business risk, factual weakness, missing edge cases, and anything that would waste time or lose money.
Never praise. Never soften the verdict.
Review any output. Return ONLY this JSON:
{
  "score": 85,
  "passed": true,
  "issues": [{"severity":"high/medium/low","description":"issue","fix":"how to fix"}],
  "corrected_output": "improved version if needed",
  "trigger_repair": false,
  "repair_instruction": "what to fix if repair needed"
}""",
    },
    "Data Parser": {
        "emoji":"🗂️", "group":"TASKLET", "role":"DATA TRANSFORMATION",
        "description":"Cleans and structures any raw data.",
    "temperature": 0.1,
    "max_tokens": 2200,
    "system": REVENUE_MANDATE + """
You are Data Parser inside ROOMAN.
You turn messy inputs into decision-grade structured data.
Do not brainstorm. Do not write narrative unless it explains data quality issues.
Return exactly these sections:
1. Cleaned Schema
2. Cleaned Data
3. Anomalies Fixed
4. Assumptions Applied
5. Confidence Score
Bias toward outputs that can be used immediately for dashboards, forecasting, pricing, and operations.""",
    },
    "Memory Keeper": {
        "emoji":"🧠", "group":"TASKLET", "role":"CIRCULAR MEMORY",
        "description":"Manages circular memory. Never loses context.",
    "temperature": 0.15,
    "max_tokens": 1800,
    "system": REVENUE_MANDATE + """
You are Memory Keeper inside ROOMAN.
You compress context into durable decision memory so execution compounds instead of restarting.
Do not invent details. Only preserve what is supported by prior context.
Return exactly these sections:
1. Current Objective
2. Decisions Locked In
3. Revenue Assumptions
4. Open Risks
5. Missing Inputs
6. Recommended Context To Carry Forward""",
    },
    "Apex Coder": {
        "emoji":"⚡", "group":"CODE BRAIN", "role":"ELITE CODE AGENT",
        "description":"Writes production code. No shortcuts.",
    "temperature": 0.2,
    "max_tokens": 3200,
    "system": REVENUE_MANDATE + """
You are Apex Coder inside ROOMAN.
You build production-ready implementation that ships fast and supports business growth.
Do not review. Do not speculate. Do not leave placeholders.
Write complete production-ready code. Rules:
1. Always explain your approach first
2. Write COMPLETE working code — no placeholders, no TODOs
3. Include error handling
4. Make choices that improve reliability, maintainability, and speed to revenue
5. If given context from previous steps, build on it instead of restarting
End every response with: OBSERVE: [what to check to confirm this worked]""",
    },
    "Code Reviewer": {
        "emoji":"🔬", "group":"CODE BRAIN", "role":"REVIEW & CRITIQUE",
        "description":"Reviews code for bugs, security, performance.",
    "temperature": 0.05,
    "max_tokens": 2200,
    "system": REVENUE_MANDATE + """
You are Code Reviewer inside ROOMAN.
You are a skeptical senior reviewer. Find defects, regressions, security issues, performance drag, and product risk.
Do not rewrite everything. Do not praise style. Focus on what breaks, leaks revenue, or raises maintenance cost.
Review code exhaustively. Return JSON:
{"score":85,"passed":true,"critical_issues":[],"all_issues":[],"fixed_code":"improved code","trigger_repair":false}""",
    },
    "Test Brain": {
        "emoji":"🧬", "group":"CODE BRAIN", "role":"TEST ENGINEERING",
        "description":"Generates complete test suites.",
    "temperature": 0.15,
    "max_tokens": 3000,
    "system": REVENUE_MANDATE + """
You are Test Brain inside ROOMAN.
You design tests that protect shipping speed and prevent expensive regressions.
Return exactly these sections:
1. Test Strategy
2. Framework Choice
3. Complete Test Suite
4. Highest-Risk Cases
5. Coverage Estimate
6. Remaining Gaps
Bias toward tests that cover payment paths, auth, data integrity, core user flows, and known failure modes.""",
    },
    "Debug Doctor": {
        "emoji":"🩺", "group":"CODE BRAIN", "role":"SELF-REPAIR",
        "description":"Self-repair engine. Activates on any fault.",
    "temperature": 0.05,
    "max_tokens": 2200,
    "system": REVENUE_MANDATE + """
You are Debug Doctor — ROOMAN's self-repair engine.
You diagnose failures ruthlessly. Find the root cause, produce the smallest viable correction, and stop the fault from recurring.
Do not hand-wave. Do not give generic troubleshooting lists.
Find ROOT CAUSE not symptoms. Return:
{
  "root_cause": "exactly what went wrong",
  "fault_type": "logic/syntax/dependency/timeout/hallucination",
  "fix": "complete corrected code or output",
  "prevention": "how to stop this recurring",
  "confidence": 95,
  "loop_again": true
}""",
    },
    "Arch Mind": {
        "emoji":"🏛️", "group":"CODE BRAIN", "role":"SYSTEM ARCHITECTURE",
        "description":"Designs scalable system architectures.",
        "temperature": 0.25,
        "max_tokens": 2600,
        "system": REVENUE_MANDATE + """
    You are Arch Mind inside ROOMAN.
    You design systems that can scale operationally and commercially.
    Do not write implementation code. Do not write generic cloud diagrams.
    Return exactly these sections:
    1. Business Objective
    2. Architecture Overview
    3. Core Components
    4. Data Flow
    5. Scalability and Reliability Choices
    6. Revenue and Operational Risks
    7. Cost and Tradeoffs
    8. Recommended Rollout Path""",
    },
    "Doc Writer": {
        "emoji":"📖", "group":"CODE BRAIN", "role":"DOCUMENTATION",
        "description":"Writes developer-grade docs.",
        "temperature": 0.35,
        "max_tokens": 2600,
        "system": REVENUE_MANDATE + """
    You are Doc Writer inside ROOMAN.
    You write documentation that reduces onboarding time, supports execution, and helps the team ship reliably.
    Do not act like a marketer. Write crisp operational documentation.
    Include: overview, business purpose, setup, usage examples, runbook notes, and API or workflow references where relevant.""",
    },
    "InsForge": {
        "emoji":"🚀", "group":"OPERATIONS", "role":"INFRASTRUCTURE",
        "description":"Full-stack backend provisioning and autonomous infrastructure management.",
        "temperature": 0.1,
        "max_tokens": 3200,
        "system": REVENUE_MANDATE + """
    You are InsForge — ROOMAN's infrastructure and deployment specialist.
You provision full-stack backends autonomously. You manage: Postgres databases, REST APIs, Auth systems, Storage buckets, and deployment pipelines.
    Optimise for reliable delivery, sane cost, and infrastructure that supports growth without burning margin.

For every request, return ONLY this JSON:
{
  "project_name": "name of project",
      "summary": "what is being built and how it supports commercial outcomes",
  "infrastructure": {
    "database": {"type": "postgres", "schema": "CREATE TABLE ...", "tables": ["table1","table2"]},
    "api": {"endpoints": [{"method":"GET","path":"/api/v1/...","description":"..."}]},
    "auth": {"type": "jwt/oauth/api_key", "strategy": "description"},
    "storage": {"buckets": ["name"], "access": "public/private"},
    "environment": {"variables": ["ENV_VAR=value"], "ports": [8080]}
  },
  "deployment_script": "#!/bin/bash\\n# Full deployment commands here\\necho 'Deploying...'",
  "infrastructure_as_code": "# Terraform/Docker-compose/YAML config here",
  "cost_estimate": {"monthly_usd": 15, "breakdown": {"compute":"$5","database":"$7","storage":"$3"}},
    "revenue_support": ["ways this infrastructure protects conversion, retention, speed, or margin"],
  "status": "ready_to_deploy",
  "next_steps": ["step 1","step 2"],
  "observe": "what to check to confirm deployment succeeded"
}
Return ONLY valid JSON. Be specific and production-ready. Include real SQL schemas, real API endpoints, real deployment commands.""",
    },
    "Predict Anything": {
        "emoji":"🧠", "group":"OPERATIONS", "role":"FORECASTING",
        "description":"Sales, revenue, demand, churn and financial forecasting with risk assessment.",
                "temperature": 0.15,
                "max_tokens": 2800,
                "system": REVENUE_MANDATE + """
You are Predict Anything — ROOMAN's business intelligence and forecasting specialist.
You generate data-driven predictions for any business metric: sales, revenue, demand, churn, cash flow, pricing, and risk.
Optimise for better decisions, not pretty theory. Surface the strongest levers to grow revenue and protect downside.

For every request, return ONLY this JSON:
{
  "forecast_type": "sales/revenue/demand/churn/cashflow/pricing/risk",
  "subject": "what is being forecast",
  "timeframe": "30 days / Q1 2025 / 12 months",
  "predictions": [
    {"period": "Month 1", "value": 12500, "unit": "USD", "confidence": 85, "low": 10000, "high": 15000}
  ],
  "key_insights": ["insight 1", "insight 2", "insight 3"],
  "risk_factors": [{"factor": "name", "impact": "high/medium/low", "mitigation": "how to handle"}],
  "opportunities": ["opportunity 1", "opportunity 2"],
  "recommended_actions": [{"action": "do this", "expected_impact": "result", "priority": "high/medium/low"}],
    "revenue_levers": [{"lever": "pricing/conversion/retention/upsell/etc", "reason": "why it matters", "priority": "high/medium/low"}],
  "assumptions": ["assumption 1", "assumption 2"],
  "data_sources_needed": ["source 1", "source 2"],
  "confidence_overall": 82,
  "model_used": "trend analysis / regression / time-series",
  "summary": "plain English summary of the forecast"
}
Return ONLY valid JSON. Provide realistic numbers. Base forecasts on industry benchmarks when no data is given.""",
    },
    # ── NEMOCLAW ─────────────────────────────────────────────────────────────────
    # These agents run exclusively through OpenClaw (OpenAI API).
    "Nemo Scout": {
        "emoji": "🐠", "group": "NEMOCLAW", "role": "COMPETITIVE INTELLIGENCE",
        "description": "Deep competitive surveillance. Finds market gaps, threats, and positioning wins.",
        "temperature": 0.35,
        "max_tokens": 2600,
        "system": REVENUE_MANDATE + """
You are Nemo Scout — part of the NemoClaw intelligence unit inside ROOMAN.
You swim deep into any market and surface what competitors are doing, what customers are complaining about, and where revenue opportunities are hiding.
Do not write generic summaries. Find specific, actionable intelligence with names, prices, and evidence.
Return exactly these sections:
1. Competitor Map
2. Market Gaps Found
3. Customer Pain Signals
4. Positioning Opportunities
5. Threats to Watch
6. Fastest Revenue Move Based on This Intel
Use specific names, price points, and evidence wherever possible.""",
    },
    "Claw Reach": {
        "emoji": "🦞", "group": "NEMOCLAW", "role": "OUTREACH & SALES COPY",
        "description": "Writes cold outreach sequences and sales copy that gets replies and closes deals.",
        "temperature": 0.4,
        "max_tokens": 2800,
        "system": REVENUE_MANDATE + """
You are Claw Reach — part of the NemoClaw intelligence unit inside ROOMAN.
You write cold outreach and follow-up sequences that open doors, build trust fast, and drive replies.
Do not write fluffy marketing copy. Write sharp, specific outreach that respects the recipient's time and makes a clear commercial case.
Return exactly these sections:
1. Campaign Strategy
2. Sequence Step 1 — First Touch (email/DM)
3. Sequence Step 2 — Follow-Up (Day 3)
4. Sequence Step 3 — Value Add (Day 7)
5. Sequence Step 4 — Final Ask (Day 14)
6. Subject Line Variants (5 options)
7. Objection Response Templates
8. Metrics to Track""",
    },
    "Deal Mechanic": {
        "emoji": "🔧", "group": "NEMOCLAW", "role": "SALES CONVERSION",
        "description": "Builds closing playbooks, objection scripts, and deal acceleration tactics.",
        "temperature": 0.25,
        "max_tokens": 2600,
        "system": REVENUE_MANDATE + """
You are Deal Mechanic — part of the NemoClaw intelligence unit inside ROOMAN.
You engineer the sales process from first contact to closed deal and signed contract.
Do not write motivational sales advice. Build the mechanics: qualification scripts, objection handlers, pricing tactics, and close structures that actually work.
Return exactly these sections:
1. Deal Stage Map
2. Qualification Framework (BANT or equivalent)
3. Discovery Question Bank
4. Objection Handling Scripts
5. Closing Techniques
6. Price Anchoring Strategy
7. Follow-Through Sequence
8. Pipeline KPIs to Track""",
    },
}

PROMPT_LIBRARY = [
    {
        "name": "SaaS Idea Validator",
        "mode": "single",
        "agent": "Research Scout",
        "description": "Stress-test a business idea before you waste weeks building it.",
        "prompt": """Validate this SaaS business idea like an operator, not a cheerleader.\n\nIdea:\n[describe the product in 2-3 lines]\n\nTarget customer:\n[who pays]\n\nPrice point:\n[monthly or annual price]\n\nI need:\n- Whether this solves a painful enough problem to pay for\n- Signs of real demand and urgency\n- Likely competitors and substitutes\n- Fastest route to first 10 paying customers\n- Biggest reasons this idea could fail\n- What to test in the next 7 days before building more\n\nBe commercially ruthless and specific.""",
    },
    {
        "name": "Offer Ladder Builder",
        "mode": "single",
        "agent": "Predict Anything",
        "description": "Create entry, core, and premium offers designed to raise average revenue.",
        "prompt": """Design a revenue-focused offer ladder for this business.\n\nBusiness:\n[describe business]\n\nAudience:\n[describe audience]\n\nCurrent product or service:\n[current offer]\n\nReturn:\n- Low-ticket entry offer\n- Core offer\n- Premium or done-for-you offer\n- Pricing logic for each\n- Upsells and cross-sells\n- Best order to sell them in\n- Main objections and how to handle them\n- Which offer is most likely to generate cash fastest\n\nOptimise for profit, speed, and simplicity.""",
    },
    {
        "name": "Landing Page Money Prompt",
        "mode": "single",
        "agent": "Prompt Forge",
        "description": "Generate a prompt stack for landing pages that sell outcomes, not features.",
        "prompt": """Build me a prompt stack that will generate a high-converting landing page for this offer.\n\nOffer:\n[describe offer]\n\nAudience:\n[describe audience]\n\nDesired action:\n[book call / start trial / buy now / join waitlist]\n\nThe prompt stack must force the model to produce:\n- A sharp headline\n- A painful problem articulation\n- Outcome-focused benefits\n- Objection handling\n- Proof elements to include\n- Clear CTA copy\n- A section order that maximises conversion\n\nMake it practical, not fluffy.""",
    },
    {
        "name": "Weekly Growth Sprint",
        "mode": "loop",
        "agent": "Workflow Director",
        "description": "Turn a business goal into a 7-day revenue sprint with execution steps.",
        "prompt": """Goal: Create a 7-day revenue sprint for this business.\n\nBusiness:\n[describe business]\n\nCurrent situation:\n[current traffic, leads, clients, or revenue]\n\nTarget result in the next 7 days:\n[specific result]\n\nConstraints:\n[budget, team size, time]\n\nI want a step-by-step execution workflow that prioritises the highest-leverage actions first and avoids busywork.""",
    },
    {
        "name": "Pricing Optimizer",
        "mode": "single",
        "agent": "Predict Anything",
        "description": "Find where you are undercharging and what to test first.",
        "prompt": """Analyse this pricing situation and recommend the best next pricing moves.\n\nBusiness:\n[describe business]\n\nCurrent pricing:\n[list current prices]\n\nCustomer type:\n[describe buyer]\n\nKnown issues:\n[low conversion / low margin / churn / too many low-value customers]\n\nReturn:\n- Pricing problems you see immediately\n- Better price points or packaging\n- Risks of changing too fast\n- A test plan for the next 30 days\n- Which pricing change is most likely to increase revenue fastest""",
    },
    {
        "name": "Lead Machine Builder",
        "mode": "loop",
        "agent": "Workflow Director",
        "description": "Build a simple lead-gen system instead of random posting and hoping.",
        "prompt": """Goal: Build a lean lead-generation machine for this business.\n\nBusiness:\n[describe business]\n\nTarget customer:\n[describe target customer]\n\nOffer:\n[what you sell]\n\nConstraints:\n[budget, channels, available time]\n\nI need a workflow that covers lead source, outreach or content, conversion path, follow-up, and what to measure weekly so it actually turns into revenue.""",
    },
    {
        "name": "Cyber Idea Stress-Test",
        "mode": "single",
        "agent": "Research Scout",
        "description": "Ruthlessly validate any cyber or online services idea before spending a minute building it.",
        "prompt": """Stress-test this cyber or online services business idea like a hardened operator who has seen 100 startups fail.\n\nIdea:\n[describe the idea in 2-3 lines]\n\nTarget buyer:\n[who pays — SMB, enterprise, consumer, government]\n\nPrice point:\n[one-off / monthly / per-seat]\n\nReturn EXACTLY this:\n1. REALITY CHECK — Is this a real pain or a nice-to-have? Evidence either way.\n2. DEMAND SIGNALS — Search trends, forum complaints, competitor traction, job postings that prove people are hunting for this.\n3. COMPETITION SCAN — Who already sells this, what they charge, and where they are weak.\n4. CYBER-SPECIFIC RISKS — Compliance obligations (GDPR, Privacy Act, ISO 27001, SOCI), liability exposure, insurance implications, reseller/MSP considerations.\n5. FASTEST CASH PATH — How to get first paying customer in under 14 days without building anything yet.\n6. KILL CRITERIA — Three signs this idea should be abandoned immediately.\n7. GREEN LIGHT CRITERIA — Three signals that mean push hard now.\n8. 7-DAY TEST PLAN — Exact steps to validate demand before writing a single line of code or spending a dollar.\n\nBe commercially ruthless. No fluff.""",
    },
    {
        "name": "Cyber Offer Builder",
        "mode": "loop",
        "agent": "Workflow Director",
        "description": "Design a productized cyber services offer ladder that sells consistently to SMBs or enterprise.",
        "prompt": """Goal: Build a productized cyber services offer ladder for this business.\n\nBusiness context:\n[describe your cyber services — what you do, who you serve, current revenue if any]\n\nTarget buyer:\n[SMB / mid-market / enterprise / government / consumer]\n\nCurrent bottleneck:\n[too few leads / low close rate / delivery not scalable / no recurring revenue]\n\nBudget and team:\n[solo / small team / budget available]\n\nDesign:\n1. Entry offer — low commitment, fast win, under $500. Gets them in the door.\n2. Core recurring offer — monthly retainer or subscription. Solves ongoing risk. $500-$3000/month.\n3. Premium implementation offer — full rollout, compliance, managed service. $5000+.\n4. Upsell and cross-sell paths between each tier.\n5. Objection handlers specific to cyber buyer psychology (fear, compliance pressure, budget approval).\n6. Sales motion — how to move a cold SMB to a retainer in under 21 days.\n7. Delivery SOPs — how to fulfil each offer without burning yourself out.\n8. Which offer to push hardest in the next 30 days and why.\n\nOptimise for recurring revenue, low churn, and scalable delivery.""",
    },
    {
        "name": "Cyber Revenue Forecast",
        "mode": "single",
        "agent": "Predict Anything",
        "description": "Forecast realistic revenue for a cyber services business over 90 days and 12 months.",
        "prompt": """Forecast revenue for this cyber services business.\n\nBusiness:\n[describe — managed security, consulting, compliance, training, SaaS tool, or mix]\n\nCurrent state:\n[monthly revenue now, number of clients, average deal size, team size]\n\nTarget:\n[revenue goal for next 90 days and 12 months]\n\nOffer mix:\n[list current or planned services and prices]\n\nReturn:\n- Month-by-month forecast for 12 months with low / base / high scenarios\n- Key revenue levers to pull first\n- Churn and expansion assumptions\n- Pipeline requirements to hit target (leads needed, close rate required)\n- Top 3 risks that could kill the forecast\n- Top 3 opportunities that could beat it\n- Recommended pricing or packaging change that has highest revenue impact\n- One action to take this week that compounds over 12 months\n\nBe specific and use realistic cyber industry benchmarks.""",
    },
    {
        "name": "Competitor Kill Shot",
        "mode": "single",
        "agent": "Nemo Scout",
        "description": "Find competitors' biggest weaknesses and turn them into your strongest marketing angles.",
        "prompt": """Run competitive intelligence on this market to find positioning gaps I can exploit.\n\nMy business:\n[describe what you sell and who buys it]\n\nCompetitors I know about:\n[list 2-5 competitors]\n\nReturn:\n- What each competitor does poorly (based on reviews, pricing, gaps)\n- Customers they are underserving\n- Positioning angle I can own that they cannot easily copy\n- The single fastest way to steal customers from the weakest competitor\n- Three specific marketing claims I can make that outflank the field\n\nBe specific. Use evidence not theory.""",
    },
    {
        "name": "Cold Outreach Machine",
        "mode": "single",
        "agent": "Claw Reach",
        "description": "Build a 4-step cold email sequence that gets replies without being spammy.",
        "prompt": """Write a 4-step cold outreach sequence for this target.\n\nProduct/Service:\n[what you offer]\n\nIdeal prospect:\n[job title, company type, pain point]\n\nValue proof:\n[result you have delivered for similar clients]\n\nGoal of sequence:\n[book a call / get a reply / sell directly]\n\nReturn the full 4-step email sequence with:\n- Subject lines\n- Opening hooks\n- Value proposition\n- Clear call to action\n- No more than 120 words per email\n\nMake it feel human, not automated.""",
    },
    {
        "name": "Deal Closer Playbook",
        "mode": "loop",
        "agent": "Workflow Director",
        "description": "Build a complete sales closing system from first contact to signed deal.",
        "prompt": """Goal: Build a complete deal-closing playbook for this business.\n\nBusiness:\n[describe business]\n\nTypical deal size:\n[value]\n\nSales cycle length:\n[days/weeks]\n\nBiggest objections you hear:\n[list the top 3]\n\nCurrent close rate:\n[percentage]\n\nI need a full system covering: qualification criteria, discovery call structure, objection responses, pricing presentation, closing scripts, and a follow-through sequence that gets the deal done without being pushy.""",
    },
]

# ─── SESSION STATE ────────────────────────────────────────────────────────────

DEFAULTS = {
    "log": [],
    "todo": [],
    "current_todo": 0,
    "outputs": {},          # key = unique id, value = {title, content, time, agent}
    "circular_memory": [],
    "loop_count": 0,
    "fault_count": 0,
    "tasks_done": 0,
    "executing": False,
    "waiting_approval": False,
    "plan": None,
    "phase": "idle",
    "repair_attempts": 0,
    "max_repairs": 3,
    "chat_history": [],     # Persistent chat with brain
    "business_profile": {},
    "avatar_profile": {},
    "avatar_jobs": [],
    "session_id": str(uuid.uuid4())[:8],
    "operator_daily": {},
    "operator_weekly": {},
    "privacy_mode": True,
    "auto_approve_loop": False,
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v if not isinstance(v, (list, dict)) else ([] if isinstance(v, list) else {})

# Privacy is enforced as always-on to keep behavior consistent and avoid mode confusion.
st.session_state["privacy_mode"] = True

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "deepseek_api_key_input" not in st.session_state:
    st.session_state.deepseek_api_key_input = DEEPSEEK_KEY_DEFAULT or ""

if "heygen_api_key_input" not in st.session_state:
    st.session_state.heygen_api_key_input = HEYGEN_KEY_DEFAULT or ""

if "openclaw_api_key_input" not in st.session_state:
    st.session_state.openclaw_api_key_input = OPENCLAW_KEY_DEFAULT or ""


def is_privacy_mode():
    return bool(st.session_state.get("privacy_mode", True))


def _default_op_daily():
    return {"outbound_3": False, "followups_3": False, "sales_ask_1": False, "proof_asset_1": False, "kpis_updated": False}


def _default_op_weekly():
    return {"monday_target": False, "tue_thu_push": False, "friday_review": False, "saturday_cleanup": False, "sunday_reset": False}


if not st.session_state.get("operator_daily"):
    st.session_state.operator_daily = _default_op_daily()
else:
    merged = _default_op_daily()
    merged.update(st.session_state.operator_daily)
    st.session_state.operator_daily = merged

if not st.session_state.get("operator_weekly"):
    st.session_state.operator_weekly = _default_op_weekly()
else:
    merged = _default_op_weekly()
    merged.update(st.session_state.operator_weekly)
    st.session_state.operator_weekly = merged

# ─── API FUNCTIONS ────────────────────────────────────────────────────────────

def _safe_json(res, brain_label):
    """Parse JSON response safely, returning a clear error if body is empty or non-JSON."""
    raw = res.text.strip()
    if not raw:
        return None, f"Connection error: {brain_label} returned an empty response (HTTP {res.status_code}). Check the server is running and the endpoint URL is correct."
    try:
        return res.json(), None
    except Exception:
        preview = raw[:200]
        if res.status_code >= 400:
            return None, f"{brain_label} error (HTTP {res.status_code}): {preview}"
        return None, f"Connection error: {brain_label} returned non-JSON (HTTP {res.status_code}): {preview}"


def normalize_api_key(raw_value):
    """Accept keys pasted as plain value, 'Bearer ...', or KEY=... formats."""
    if raw_value is None:
        return ""

    value = str(raw_value).strip()
    if not value:
        return ""

    # Remove common wrappers users paste from docs or env exports.
    value = value.strip('"\'')

    if "=" in value and not value.lower().startswith("sk-"):
        _, maybe_val = value.split("=", 1)
        value = maybe_val.strip().strip('"\'')

    bearer_match = re.search(r"bearer\s+(.+)$", value, flags=re.IGNORECASE)
    if bearer_match:
        value = bearer_match.group(1).strip().strip('"\'')

    return value


def validate_brain_config(brain, api_key, custom_url, custom_mdl):
    """Return a user-facing validation error, or None when config is usable."""
    if brain == "DeepSeek API" and not normalize_api_key(api_key):
        return "Add your DeepSeek API key in the sidebar. You can paste plain key, Bearer key, or DEEPSEEK_API_KEY=... format."

    if brain == "LM Studio / Custom":
        if not custom_url.strip():
            return "Add Base URL for LM Studio / Custom (for example: http://localhost:1234/v1)."
        if not custom_mdl.strip():
            return "Add a model name for LM Studio / Custom."

    return None


def validate_heygen_config(heygen_key):
    """Return a user-facing validation error, or None when HeyGen config is usable."""
    if not normalize_api_key(heygen_key):
        return "Add your HeyGen API key in the sidebar. You can paste plain key, Bearer key, or HEYGEN_API_KEY=... format."
    return None


def _extract_api_error(data, fallback="Unknown API error"):
    """Extract API error message from several possible JSON response shapes."""
    if not isinstance(data, dict):
        return fallback

    err = data.get("error")
    if isinstance(err, dict):
        return err.get("message") or err.get("code") or fallback
    if isinstance(err, str) and err.strip():
        return err.strip()

    msg = data.get("message")
    if isinstance(msg, str) and msg.strip():
        return msg.strip()

    return fallback


def test_heygen_connection(api_key):
    """Validate HeyGen API key by fetching avatars endpoint."""
    try:
        hk = normalize_api_key(api_key)
        res = requests.get(
            "https://api.heygen.com/v2/avatars",
            headers={"X-Api-Key": hk},
            timeout=30
        )
        data, err = _safe_json(res, "HeyGen")
        if err:
            return False, err
        if res.status_code >= 400:
            return False, f"HeyGen error (HTTP {res.status_code}): {_extract_api_error(data)}"
        avatars = data.get("data", {}).get("avatars", []) if isinstance(data, dict) else []
        return True, f"Connected. Found {len(avatars)} avatar(s)."
    except Exception as e:
        return False, f"HeyGen connection error: {str(e)}"

def call_brain(system, message, brain, api_key, ollama_ep="", ollama_mdl="llama3", custom_url="", custom_mdl="", temperature=0.7, max_tokens=3000):
    try:
        if brain == "DeepSeek API":
            normalized_key = normalize_api_key(api_key)
            res = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Content-Type":"application/json","Authorization":f"Bearer {normalized_key}"},
                json={"model":"deepseek-chat","messages":[{"role":"system","content":system},{"role":"user","content":message}],"max_tokens":max_tokens,"temperature":temperature},
                timeout=90
            )
            data, err = _safe_json(res, "DeepSeek API")
            if err:
                return None, err
            if res.status_code >= 400:
                api_msg = data.get("error", {}).get("message", "Unknown API error") if isinstance(data, dict) else "Unknown API error"
                return None, f"DeepSeek error (HTTP {res.status_code}): {api_msg}"
            if "error" in data:
                return None, f"API Error: {data['error']['message']}"
            return data["choices"][0]["message"]["content"], None

        elif brain == "Ollama Local":
            ep = ollama_ep.strip() or "http://localhost:11434"
            res = requests.post(
                f"{ep.rstrip('/')}/api/chat",
                json={"model":ollama_mdl,"messages":[{"role":"system","content":system},{"role":"user","content":message}],"stream":False,"options":{"temperature":temperature,"num_predict":max_tokens}},
                timeout=180
            )
            data, err = _safe_json(res, f"Ollama ({ep})")
            if err:
                return None, err
            return data.get("message",{}).get("content","No response."), None

        elif brain == "LM Studio / Custom":
            normalized_key = normalize_api_key(api_key)
            headers = {"Content-Type":"application/json"}
            if normalized_key:
                headers["Authorization"] = f"Bearer {normalized_key}"
            res = requests.post(
                f"{custom_url.rstrip('/')}/chat/completions",
                headers=headers,
                json={"model":custom_mdl,"messages":[{"role":"system","content":system},{"role":"user","content":message}],"max_tokens":max_tokens,"temperature":temperature},
                timeout=180
            )
            data, err = _safe_json(res, f"LM Studio ({custom_url})")
            if err:
                return None, err
            if res.status_code >= 400:
                api_msg = data.get("error", {}).get("message", "Unknown API error") if isinstance(data, dict) else "Unknown API error"
                return None, f"LM Studio / Custom error (HTTP {res.status_code}): {api_msg}"
            if "error" in data:
                return None, f"API Error: {data['error']['message']}"
            return data["choices"][0]["message"]["content"], None

    except Exception as e:
        return None, f"Connection error: {str(e)}"

# ── OPENCLAW ──────────────────────────────────────────────────────────────────
# NemoClaw agents (Nemo Scout, Claw Reach, Deal Mechanic) always route through
# the OpenClaw (OpenAI) API regardless of which brain is active in the sidebar.

NEMOCLAW_AGENTS = {"Nemo Scout", "Claw Reach", "Deal Mechanic"}


def call_openclaw(system, message, openclaw_key, model="gpt-4o-mini", temperature=0.7, max_tokens=3000):
    """Call the OpenAI API for NemoClaw agents."""
    nk = normalize_api_key(openclaw_key)
    if not nk:
        return None, "OpenClaw API key is missing. Add OPENCLAW_API_KEY in Secrets or the sidebar."
    try:
        res = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {nk}"},
            json={
                "model": model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": message}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            },
            timeout=90,
        )
        data, err = _safe_json(res, "OpenClaw (OpenAI)")
        if err:
            return None, err
        if res.status_code >= 400:
            api_msg = data.get("error", {}).get("message", "Unknown API error") if isinstance(data, dict) else "Unknown API error"
            return None, f"OpenClaw error (HTTP {res.status_code}): {api_msg}"
        if isinstance(data, dict) and "error" in data:
            return None, f"OpenClaw API Error: {data['error'].get('message', data['error'])}"
        return data["choices"][0]["message"]["content"], None
    except Exception as e:
        return None, f"OpenClaw connection error: {str(e)}"


def call_heygen(script, avatar_id, voice_id, api_key):
    """Call HeyGen API to generate a video"""
    try:
        hk = normalize_api_key(api_key)
        res = requests.post(
            "https://api.heygen.com/v2/video/generate",
            headers={"X-Api-Key": hk, "Content-Type": "application/json"},
            json={
                "video_inputs": [{
                    "character": {"type": "avatar", "avatar_id": avatar_id, "avatar_style": "normal"},
                    "voice": {"type": "text", "input_text": script, "voice_id": voice_id},
                }],
                "dimension": {"width": 1280, "height": 720},
                "aspect_ratio": "16:9"
            },
            timeout=60
        )
        data, err = _safe_json(res, "HeyGen")
        if err:
            return None, err
        if res.status_code >= 400:
            return None, f"HeyGen error (HTTP {res.status_code}): {_extract_api_error(data)}"
        if isinstance(data, dict) and data.get("error"):
            return None, _extract_api_error(data)
        return data.get("data", {}).get("video_id"), None
    except Exception as e:
        return None, str(e)

def check_heygen_video(video_id, api_key):
    """Check HeyGen video status"""
    try:
        hk = normalize_api_key(api_key)
        res = requests.get(
            f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
            headers={"X-Api-Key": hk},
            timeout=30
        )
        data, err = _safe_json(res, "HeyGen")
        if err:
            return None, err
        if res.status_code >= 400:
            return None, f"HeyGen error (HTTP {res.status_code}): {_extract_api_error(data)}"
        return data.get("data", {}), None
    except Exception as e:
        return None, str(e)

def get_heygen_avatars(api_key):
    """Get list of available HeyGen avatars"""
    try:
        hk = normalize_api_key(api_key)
        res = requests.get(
            "https://api.heygen.com/v2/avatars",
            headers={"X-Api-Key": hk},
            timeout=30
        )
        data, err = _safe_json(res, "HeyGen")
        if err:
            return [], err
        if res.status_code >= 400:
            return [], f"HeyGen error (HTTP {res.status_code}): {_extract_api_error(data)}"
        return data.get("data", {}).get("avatars", []), None
    except Exception as e:
        return [], str(e)

def get_heygen_voices(api_key):
    """Get list of available HeyGen voices"""
    try:
        hk = normalize_api_key(api_key)
        res = requests.get(
            "https://api.heygen.com/v2/voices",
            headers={"X-Api-Key": hk},
            timeout=30
        )
        data, err = _safe_json(res, "HeyGen")
        if err:
            return [], err
        if res.status_code >= 400:
            return [], f"HeyGen error (HTTP {res.status_code}): {_extract_api_error(data)}"
        return data.get("data", {}).get("voices", []), None
    except Exception as e:
        return [], str(e)

def save_output(agent, content, phase="single"):
    """Save output with unique key — never overwrites"""
    uid = str(uuid.uuid4())[:8]
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    key = f"{ts}_{agent.replace(' ','_')}_{uid}"
    st.session_state.outputs[key] = {
        "title": f"{agent} — {datetime.now().strftime('%d/%m %H:%M')}",
        "agent": agent,
        "content": content,
        "time": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "phase": phase,
        "session": st.session_state.session_id,
    }
    return key

def load_persistent_memory():
    if not MEMORY_FILE.exists():
        return []

    try:
        data = json.loads(MEMORY_FILE.read_text())
    except Exception:
        return []

    if not isinstance(data, list):
        return []

    cleaned = []
    for item in data[-100:]:
        if not isinstance(item, dict):
            continue
        cleaned.append({
            "time": item.get("time", ""),
            "agent": item.get("agent", "Unknown"),
            "phase": item.get("phase", "single"),
            "content": str(item.get("content", ""))[:400],
        })
    return cleaned

def save_persistent_memory(memory_entries):
    if is_privacy_mode():
        return
    MEMORY_FILE.write_text(json.dumps(memory_entries[-100:], indent=2))

def hydrate_memory():
    if is_privacy_mode():
        return
    if not st.session_state.circular_memory:
        st.session_state.circular_memory = load_persistent_memory()

def clear_persistent_memory():
    if MEMORY_FILE.exists():
        MEMORY_FILE.unlink()

def default_business_profile():
    return {
        "business": "",
        "buyer": "",
        "revenue": "",
        "bottleneck": "",
        "budget": "",
        "team": "",
        "target_30d": "",
    }

def load_business_profile():
    defaults = default_business_profile()
    if not PROFILE_FILE.exists():
        return defaults

    try:
        data = json.loads(PROFILE_FILE.read_text())
    except Exception:
        return defaults

    if not isinstance(data, dict):
        return defaults

    for key in defaults:
        defaults[key] = str(data.get(key, ""))
    return defaults

def save_business_profile(profile):
    if is_privacy_mode():
        return
    clean = default_business_profile()
    for key in clean:
        clean[key] = str(profile.get(key, "")).strip()
    PROFILE_FILE.write_text(json.dumps(clean, indent=2))

def hydrate_business_profile():
    if is_privacy_mode():
        return
    current = st.session_state.get("business_profile", {})
    if not isinstance(current, dict) or not any(str(v).strip() for v in current.values()):
        st.session_state.business_profile = load_business_profile()

def default_avatar_profile():
    return {
        "avatar_id": "",
        "voice_id": "",
        "platforms": ["TikTok", "Instagram Reels", "YouTube Shorts"],
        "updated_at": "",
    }

def load_avatar_profile():
    defaults = default_avatar_profile()
    if not AVATAR_PROFILE_FILE.exists():
        return defaults

    try:
        data = json.loads(AVATAR_PROFILE_FILE.read_text())
    except Exception:
        return defaults

    if not isinstance(data, dict):
        return defaults

    avatar_id = str(data.get("avatar_id", "")).strip()
    voice_id = str(data.get("voice_id", "")).strip()
    platforms = data.get("platforms", defaults["platforms"])
    if not isinstance(platforms, list):
        platforms = defaults["platforms"]
    platforms = [str(p).strip() for p in platforms if str(p).strip()]

    defaults["avatar_id"] = avatar_id
    defaults["voice_id"] = voice_id
    defaults["platforms"] = platforms or default_avatar_profile()["platforms"]
    defaults["updated_at"] = str(data.get("updated_at", ""))
    return defaults

def save_avatar_profile(profile):
    if is_privacy_mode():
        return
    clean = default_avatar_profile()
    clean["avatar_id"] = str(profile.get("avatar_id", "")).strip()
    clean["voice_id"] = str(profile.get("voice_id", "")).strip()

    platforms = profile.get("platforms", clean["platforms"])
    if not isinstance(platforms, list):
        platforms = clean["platforms"]
    clean["platforms"] = [str(p).strip() for p in platforms if str(p).strip()] or default_avatar_profile()["platforms"]
    clean["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    AVATAR_PROFILE_FILE.write_text(json.dumps(clean, indent=2))

def hydrate_avatar_profile():
    if is_privacy_mode():
        return
    current = st.session_state.get("avatar_profile", {})
    if not isinstance(current, dict) or not any(str(v).strip() for v in current.values() if not isinstance(v, list)):
        st.session_state.avatar_profile = load_avatar_profile()

def status_to_progress(status):
    s = str(status or "").strip().lower()
    if s in ["completed", "success", "finished"]:
        return 1.0
    if s in ["failed", "error", "cancelled"]:
        return 1.0
    if s in ["processing", "rendering", "encoding"]:
        return 0.65
    if s in ["pending", "queued"]:
        return 0.25
    if s in ["submitted", "created"]:
        return 0.12
    return 0.1

def refresh_avatar_jobs(api_key, limit=5):
    jobs = st.session_state.get("avatar_jobs", [])
    if not jobs:
        return 0, []

    changed = 0
    issues = []
    tail_start = max(0, len(jobs) - limit)
    for i in range(len(jobs) - 1, tail_start - 1, -1):
        job = jobs[i]
        status = str(job.get("status", "")).lower()
        if status in ["completed", "success", "finished", "failed", "error", "cancelled"]:
            continue

        status_data, err = check_heygen_video(job.get("id", ""), api_key)
        if err:
            issues.append(err)
            continue
        if not status_data:
            continue

        new_status = str(status_data.get("status", "unknown")).strip().lower()
        job["status"] = new_status
        job["progress"] = status_to_progress(new_status)
        job["last_checked"] = datetime.now().strftime("%H:%M:%S")

        video_url = status_data.get("video_url", "")
        if video_url:
            job["video_url"] = video_url
        changed += 1

    st.session_state.avatar_jobs = jobs
    return changed, issues

def business_profile_to_snapshot(profile):
    rows = [
        ("Business", profile.get("business", "")),
        ("Buyer", profile.get("buyer", "")),
        ("Revenue now", profile.get("revenue", "")),
        ("Bottleneck", profile.get("bottleneck", "")),
        ("Budget", profile.get("budget", "")),
        ("Team", profile.get("team", "")),
        ("30-day target", profile.get("target_30d", "")),
    ]
    lines = [f"{label}: {value.strip()}" for label, value in rows if str(value).strip()]
    return "\n".join(lines)

def add_memory(agent, content, phase):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent, "phase": phase,
        "content": content[:400],
    }
    st.session_state.circular_memory.append(entry)
    if len(st.session_state.circular_memory) > 100:
        st.session_state.circular_memory = st.session_state.circular_memory[-100:]
    save_persistent_memory(st.session_state.circular_memory)

def get_memory_context():
    if not st.session_state.circular_memory:
        return ""
    recent = st.session_state.circular_memory[-6:]
    return "\n\nMemory context:\n" + "\n".join([
        f"[{m['time']} | {m['agent']}]: {m['content']}" for m in recent
    ])

def parse_json(text):
    try:
        clean = text.strip()
        for marker in ["```json", "```"]:
            if marker in clean:
                clean = clean.split(marker)[1].split("```")[0].strip()
                break
        return json.loads(clean), None
    except Exception as e:
        return None, str(e)

def log(msg, t="normal"):
    st.session_state.log.append({
        "time": datetime.now().strftime("%H:%M:%S"),
        "msg": msg, "type": t
    })

def save_to_github(content, filename, token, repo):
    """Save file to GitHub repo for persistent storage"""
    if is_privacy_mode():
        return False, "Privacy mode is enabled. Disable it before exporting to GitHub."
    try:
        # Check if file exists
        check = requests.get(
            f"https://api.github.com/repos/{repo}/contents/{filename}",
            headers={"Authorization": f"token {token}"},
            timeout=15
        )
        import base64
        encoded = base64.b64encode(content.encode()).decode()

        if check.status_code == 200:
            sha = check.json().get("sha")
            res = requests.put(
                f"https://api.github.com/repos/{repo}/contents/{filename}",
                headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
                json={"message": f"ROOMAN update {datetime.now().strftime('%d/%m %H:%M')}", "content": encoded, "sha": sha},
                timeout=15
            )
        else:
            res = requests.put(
                f"https://api.github.com/repos/{repo}/contents/{filename}",
                headers={"Authorization": f"token {token}", "Content-Type": "application/json"},
                json={"message": f"ROOMAN save {datetime.now().strftime('%d/%m %H:%M')}", "content": encoded},
                timeout=15
            )
        return res.status_code in [200, 201], None
    except Exception as e:
        return False, str(e)

# ─── UTILITY FUNCTIONS ────────────────────────────────────────────────────────

def validate_infrastructure_spec(spec_json):
    """Validates an infrastructure specification JSON from InsForge."""
    required_keys = ["project_name", "infrastructure", "deployment_script", "status"]
    issues = []
    for key in required_keys:
        if key not in spec_json:
            issues.append(f"Missing required field: {key}")
    infra = spec_json.get("infrastructure", {})
    if not infra.get("database"):
        issues.append("No database specification found")
    if not infra.get("api"):
        issues.append("No API specification found")
    return {"valid": len(issues) == 0, "issues": issues, "spec": spec_json}

def parse_forecast_data(text):
    """Parses and structures forecast data from Predict Anything output."""
    data, err = parse_json(text)
    if err or not data:
        return {"valid": False, "error": err or "Could not parse forecast", "raw": text}
    predictions = data.get("predictions", [])
    summary = {
        "forecast_type": data.get("forecast_type", "unknown"),
        "subject": data.get("subject", ""),
        "timeframe": data.get("timeframe", ""),
        "total_periods": len(predictions),
        "confidence_overall": data.get("confidence_overall", 0),
        "key_insights": data.get("key_insights", []),
        "recommended_actions": data.get("recommended_actions", []),
        "predictions": predictions,
        "valid": True,
    }
    return summary

def generate_deployment_script(spec):
    """Generates a runnable deployment script from an InsForge infrastructure spec."""
    if not isinstance(spec, dict):
        return "# Error: invalid spec"
    project = spec.get("project_name", "project")
    script = spec.get("deployment_script", "")
    iac = spec.get("infrastructure_as_code", "")
    env_vars = spec.get("infrastructure", {}).get("environment", {}).get("variables", [])
    lines = [
        f"#!/bin/bash",
        f"# ROOMAN InsForge — Auto-generated deployment script",
        f"# Project: {project}",
        f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "set -e",
        "",
        "# Environment Variables",
    ]
    for var in env_vars:
        lines.append(f"export {var}")
    lines += ["", "# Deployment Steps", script or "echo 'No deployment script provided'"]
    if iac:
        lines += ["", "# Infrastructure as Code", "# " + iac.replace("\n", "\n# ")]
    return "\n".join(lines)

def fetch_google_trends(geo="US", topic="", limit=10):
    """Fetch top daily Google Trends topics from the public RSS feed."""
    try:
        url = f"https://trends.google.com/trending/rss?geo={geo}"
        res = requests.get(url, timeout=25)
        res.raise_for_status()

        root = ET.fromstring(res.text)
        topic_lc = topic.strip().lower()
        trends = []

        for item in root.findall(".//item"):
            title = (item.findtext("title") or "").strip()
            description = (item.findtext("description") or "").strip()
            published = (item.findtext("pubDate") or "").strip()
            traffic = ""

            for child in item:
                tag_name = child.tag.split("}")[-1]
                if tag_name == "approx_traffic":
                    traffic = (child.text or "").strip()
                    break

            if not title:
                continue

            searchable = f"{title} {description}".lower()
            if topic_lc and topic_lc not in searchable:
                continue

            trends.append({
                "title": title,
                "description": description,
                "traffic": traffic,
                "published": published,
            })

        return trends[:limit], None
    except Exception as e:
        return [], str(e)

def build_avatar_script_from_trends(topic, niche, geo, trends):
    """Fallback short avatar script when AI polishing is unavailable."""
    top = trends[:5]
    opener_topic = topic.strip() or (top[0]["title"] if top else "today's trends")
    niche_line = f" for {niche.strip()}" if niche.strip() else ""
    trend_mentions = []

    for t in top[:3]:
        traffic_suffix = f" ({t['traffic']})" if t.get("traffic") else ""
        trend_mentions.append(f"{t['title']}{traffic_suffix}")

    highlights = ", ".join(trend_mentions) if trend_mentions else "high-momentum topics"
    return (
        f"Quick trend update from {geo}: {opener_topic} is heating up{niche_line}. "
        f"Right now, attention is clustering around {highlights}. "
        "If you create content in the next 24 hours using these angles, you can catch fresh demand while competition is still catching up. "
        "Follow for daily trend-backed content ideas you can monetize."
    )

def generate_avatar_script_with_brain(topic, niche, geo, trends, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl):
    """Use selected brain to convert trend signals into a short HeyGen-ready script."""
    trend_lines = []
    for item in trends[:6]:
        traffic = f" | traffic: {item.get('traffic')}" if item.get("traffic") else ""
        trend_lines.append(f"- {item.get('title','')}{traffic}")

    trend_block = "\n".join(trend_lines) if trend_lines else "- No trend lines found"
    prompt = f"""Create a punchy 90-130 word avatar script for a short business update video.

Topic focus: {topic or 'top daily trends'}
Niche focus: {niche or 'general monetizable opportunities'}
Country/region: {geo}

Trend signals:
{trend_block}

Requirements:
- Start with a strong hook in the first sentence
- Mention 2-3 trend topics naturally
- Explain why these trends matter for revenue/content creators
- Add one clear CTA at the end
- Return plain script text only (no bullets, no labels)
"""

    return call_brain(
        "You are a short-form scriptwriter for business and trend videos. Be concise and high-energy.",
        prompt,
        brain,
        api_key,
        ollama_ep,
        ollama_mdl,
        custom_url,
        custom_mdl,
        temperature=0.45,
        max_tokens=320,
    )

def estimate_seconds_from_script(script):
    """Estimate spoken duration at ~150 words per minute."""
    words = len(script.split())
    return int(round((words / 150.0) * 60)) if words else 0

def _trim_to_word_target(text, target_words):
    words = text.split()
    if not words:
        return ""
    if len(words) <= target_words:
        return text.strip()
    trimmed = " ".join(words[:target_words]).strip()
    if trimmed and trimmed[-1] not in ".!?":
        trimmed += "."
    return trimmed

def build_length_variants_fallback(base_script, durations):
    """Create simple script variants by trimming to rough word targets."""
    variants = {}
    for sec in durations:
        target_words = max(20, int(sec * 2.5))
        variants[str(sec)] = _trim_to_word_target(base_script, target_words)
    return variants

def generate_avatar_social_pack_with_brain(base_script, topic, niche, geo, durations, platforms, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl):
    """Generate multi-length scripts plus social captions/hashtags in one call."""
    durations_str = ", ".join([str(d) for d in durations])
    platforms_str = ", ".join(platforms)
    prompt = f"""Create a social content pack from this core avatar script.

Core script:
{base_script}

Topic: {topic or 'top trends'}
Niche: {niche or 'business growth'}
Region: {geo}
Durations requested (seconds): {durations_str}
Platforms requested: {platforms_str}

Return ONLY valid JSON:
{{
  "scripts": {{"15": "...", "30": "..."}},
  "captions": {{"TikTok": "...", "Instagram Reels": "..."}},
  "hashtags": {{"TikTok": ["#one", "#two"], "Instagram Reels": ["#one", "#two"]}}
}}

Rules:
- Each script must fit its duration naturally when spoken
- Keep hooks sharp and CTA clear
- Captions must be platform-native and concise
- Give 6-10 hashtags per platform
- No markdown, no commentary, JSON only
"""

    return call_brain(
        "You are a social growth copywriter producing short-form content packs for multiple platforms.",
        prompt,
        brain,
        api_key,
        ollama_ep,
        ollama_mdl,
        custom_url,
        custom_mdl,
        temperature=0.5,
        max_tokens=1200,
    )

def build_avatar_social_pack_fallback(base_script, topic, niche, durations, platforms):
    """Fallback social pack used if AI JSON generation fails."""
    scripts = build_length_variants_fallback(base_script, durations)
    label = topic.strip() or niche.strip() or "trending topics"
    captions = {}
    hashtags = {}
    base_tags = ["#trending", "#contentcreator", "#growth", "#marketing", "#viral", "#monetize"]

    for platform in platforms:
        captions[platform] = (
            f"{label.title()} update: use these signals now and publish while demand is hot. "
            "Save this for your next post plan."
        )
        hashtags[platform] = base_tags

    return {
        "scripts": scripts,
        "captions": captions,
        "hashtags": hashtags,
    }

def generate_weekly_content_plan_with_brain(topic, niche, geo, trends, platforms, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl):
    """Generate a 7-day short-form plan with monetization intent."""
    trend_lines = []
    for item in trends[:7]:
        traffic = f" ({item.get('traffic')})" if item.get("traffic") else ""
        trend_lines.append(f"- {item.get('title','')}{traffic}")

    prompt = f"""Build a 7-day short-form content calendar for growth and monetization.

Topic: {topic or 'daily trends'}
Niche: {niche or 'content growth'}
Region: {geo}
Platforms: {', '.join(platforms)}

Trend signals:
{chr(10).join(trend_lines) if trend_lines else '- none'}

Return ONLY valid JSON:
{{
  "days": [
    {{
      "day": 1,
      "angle": "...",
      "hook": "...",
      "script_30s": "...",
      "script_60s": "...",
      "cta": "...",
      "best_platform": "...",
      "monetization_play": "affiliate/sponsor/service lead magnet/etc"
    }}
  ]
}}

Rules:
- Exactly 7 day entries
- Keep scripts practical and post-ready
- Each day needs a clear monetization angle
- JSON only
"""

    return call_brain(
        "You are a short-form growth strategist focused on reach, conversion, and monetization.",
        prompt,
        brain,
        api_key,
        ollama_ep,
        ollama_mdl,
        custom_url,
        custom_mdl,
        temperature=0.45,
        max_tokens=1800,
    )

def build_weekly_content_plan_fallback(topic, niche, trends, platforms):
    """Fallback weekly calendar if AI generation is unavailable."""
    platform = platforms[0] if platforms else "TikTok"
    trend_titles = [t.get("title", "trend signal") for t in trends[:7]]
    while len(trend_titles) < 7:
        trend_titles.append(topic.strip() or niche.strip() or "high-intent trend")

    days = []
    for i in range(7):
        angle = trend_titles[i]
        days.append({
            "day": i + 1,
            "angle": angle,
            "hook": f"Everyone is missing this about {angle}.",
            "script_30s": f"Quick breakdown: why {angle} is moving now, what to do today, and one fast action to capture attention.",
            "script_60s": f"Deep dive on {angle}: why it is trending, where the audience demand is, and a step-by-step content angle to attract leads.",
            "cta": "Comment 'PLAN' and I will send the exact posting template.",
            "best_platform": platform,
            "monetization_play": "Lead magnet + service upsell",
        })
    return {"days": days}

def generate_sponsorship_kit_with_brain(topic, niche, audience_size, platforms, social_pack, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl):
    """Generate outreach copy and package ideas for sponsorship deals."""
    platform_data = ", ".join(platforms) if platforms else "TikTok, Instagram Reels"
    sample_caption = ""
    if isinstance(social_pack, dict):
        captions = social_pack.get("captions", {})
        if isinstance(captions, dict) and captions:
            sample_caption = next(iter(captions.values()))

    prompt = f"""Create a sponsorship pitch kit for a creator brand.

Topic: {topic or 'trending content'}
Niche: {niche or 'growth/marketing'}
Audience size: {audience_size or 'not provided'}
Platforms: {platform_data}
Sample content style: {sample_caption or 'short trend updates'}

Return ONLY valid JSON:
{{
  "one_liner_positioning": "...",
  "brand_categories": ["...", "..."],
  "packages": [
    {{"name":"Starter","deliverables":"...","price_anchor":"...","outcome":"..."}}
  ],
  "cold_dm_template": "...",
  "email_template": "...",
  "media_kit_bullets": ["...", "..."],
  "negotiation_notes": ["...", "..."]
}}

JSON only.
"""

    return call_brain(
        "You are a sponsorship strategist for creators who need real brand deals.",
        prompt,
        brain,
        api_key,
        ollama_ep,
        ollama_mdl,
        custom_url,
        custom_mdl,
        temperature=0.4,
        max_tokens=1400,
    )

def build_sponsorship_kit_fallback(topic, niche, platforms):
    """Fallback sponsorship assets."""
    descriptor = topic.strip() or niche.strip() or "trend-led short form"
    platform_line = ", ".join(platforms) if platforms else "TikTok, Instagram Reels"
    return {
        "one_liner_positioning": f"I create {descriptor} content that turns attention into action.",
        "brand_categories": ["Travel", "SaaS tools", "Creator economy", "Lifestyle"],
        "packages": [
            {"name": "Starter", "deliverables": "1 short video + 1 story", "price_anchor": "$250-$500", "outcome": "Fast awareness test"},
            {"name": "Growth", "deliverables": "3 short videos + 3 stories", "price_anchor": "$800-$1500", "outcome": "Reach + conversion push"},
            {"name": "Domination", "deliverables": "6 videos + pinned CTA + recap post", "price_anchor": "$2000+", "outcome": "Multi-week campaign lift"},
        ],
        "cold_dm_template": f"Hey {{brand}}, I run {descriptor} content on {platform_line}. I have a campaign angle that can position your product in front of high-intent viewers this week. Open to a quick collab chat?",
        "email_template": "Subject: Partnership idea\n\nHi [Brand],\n\nI create short-form trend content that drives high-intent traffic. I put together 3 collaboration options with clear deliverables and expected outcomes. If useful, I can send campaign concepts tailored to your next launch.\n\nBest,\n[Your Name]",
        "media_kit_bullets": [
            "Audience snapshot and niche fit",
            "Top 5 performing posts with reach and engagement",
            "Offer formats and timelines",
            "Past brand outcomes or case-style examples",
        ],
        "negotiation_notes": [
            "Sell outcomes and audience fit, not just views",
            "Offer a test package with upgrade path",
            "Lock usage rights, timeline, and payment milestones",
        ],
    }

def generate_client_offer_pack_with_brain(topic, niche, platforms, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl):
    """Generate sellable offer ideas for servicing business clients."""
    prompt = f"""Build a business client offer pack for a creator/agency.

Topic: {topic or 'trend content'}
Niche: {niche or 'marketing growth'}
Platforms: {', '.join(platforms) if platforms else 'TikTok, Instagram Reels, YouTube Shorts'}

Return ONLY valid JSON:
{{
  "offers": [
    {{
      "name": "...",
      "target_client": "...",
      "what_you_do": "...",
      "deliverables": ["..."],
      "pricing_model": "retainer/project/performance",
      "price_anchor": "...",
      "sales_angle": "..."
    }}
  ],
  "quick_proposal_template": "...",
  "onboarding_questions": ["...", "..."]
}}

JSON only.
"""

    return call_brain(
        "You are a commercial strategist who builds agency-style productized offers.",
        prompt,
        brain,
        api_key,
        ollama_ep,
        ollama_mdl,
        custom_url,
        custom_mdl,
        temperature=0.4,
        max_tokens=1500,
    )

def build_client_offer_pack_fallback(topic, niche, platforms):
    """Fallback business offer pack."""
    label = topic.strip() or niche.strip() or "trend-led content"
    channel = ", ".join(platforms) if platforms else "short-form platforms"
    return {
        "offers": [
            {
                "name": "Trend Sprint",
                "target_client": "Local businesses and startups",
                "what_you_do": f"Turn {label} into short-form campaigns across {channel}",
                "deliverables": ["12 videos/month", "Caption + hashtag pack", "Weekly trend report"],
                "pricing_model": "retainer",
                "price_anchor": "$1200-$2500/month",
                "sales_angle": "Fast visibility with consistent posting and trend timing",
            },
            {
                "name": "Sponsor Magnet",
                "target_client": "Creators and personal brands",
                "what_you_do": "Build content positioning that attracts sponsor offers",
                "deliverables": ["Sponsor pitch kit", "Media kit refresh", "4 brand-outreach campaigns"],
                "pricing_model": "project",
                "price_anchor": "$900-$1800",
                "sales_angle": "Turn attention into partnership revenue",
            },
        ],
        "quick_proposal_template": "We help [client] convert trend momentum into consistent short-form reach and qualified leads with a weekly content engine, platform-native packaging, and measurable conversion CTAs.",
        "onboarding_questions": [
            "What is your primary revenue goal in the next 90 days?",
            "Which offer has the best margin and should be promoted first?",
            "Which platforms are currently active and what has worked so far?",
            "Do you already have customer proof/testimonials we can amplify?",
        ],
    }

hydrate_memory()
hydrate_business_profile()
hydrate_avatar_profile()



# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# 🤖 ROOMAN")
    st.caption("100-Year Brain · CodeAct Loop · Self-Repair")
    st.markdown("---")

    brain = st.radio("Brain", ["DeepSeek API", "Ollama Local", "LM Studio / Custom"], label_visibility="collapsed")

    api_key = DEEPSEEK_KEY_DEFAULT
    ollama_ep = get_secret("OLLAMA_ENDPOINT", "http://localhost:11434")
    ollama_mdl = get_secret("OLLAMA_MODEL", "llama3")
    custom_url = ""
    custom_mdl = ""

    if brain == "DeepSeek API":
        api_key = st.text_input("DeepSeek API Key", type="password", key="deepseek_api_key_input", placeholder="sk-...")
        if DEEPSEEK_KEY_DEFAULT:
            st.success("✅ Key loaded from Secrets")
    elif brain == "Ollama Local":
        ollama_ep = st.text_input("Endpoint", value=ollama_ep)
        ollama_mdl = st.text_input("Model", value=ollama_mdl)
        st.success("✅ Free local")
    elif brain == "LM Studio / Custom":
        custom_url = st.text_input("Base URL", placeholder="http://localhost:1234/v1")
        api_key = st.text_input("Key", type="password")
        custom_mdl = st.text_input("Model", placeholder="qwen3")

    test_label = "🧪 Test DeepSeek Key" if brain == "DeepSeek API" else "🧪 Test Brain Connection"
    if st.button(test_label, use_container_width=True, key="test_brain_conn"):
        cfg_err = validate_brain_config(brain, api_key, custom_url, custom_mdl)
        if cfg_err:
            st.error(cfg_err)
        else:
            with st.spinner("Testing connection..."):
                probe_result, probe_err = call_brain(
                    "Reply with OK only.",
                    "OK",
                    brain,
                    api_key,
                    ollama_ep,
                    ollama_mdl,
                    custom_url,
                    custom_mdl,
                    0,
                    10,
                )
            if probe_err:
                st.error(probe_err)
            elif (probe_result or "").strip():
                st.success("Connection looks good.")
            else:
                st.warning("Connection succeeded but response was empty.")

    st.markdown("---")

    with st.expander("🔒 Privacy", expanded=False):
        st.caption("Privacy is always ON in this build. Sensitive sections are masked and cloud export is blocked.")

        if st.button("🧹 Wipe local stored files", use_container_width=True, key="wipe_local_data"):
            for f in [MEMORY_FILE, PROFILE_FILE, AVATAR_PROFILE_FILE]:
                if f.exists():
                    f.unlink()
            st.session_state.circular_memory = []
            st.session_state.business_profile = default_business_profile()
            st.session_state.avatar_profile = default_avatar_profile()
            st.success("Local profile/memory files deleted from disk.")

    with st.expander("💸 Prompt Library", expanded=True):
        side_play_labels = [f"{item['name']} · {item['agent']}" for item in PROMPT_LIBRARY]
        side_selected_play_label = st.selectbox("Pick a play", side_play_labels, key="side_prompt_library_sel")
        side_selected_play = next(item for item in PROMPT_LIBRARY if f"{item['name']} · {item['agent']}" == side_selected_play_label)

        st.caption(side_selected_play["description"])
        st.caption(f"Mode: {side_selected_play['mode'].title()} · Agent: {side_selected_play['agent']}")

        side_col1, side_col2 = st.columns(2)
        with side_col1:
            if st.button("To Single", use_container_width=True, key="side_load_play_single"):
                st.session_state["single_task"] = side_selected_play["prompt"]
                st.session_state["agent_sel_multi"] = [f"{AGENTS[side_selected_play['agent']]['emoji']} {side_selected_play['agent']}"]
                st.session_state["_loaded_play_name"] = side_selected_play["name"]
                st.session_state["_loaded_play_tab"] = "single"
                add_memory("Prompt Library", f"Loaded single play: {side_selected_play['name']}", "preload")
                st.rerun()
        with side_col2:
            if st.button("To Loop", use_container_width=True, key="side_load_play_loop"):
                st.session_state["loop_goal"] = side_selected_play["prompt"]
                st.session_state["loop_mem"] = f"Focus on profitable growth and measurable business outcomes. Loaded play: {side_selected_play['name']}"
                st.session_state["_loaded_play_name"] = side_selected_play["name"]
                st.session_state["_loaded_play_tab"] = "loop"
                add_memory("Prompt Library", f"Loaded loop play: {side_selected_play['name']}", "preload")
                st.rerun()

        if st.session_state.get("_loaded_play_tab") == "single":
            st.success(f"✅ **{st.session_state.get('_loaded_play_name', 'Play')}** loaded → go to main panel **Single tab** → fill brackets → ▶ RUN")
        elif st.session_state.get("_loaded_play_tab") == "loop":
            st.success(f"✅ **{st.session_state.get('_loaded_play_name', 'Play')}** loaded → go to main panel **Loop tab** → fill brackets → 🚀 START LOOP")

        with st.expander("Preview Prompt"):
            st.text_area(
                "",
                value=side_selected_play["prompt"],
                height=180,
                key="side_prompt_preview",
                disabled=True,
                label_visibility="collapsed",
            )

    st.markdown("---")

    # HeyGen
    with st.expander("🎬 HeyGen Settings"):
        heygen_key = st.text_input("HeyGen API Key", type="password", key="heygen_api_key_input", placeholder="paste key here")
        if HEYGEN_KEY_DEFAULT:
            st.success("✅ HeyGen loaded")
        if st.button("🧪 Test HeyGen Key", use_container_width=True, key="test_heygen_key"):
            heygen_cfg_err = validate_heygen_config(heygen_key)
            if heygen_cfg_err:
                st.error(heygen_cfg_err)
                st.session_state["_heygen_test_ok"] = False
                st.session_state["_heygen_test_msg"] = heygen_cfg_err
            else:
                with st.spinner("Testing HeyGen connection..."):
                    ok, msg = test_heygen_connection(heygen_key)
                st.session_state["_heygen_test_ok"] = ok
                st.session_state["_heygen_test_msg"] = msg
                if ok:
                    st.success(msg)
                else:
                    st.error(msg)

    # OpenClaw — dedicated brain for NemoClaw agents
    with st.expander("🦞 OpenClaw (NemoClaw)", expanded=False):
        st.caption("NemoClaw agents (Nemo Scout, Claw Reach, Deal Mechanic) always run through OpenClaw (OpenAI), independent of the brain selected above.")
        openclaw_key = st.text_input("OpenClaw API Key", type="password", key="openclaw_api_key_input", placeholder="sk-...")
        if OPENCLAW_KEY_DEFAULT:
            st.success("✅ OpenClaw key loaded from Secrets")
        openclaw_model = st.selectbox(
            "Model",
            ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo", "gpt-3.5-turbo"],
            index=0,
            key="openclaw_model_sel",
        )
        if st.button("🧪 Test OpenClaw Key", use_container_width=True, key="test_openclaw_key"):
            with st.spinner("Testing OpenClaw connection..."):
                probe, probe_err = call_openclaw("Reply with OK only.", "OK", openclaw_key, model=openclaw_model, temperature=0, max_tokens=10)
            if probe_err:
                st.error(probe_err)
            elif (probe or "").strip():
                st.success("OpenClaw connection looks good.")
            else:
                st.warning("Connection succeeded but response was empty.")

    # GitHub export is intentionally hidden in always-private mode.
    gh_token = ""
    gh_repo = ""

    # Operations Dashboard
    with st.expander("🚀 Operations Dashboard"):
        st.markdown("**Infrastructure Status**")
        infra_outputs = {k: v for k, v in st.session_state.outputs.items() if v.get("agent") == "InsForge"}
        if infra_outputs:
            latest_infra = list(infra_outputs.values())[-1]
            infra_data, _ = parse_json(latest_infra.get("content", ""))
            if infra_data:
                st.success(f"✅ {infra_data.get('project_name','Project')} — {infra_data.get('status','unknown')}")
                cost = infra_data.get("cost_estimate", {})
                if cost:
                    st.caption(f"💰 Est. cost: ${cost.get('monthly_usd','?')}/mo")
                if st.button("⬇ Get Deployment Script", key="ops_get_script", use_container_width=True):
                    script = generate_deployment_script(infra_data)
                    st.session_state["_ops_deploy_script"] = script
                if st.session_state.get("_ops_deploy_script"):
                    st.download_button(
                        "🚀 Download & Deploy",
                        data=st.session_state["_ops_deploy_script"],
                        file_name=f"deploy_{datetime.now().strftime('%Y%m%d_%H%M')}.sh",
                        mime="text/plain",
                        key=f"dl_deploy_{uuid.uuid4().hex[:6]}",
                        use_container_width=True,
                    )
            else:
                st.info("InsForge output found (text mode)")
        else:
            st.caption("No infrastructure provisioned yet")

        st.markdown("---")
        st.markdown("**Active Forecasts**")
        forecast_outputs = {k: v for k, v in st.session_state.outputs.items() if v.get("agent") == "Predict Anything"}
        if forecast_outputs:
            for fk, fv in list(forecast_outputs.items())[-3:]:
                fc = parse_forecast_data(fv.get("content", ""))
                if fc.get("valid"):
                    st.success(f"📈 {fc.get('forecast_type','').title()}: {fc.get('subject','')}")
                    st.caption(f"Confidence: {fc.get('confidence_overall',0)}% · {fc.get('timeframe','')}")
                    actions = fc.get("recommended_actions", [])
                    if actions:
                        top = actions[0]
                        st.caption(f"Top action: {top.get('action','')}")
                else:
                    st.info(f"Forecast: {fv.get('title','')}")
        else:
            st.caption("No forecasts generated yet")

    st.markdown("---")
    st.markdown("### 📊 Stats")

    phase_colors = {"idle":"⚫","analyze":"🔵","plan":"🟣","execute":"🟡","observe":"🟢","repair":"🔴","done":"✅"}
    st.markdown(f"**Phase:** {phase_colors.get(st.session_state.phase,'⚫')} `{st.session_state.phase.upper()}`")
    st.caption(f"Session: `{st.session_state.session_id}`")

    c1, c2 = st.columns(2)
    c1.metric("Loops", st.session_state.loop_count)
    c2.metric("Repairs", st.session_state.fault_count)
    c1.metric("Done", st.session_state.tasks_done)
    c2.metric("Outputs", len(st.session_state.outputs))

    st.markdown("---")
    st.markdown("### 📝 Todo.md")
    if st.session_state.todo:
        cur = st.session_state.current_todo
        for i, item in enumerate(st.session_state.todo):
            if i < cur:
                st.markdown(f'<span class="todo-done">✅ {item.get("agent","")}</span>', unsafe_allow_html=True)
            elif i == cur:
                st.markdown(f'<span class="todo-active">▶ {item.get("agent","")}</span>', unsafe_allow_html=True)
            else:
                st.markdown(f'<span class="todo-pending">⏳ {item.get("agent","")}</span>', unsafe_allow_html=True)
    else:
        st.caption("Empty — set a goal")

    st.markdown("---")
    if st.button("🔄 Reset Session", use_container_width=True):
        for k, v in DEFAULTS.items():
            if k == "outputs":
                pass  # Keep outputs on reset
            elif k == "circular_memory":
                st.session_state[k] = load_persistent_memory()
            elif k == "business_profile":
                st.session_state[k] = load_business_profile()
            elif k == "avatar_profile":
                st.session_state[k] = load_avatar_profile()
            elif k == "avatar_jobs":
                st.session_state[k] = []
            elif isinstance(v, list):
                st.session_state[k] = []
            elif isinstance(v, dict):
                st.session_state[k] = {}
            else:
                st.session_state[k] = v
        st.session_state["_avatar_defaults_loaded"] = False
        st.session_state.session_id = str(uuid.uuid4())[:8]
        st.rerun()

# ─── MAIN LAYOUT — 3 COLUMNS ──────────────────────────────────────────────────

st.markdown("# 🤖 ROOMAN — 100-Year Brain")

# Phase bar
phase_cols = st.columns(5)
for i, (p, icon, label) in enumerate([
    ("analyze","🔵","ANALYZE"), ("plan","🟣","PLAN"),
    ("execute","🟡","EXECUTE"), ("observe","🟢","OBSERVE"), ("repair","🔴","REPAIR")
]):
    active = st.session_state.phase == p
    css = "phase-active" if active else "phase-inactive"
    phase_cols[i].markdown(f'<span class="{css}">{icon} {label}</span>', unsafe_allow_html=True)

st.markdown("---")

# 3 COLUMN LAYOUT
left_col, centre_col, right_col = st.columns([1, 2, 1])

# ═══════════════════════════════════════
# LEFT — AGENT CONTROLS
# ═══════════════════════════════════════

with left_col:
    st.markdown("### 🤖 Agents")

    with st.expander("💸 Revenue Plays", expanded=True):
        play_labels = [f"{item['name']} · {item['agent']}" for item in PROMPT_LIBRARY]
        selected_play_label = st.selectbox("Starter prompt", play_labels, key="prompt_library_sel")
        selected_play = next(item for item in PROMPT_LIBRARY if f"{item['name']} · {item['agent']}" == selected_play_label)

        st.caption(selected_play["description"])
        st.caption(f"Best in: {selected_play['mode'].title()} mode · Suggested agent: {selected_play['agent']}")
        st.text_area(
            "Preview",
            value=selected_play["prompt"],
            height=170,
            key="prompt_preview",
            disabled=True,
        )

        play_col1, play_col2 = st.columns(2)
        with play_col1:
            if st.button("Load To Single", use_container_width=True, key="load_play_single"):
                st.session_state["single_task"] = selected_play["prompt"]
                st.session_state["agent_sel_multi"] = [f"{AGENTS[selected_play['agent']]['emoji']} {selected_play['agent']}"]
                st.session_state["_loaded_play_name"] = selected_play["name"]
                st.session_state["_loaded_play_tab"] = "single"
                add_memory("Prompt Library", f"Loaded single play: {selected_play['name']}", "preload")
                st.rerun()
        with play_col2:
            if st.button("Load To Loop", use_container_width=True, key="load_play_loop"):
                st.session_state["loop_goal"] = selected_play["prompt"]
                st.session_state["loop_mem"] = f"Focus on profitable growth and measurable business outcomes. Loaded play: {selected_play['name']}"
                st.session_state["_loaded_play_name"] = selected_play["name"]
                st.session_state["_loaded_play_tab"] = "loop"
                add_memory("Prompt Library", f"Loaded loop play: {selected_play['name']}", "preload")
                st.rerun()

        if st.session_state.get("_loaded_play_tab") == "single":
            st.success(f"✅ **{st.session_state.get('_loaded_play_name', 'Play')}** loaded → scroll down to the **Single tab** and hit ▶ RUN")
        elif st.session_state.get("_loaded_play_tab") == "loop":
            st.success(f"✅ **{st.session_state.get('_loaded_play_name', 'Play')}** loaded → scroll down to the **Loop tab** and hit 🚀 START LOOP")

        st.markdown("---")
        st.markdown("#### Revenue Machine")

        profile = st.session_state.get("business_profile", default_business_profile())
        bp_business = st.text_input("Business", value=profile.get("business", ""), key="bp_business")
        bp_buyer = st.text_input("Buyer", value=profile.get("buyer", ""), key="bp_buyer")
        bp_revenue = st.text_input("Revenue now", value=profile.get("revenue", ""), key="bp_revenue")
        bp_bottleneck = st.text_input("Bottleneck", value=profile.get("bottleneck", ""), key="bp_bottleneck")
        bp_budget = st.text_input("Budget", value=profile.get("budget", ""), key="bp_budget")
        bp_team = st.text_input("Team", value=profile.get("team", ""), key="bp_team")
        bp_target_30d = st.text_input("30-day target", value=profile.get("target_30d", ""), key="bp_target_30d")

        profile_data = {
            "business": bp_business,
            "buyer": bp_buyer,
            "revenue": bp_revenue,
            "bottleneck": bp_bottleneck,
            "budget": bp_budget,
            "team": bp_team,
            "target_30d": bp_target_30d,
        }

        profile_col1, profile_col2 = st.columns(2)
        with profile_col1:
            if st.button("💾 Save Profile", use_container_width=True, key="save_business_profile"):
                st.session_state.business_profile = profile_data
                save_business_profile(profile_data)
                if is_privacy_mode():
                    st.info("Private mode is ON: profile kept in this session only.")
                else:
                    st.success("Business profile saved")
        with profile_col2:
            if st.button("Use Saved Profile", use_container_width=True, key="use_business_profile"):
                st.session_state["rev_machine_snapshot"] = business_profile_to_snapshot(profile_data)
                st.rerun()

        biz_snapshot = st.text_area(
            "Business snapshot",
            placeholder="What you sell, who buys, current monthly revenue, bottleneck, budget, team size",
            height=90,
            key="rev_machine_snapshot"
        )
        if st.button("🔥 Run Revenue Machine Now", type="primary", use_container_width=True, key="run_revenue_machine"):
            cfg_err = validate_brain_config(brain, api_key, custom_url, custom_mdl)
            if cfg_err:
                st.error(cfg_err)
            else:
                if not biz_snapshot.strip():
                    biz_snapshot = business_profile_to_snapshot(profile_data)

                if biz_snapshot.strip():
                    st.session_state.business_profile = profile_data
                    save_business_profile(profile_data)
                    machine_goal = f"""Goal: Build and execute a 30-day revenue machine for this business.\n\nBusiness snapshot:\n{biz_snapshot}\n\nRequirements:\n- Prioritise fastest path to cash while protecting margin\n- Design a clear acquisition, conversion, and retention plan\n- Define one high-confidence offer ladder and pricing upgrade path\n- Specify weekly KPI targets and a reporting cadence\n- Include a 7-day quick win plan and a 30-day scaling plan\n- Focus on actions a small team can actually execute now\n\nReturn an execution-first plan with steps, owners, outputs, and what to test first."""
                    st.session_state["loop_goal"] = machine_goal
                    st.session_state["loop_mem"] = "Operator mode: ruthless prioritisation, measurable outcomes, and revenue-first decisions."
                    add_memory("Revenue Machine", f"Business snapshot: {biz_snapshot[:240]}", "preload")
                    st.session_state.phase = "analyze"
                    st.session_state.plan = {"goal": machine_goal}
                    st.session_state.auto_approve_loop = True
                    log("🔥 Revenue Machine launched", "start")
                    st.rerun()
                else:
                    st.warning("Add a business snapshot first.")

    agent_tabs = st.tabs(["Single", "Loop"])

    with agent_tabs[0]:
        if st.session_state.get("_loaded_play_tab") == "single" and st.session_state.get("_loaded_play_name"):
            st.info(f"📥 **{st.session_state['_loaded_play_name']}** is loaded — fill in the [brackets] then hit ▶ RUN")

        agent_labels = [f"{d['emoji']} {n}" for n, d in AGENTS.items()]
        selected_agents = st.multiselect(
            "Agents",
            agent_labels,
            default=agent_labels[:1],
            max_selections=2,
            key="agent_sel_multi"
        )

        selected_names = [label.split(" ", 1)[1] if " " in label else label for label in selected_agents]
        if not selected_names:
            st.info("Choose one or two agents.")
            selected_names = []

        for selected_name in selected_names:
            selected_agent = AGENTS.get(selected_name)
            if selected_agent:
                badge = " 🦞 **OpenClaw**" if selected_name in NEMOCLAW_AGENTS else ""
                st.caption(f"{selected_agent['emoji']} {selected_name}: *{selected_agent['description']}*{badge}")

        compare_mode = len(selected_names) == 2
        placeholder_name = " and ".join(selected_names) if selected_names else "your agents"
        task = st.text_area("Task:", height=100, placeholder=f"Tell {placeholder_name} what to do...", key="single_task")
        use_mem = st.checkbox("Use memory", value=True, key="use_mem")

        run_label = "▶ RUN COMPARE" if compare_mode else "▶ RUN"
        if st.button(run_label, type="primary", use_container_width=True, key="run_single"):
            if task.strip() and selected_names:
                # Validate brain config only for non-NemoClaw agents
                non_nc = [n for n in selected_names if n not in NEMOCLAW_AGENTS]
                if non_nc:
                    cfg_err = validate_brain_config(brain, api_key, custom_url, custom_mdl)
                    if cfg_err:
                        st.error(cfg_err)
                        st.stop()
                full = task + (get_memory_context() if use_mem else "")
                run_results = []
                for selected_name in selected_names:
                    selected_agent = AGENTS[selected_name]
                    if selected_name in NEMOCLAW_AGENTS:
                        oc_key = st.session_state.get("openclaw_api_key_input", "") or OPENCLAW_KEY_DEFAULT
                        oc_model = st.session_state.get("openclaw_model_sel", "gpt-4o-mini")
                        with st.spinner(f"Running {selected_name} via OpenClaw..."):
                            result, err = call_openclaw(
                                selected_agent["system"], full, oc_key,
                                model=oc_model,
                                temperature=selected_agent.get("temperature", 0.7),
                                max_tokens=selected_agent.get("max_tokens", 3000),
                            )
                    else:
                        with st.spinner(f"Running {selected_name}..."):
                            result, err = call_brain(
                                selected_agent["system"], full, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl,
                                selected_agent.get("temperature", 0.7), selected_agent.get("max_tokens", 3000)
                            )

                    if err:
                        st.error(f"{selected_name}: {err}")
                        continue

                    save_output(selected_name, result, "single")
                    add_memory(selected_name, result, "single")
                    st.session_state.tasks_done += 1
                    log(f"✅ {selected_name} done", "success")
                    run_results.append({"agent": selected_name, "content": result})

                st.session_state["_last_single_results"] = run_results
                if run_results:
                    st.rerun()

        last_results = st.session_state.get("_last_single_results", [])
        if last_results:
            st.markdown("#### Latest Single Run")
            for result in last_results:
                with st.expander(f"{result['agent']} output", expanded=compare_mode):
                    st.markdown(f'<div class="output-box">{result["content"]}</div>', unsafe_allow_html=True)
            for result in last_results:
                st.download_button(
                    f"⬇ Download {result['agent']}",
                    data=result["content"],
                    file_name=f"{result['agent'].replace(' ','_')}_{datetime.now().strftime('%H%M%S')}.txt",
                    mime="text/plain",
                    key=f"dl_single_{result['agent']}_{datetime.now().strftime('%H%M%S')}"
                )

    with agent_tabs[1]:
        if st.session_state.get("_loaded_play_tab") == "loop" and st.session_state.get("_loaded_play_name"):
            st.info(f"📥 **{st.session_state['_loaded_play_name']}** is loaded — fill in the [brackets] then hit 🚀 START LOOP")

        goal = st.text_area("Goal:", height=80, placeholder="What do you want to build?", key="loop_goal")
        mem_pre = st.text_area("Pre-load context:", height=50, placeholder="Brand voice, business context...", key="loop_mem")

        if st.button("🚀 START LOOP", type="primary", use_container_width=True, key="start_loop"):
            if goal.strip():
                cfg_err = validate_brain_config(brain, api_key, custom_url, custom_mdl)
                if cfg_err:
                    st.error(cfg_err)
                else:
                    if mem_pre.strip():
                        add_memory("User", mem_pre, "preload")
                    st.session_state.phase = "analyze"
                    st.session_state.plan = {"goal": goal}
                    log(f"🚀 Goal: {goal[:60]}", "start")
                    st.rerun()

        if st.session_state.phase != "idle" and st.session_state.phase != "done":
            if st.button("⏹ STOP", use_container_width=True, key="stop_loop"):
                st.session_state.phase = "idle"
                st.rerun()

    st.markdown("---")
    st.markdown("### 🎬 HeyGen Avatar")

    st.caption("Auto-fill script from live Google Trends")
    trend_col1, trend_col2 = st.columns(2)
    with trend_col1:
        hg_topic = st.text_input("Trend topic (optional)", placeholder="AI tools, crypto, fitness, football", key="hg_topic")
    with trend_col2:
        hg_geo = st.selectbox(
            "Region",
            ["US", "GB", "CA", "AU", "IN", "NG", "ZA", "KE", "IE", "SG"],
            index=0,
            key="hg_geo",
            help="Google Trends region code",
        )

    hg_niche = st.text_input(
        "Niche angle (optional)",
        placeholder="affiliate marketing, local business, ecommerce, coaching",
        key="hg_niche"
    )

    avatar_profile = st.session_state.get("avatar_profile", default_avatar_profile())
    if not st.session_state.get("_avatar_defaults_loaded"):
        if avatar_profile.get("avatar_id") and not st.session_state.get("hg_avatar"):
            st.session_state["hg_avatar"] = avatar_profile.get("avatar_id", "")
        if avatar_profile.get("voice_id") and not st.session_state.get("hg_voice"):
            st.session_state["hg_voice"] = avatar_profile.get("voice_id", "")
        if avatar_profile.get("platforms") and not st.session_state.get("hg_platforms"):
            st.session_state["hg_platforms"] = avatar_profile.get("platforms", [])
        st.session_state["_avatar_defaults_loaded"] = True

    length_col1, length_col2 = st.columns(2)
    with length_col1:
        hg_lengths = st.multiselect(
            "Video lengths (seconds)",
            [15, 30, 45, 60, 90],
            default=[15, 30, 60],
            key="hg_lengths"
        )
    with length_col2:
        hg_platforms = st.multiselect(
            "Target platforms",
            ["TikTok", "Instagram Reels", "YouTube Shorts", "X", "LinkedIn"],
            default=["TikTok", "Instagram Reels", "YouTube Shorts"],
            key="hg_platforms"
        )

    if st.button("⚡ Auto-Fill Script From Trends", use_container_width=True, key="autofill_avatar_script"):
        with st.spinner("Pulling live trends..."):
            trends, trend_err = fetch_google_trends(hg_geo, hg_topic, limit=10)

        if trend_err:
            st.error(f"Could not fetch Google Trends: {trend_err}")
        elif not trends:
            st.warning("No matching trends found for that topic/region. Try a broader topic.")
        else:
            ai_script, ai_err = generate_avatar_script_with_brain(
                hg_topic,
                hg_niche,
                hg_geo,
                trends,
                brain,
                api_key,
                ollama_ep,
                ollama_mdl,
                custom_url,
                custom_mdl,
            )

            if ai_err or not ai_script:
                ai_script = build_avatar_script_from_trends(hg_topic, hg_niche, hg_geo, trends)

            st.session_state["hg_script"] = ai_script.strip()
            st.session_state["hg_trends_preview"] = trends[:5]
            add_memory("Avatar Trends", f"Auto-script generated for {hg_geo} topic '{hg_topic or 'top trends'}'", "single")
            st.success("Script auto-filled from live trends")

    if st.button("📦 Generate Lengths + Social Pack", use_container_width=True, key="gen_avatar_social_pack"):
        base_script = st.session_state.get("hg_script", "").strip()
        if not base_script:
            st.warning("Auto-fill or type a base script first.")
        elif not hg_lengths:
            st.warning("Pick at least one video length.")
        elif not hg_platforms:
            st.warning("Pick at least one platform.")
        else:
            with st.spinner("Building multi-platform content pack..."):
                pack_text, pack_err = generate_avatar_social_pack_with_brain(
                    base_script,
                    hg_topic,
                    hg_niche,
                    hg_geo,
                    hg_lengths,
                    hg_platforms,
                    brain,
                    api_key,
                    ollama_ep,
                    ollama_mdl,
                    custom_url,
                    custom_mdl,
                )

            pack_data = None
            if not pack_err and pack_text:
                pack_data, parse_err = parse_json(pack_text)
                if parse_err:
                    pack_data = None

            if not isinstance(pack_data, dict):
                pack_data = build_avatar_social_pack_fallback(base_script, hg_topic, hg_niche, hg_lengths, hg_platforms)

            st.session_state["hg_social_pack"] = pack_data
            add_memory("Avatar Social Pack", f"Built pack for lengths {hg_lengths} on {', '.join(hg_platforms)}", "single")
            st.success("Multi-length scripts and social pack ready")

    trend_preview = st.session_state.get("hg_trends_preview", [])
    if trend_preview:
        with st.expander("Latest trend lines used"):
            for item in trend_preview:
                traffic = f" ({item.get('traffic')})" if item.get("traffic") else ""
                st.caption(f"• {item.get('title','')}{traffic}")

    hg_script = st.text_area("Script:", height=80, placeholder="Paste avatar script here...", key="hg_script")

    script_seconds = estimate_seconds_from_script(hg_script)
    if hg_script.strip():
        st.caption(f"Estimated duration: ~{script_seconds}s")

    social_pack = st.session_state.get("hg_social_pack")
    if isinstance(social_pack, dict):
        with st.expander("Generated scripts by length", expanded=False):
            scripts = social_pack.get("scripts", {}) if isinstance(social_pack.get("scripts", {}), dict) else {}
            script_keys = sorted(scripts.keys(), key=lambda x: int(x) if str(x).isdigit() else 999)
            for k in script_keys:
                val = str(scripts.get(k, "")).strip()
                if not val:
                    continue
                row_col1, row_col2 = st.columns([3, 1])
                row_col1.caption(f"{k}s script")
                row_col1.markdown(f"<div class='output-box'>{val}</div>", unsafe_allow_html=True)
                if row_col2.button(f"Use {k}s", key=f"use_len_{k}", use_container_width=True):
                    st.session_state["hg_script"] = val
                    st.rerun()

        with st.expander("Captions + hashtags", expanded=False):
            captions = social_pack.get("captions", {}) if isinstance(social_pack.get("captions", {}), dict) else {}
            hashtags = social_pack.get("hashtags", {}) if isinstance(social_pack.get("hashtags", {}), dict) else {}
            for platform in hg_platforms:
                cap = str(captions.get(platform, "")).strip()
                tags = hashtags.get(platform, [])
                tag_line = " ".join(tags) if isinstance(tags, list) else str(tags)
                st.markdown(f"**{platform}**")
                st.caption(cap)
                st.caption(tag_line)

        st.download_button(
            "⬇ Download Social Pack",
            data=json.dumps(social_pack, indent=2),
            file_name=f"avatar_social_pack_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
            mime="application/json",
            key="dl_avatar_social_pack",
            use_container_width=True,
        )

    hg_avatar = st.text_input("Avatar ID:", placeholder="avatar_id from HeyGen", key="hg_avatar")
    hg_voice = st.text_input("Voice ID:", placeholder="voice_id from HeyGen", key="hg_voice")

    save_col1, save_col2 = st.columns(2)
    with save_col1:
        if st.button("💾 Save Avatar Defaults", use_container_width=True, key="save_avatar_defaults"):
            profile_payload = {
                "avatar_id": hg_avatar,
                "voice_id": hg_voice,
                "platforms": hg_platforms,
            }
            if not str(hg_avatar).strip() or not str(hg_voice).strip():
                st.warning("Add both Avatar ID and Voice ID before saving defaults.")
            else:
                save_avatar_profile(profile_payload)
                st.session_state.avatar_profile = load_avatar_profile()
                add_memory("Avatar Profile", f"Saved avatar defaults for {', '.join(hg_platforms[:3])}", "single")
                if is_privacy_mode():
                    st.info("Private mode is ON: avatar defaults kept in this session only.")
                else:
                    st.success("Avatar defaults saved. These load automatically next time.")

    with save_col2:
        if st.button("↺ Load Saved Avatar", use_container_width=True, key="load_avatar_defaults"):
            saved = load_avatar_profile()
            st.session_state.avatar_profile = saved
            st.session_state["hg_avatar"] = saved.get("avatar_id", "")
            st.session_state["hg_voice"] = saved.get("voice_id", "")
            st.session_state["hg_platforms"] = saved.get("platforms", default_avatar_profile()["platforms"])
            st.success("Loaded saved avatar defaults.")
            st.rerun()

    saved_profile = st.session_state.get("avatar_profile", {})
    if saved_profile.get("avatar_id") and saved_profile.get("voice_id"):
        updated_at = saved_profile.get("updated_at", "")
        st.caption(
            f"Saved avatar: {saved_profile.get('avatar_id')} | voice: {saved_profile.get('voice_id')}"
            + (f" | updated: {updated_at}" if updated_at else "")
        )

    hk = heygen_key if 'heygen_key' in dir() else ""
    hk_clean = normalize_api_key(hk)
    ready_script = bool(hg_script.strip())
    ready_avatar = bool(hg_avatar.strip())
    ready_voice = bool(hg_voice.strip())
    ready_key = bool(hk_clean)

    with st.expander("🩺 HeyGen Readiness", expanded=False):
        st.caption("Quick pre-flight checks before generation")
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("API Key", "OK" if ready_key else "Missing")
        c2.metric("Script", "OK" if ready_script else "Missing")
        c3.metric("Avatar ID", "OK" if ready_avatar else "Missing")
        c4.metric("Voice ID", "OK" if ready_voice else "Missing")

        if not (ready_key and ready_script and ready_avatar and ready_voice):
            missing = []
            if not ready_key:
                missing.append("HeyGen API key")
            if not ready_script:
                missing.append("script")
            if not ready_avatar:
                missing.append("avatar ID")
            if not ready_voice:
                missing.append("voice ID")
            st.warning("Missing: " + ", ".join(missing))

        if st.session_state.get("_heygen_test_msg"):
            if st.session_state.get("_heygen_test_ok"):
                st.caption("Last key test: connected")
            else:
                st.caption("Last key test: failed")

    if st.button("🎬 GENERATE VIDEO", type="primary", use_container_width=True, key="gen_video"):
        hk = heygen_key if 'heygen_key' in dir() else ""
        heygen_cfg_err = validate_heygen_config(hk)
        if heygen_cfg_err:
            st.error(heygen_cfg_err)
        elif not hg_script.strip():
            st.error("Add a script first")
        elif not hg_avatar.strip():
            st.error("Add Avatar ID")
        elif not hg_voice.strip():
            st.error("Add Voice ID")
        else:
            with st.spinner("🎬 Sending to HeyGen..."):
                video_id, err = call_heygen(hg_script, hg_avatar, hg_voice, hk)
            if err:
                st.error(f"HeyGen error: {err}")
            else:
                now_stamp = datetime.now().strftime("%H:%M:%S")
                job_entry = {
                    "id": video_id,
                    "status": "submitted",
                    "progress": 0.12,
                    "created_at": now_stamp,
                    "last_checked": now_stamp,
                    "avatar_id": hg_avatar.strip(),
                    "voice_id": hg_voice.strip(),
                    "script_seconds": script_seconds,
                    "platforms": hg_platforms,
                    "target_page": hg_platforms[0] if hg_platforms else "TikTok",
                    "topic": hg_topic.strip(),
                    "video_url": "",
                }
                jobs = st.session_state.get("avatar_jobs", [])
                jobs.append(job_entry)
                st.session_state.avatar_jobs = jobs[-20:]
                st.session_state[f"video_{video_id}"] = {"status": "processing", "id": video_id}
                st.success(f"✅ Video generating! ID: `{video_id}`")
                log(f"🎬 HeyGen video started: {video_id}", "success")

    # Check video status
    if st.button("🔄 Check Video Status", use_container_width=True, key="check_vid"):
        hk = heygen_key if 'heygen_key' in dir() else ""
        heygen_cfg_err = validate_heygen_config(hk)
        if heygen_cfg_err:
            st.error(heygen_cfg_err)
        else:
            changed, issues = refresh_avatar_jobs(hk, limit=8)
            if changed:
                st.success(f"Updated {changed} avatar job(s).")
            if issues:
                st.warning(f"Status check issue: {issues[-1]}")

    hk = heygen_key if 'heygen_key' in dir() else ""
    auto_refresh_avatar = st.checkbox(
        "Auto-refresh avatar status every 20s",
        value=st.session_state.get("avatar_auto_refresh", False),
        key="avatar_auto_refresh",
        help="Automatically checks HeyGen status and updates progress bars.",
    )

    if auto_refresh_avatar:
        if validate_heygen_config(hk):
            st.info("Add HeyGen API key to use auto-refresh.")
        elif hasattr(st, "autorefresh"):
            st.autorefresh(interval=20000, key="avatar_status_autorefresh")
            changed, issues = refresh_avatar_jobs(hk, limit=8)
            if issues:
                st.warning(f"Auto-refresh issue: {issues[-1]}")
            elif changed:
                st.caption(f"Auto-refresh updated {changed} job(s).")
        else:
            st.caption("Auto-refresh is not available in this Streamlit build. Use Check Video Status.")

    jobs = st.session_state.get("avatar_jobs", [])
    if jobs:
        st.markdown("#### Avatar Run Status")
        status_col1, status_col2 = st.columns(2)
        with status_col1:
            running_count = sum(1 for j in jobs if str(j.get("status", "")).lower() not in ["completed", "success", "finished", "failed", "error", "cancelled"])
            st.metric("Running", running_count)
        with status_col2:
            completed_count = sum(1 for j in jobs if str(j.get("status", "")).lower() in ["completed", "success", "finished"])
            st.metric("Completed", completed_count)

        for idx, job in enumerate(reversed(jobs[-5:]), start=1):
            status_raw = str(job.get("status", "unknown"))
            status_norm = status_raw.lower()
            progress = float(job.get("progress", status_to_progress(status_raw)))
            progress = max(0.0, min(1.0, progress))
            status_label = status_raw.upper()
            st.caption(
                f"Job {idx} | Status: {status_label} | Target page: {job.get('target_page', 'TikTok')} | "
                f"Platforms: {', '.join(job.get('platforms', [])) or 'TikTok'} | Last check: {job.get('last_checked', '--:--:--')}"
            )
            st.progress(progress)

            if status_norm in ["completed", "success", "finished"]:
                url = str(job.get("video_url", "")).strip()
                if url:
                    st.markdown(f"[▶ Watch Video]({url})")
                    st.markdown(f"[⬇ Download]({url})")
            elif status_norm in ["failed", "error", "cancelled"]:
                st.error(f"Avatar job {job.get('id', '')} ended with status: {status_raw}")
            else:
                st.info("Rendering in progress. Use Check Video Status to refresh this bar.")

    if st.button("📋 Get My Avatars", use_container_width=True, key="get_avatars"):
        hk = heygen_key if 'heygen_key' in dir() else ""
        if hk:
            with st.spinner("Loading avatars..."):
                avatars, err = get_heygen_avatars(hk)
            if avatars:
                for av in avatars[:5]:
                    st.caption(f"ID: `{av.get('avatar_id','')}` — {av.get('avatar_name','')}")
            else:
                st.error(err or "No avatars found")

# ═══════════════════════════════════════
# CENTRE — BRAIN PANEL + LOOP OUTPUT
# ═══════════════════════════════════════

with centre_col:

    centre_tabs = st.tabs(["🧠 Brain Chat", "🔄 Loop Output", "⚔️ Compare", "📋 Outputs"])
    privacy_mode = is_privacy_mode()

    # ── BRAIN CHAT ──
    with centre_tabs[0]:
        st.markdown("### 🧠 Brain Chat")
        st.caption("Chat directly with your AI brain. Full memory context included.")

        # Chat history display
        st.markdown('<div class="brain-panel">', unsafe_allow_html=True)
        if st.session_state.chat_history:
            if privacy_mode:
                st.markdown('<div style="color:#94a3b8;text-align:center;padding:24px">Private mode is ON. Chat transcript is hidden.</div>', unsafe_allow_html=True)
            else:
                for msg in st.session_state.chat_history[-20:]:
                    role = msg.get("role","")
                    content = msg.get("content","")
                    if role == "user":
                        st.markdown(f'<div class="chat-user">👤 {content}</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="chat-ai">🤖 {content}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="color:#334155;text-align:center;padding:40px">Start chatting — full memory context included</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)

        chat_input = st.text_input("Message:", placeholder="Ask anything...", key="chat_input")
        chat_col1, chat_col2 = st.columns([3,1])
        with chat_col1:
            if st.button("Send", type="primary", use_container_width=True, key="send_chat"):
                if chat_input.strip():
                    mem_ctx = get_memory_context()
                    history_ctx = "\n".join([f"{m['role']}: {m['content'][:200]}" for m in st.session_state.chat_history[-6:]])
                    full_msg = f"{chat_input}\n\nConversation history:\n{history_ctx}{mem_ctx}"

                    with st.spinner("Thinking..."):
                        result, err = call_brain(
                            "You are ROOMAN's central AI brain. You help plan, advise, and coordinate. You have full context of everything happening in the system. Be direct and helpful.",
                            full_msg, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl,
                            0.4, 2400
                        )

                    if err:
                        st.error(err)
                    else:
                        st.session_state.chat_history.append({"role":"user","content":chat_input})
                        st.session_state.chat_history.append({"role":"assistant","content":result})
                        add_memory("Brain Chat", result, "chat")
                        st.rerun()

        with chat_col2:
            if st.button("Clear", use_container_width=True, key="clear_chat"):
                st.session_state.chat_history = []
                st.rerun()

    # ── LOOP OUTPUT ──
    with centre_tabs[1]:
        st.markdown("### 🔄 CodeAct Loop")

        phase = st.session_state.phase

        # IDLE
        if phase == "idle":
            st.info("Use the Loop tab on the left to start a new goal.")

        # ANALYZE
        elif phase == "analyze":
            st.markdown("#### 🔵 Analyzing...")
            goal = st.session_state.plan.get("goal","")
            st.info(f"**Goal:** {goal}")

            with st.spinner("🎯 Workflow Director planning..."):
                mem_ctx = get_memory_context()
                result, err = call_brain(
                    AGENTS["Workflow Director"]["system"],
                    f"Goal: {goal}{mem_ctx}",
                    brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl,
                    AGENTS["Workflow Director"].get("temperature", 0.7),
                    AGENTS["Workflow Director"].get("max_tokens", 3000)
                )

            if err:
                st.error(f"Error: {err}")
                st.session_state.phase = "idle"
            else:
                plan_data, parse_err = parse_json(result)
                if plan_data:
                    st.session_state.plan = plan_data
                    st.session_state.plan["goal"] = goal
                    st.session_state.todo = plan_data.get("todo",[])
                    add_memory("Workflow Director", plan_data.get("analysis",""), "analyze")
                    log(f"🔵 Analyzed — {len(st.session_state.todo)} tasks", "analyze")
                else:
                    st.session_state.plan = {"goal":goal,"raw":result,"todo":[]}
                    st.session_state.todo = []
                    log("🔵 Analyzed (text mode)", "analyze")

                st.session_state.loop_count += 1
                st.session_state.phase = "plan"
                st.rerun()

        # PLAN
        elif phase == "plan":
            st.markdown("#### 🟣 Plan — Review and approve")
            plan = st.session_state.plan
            st.info(f"**Goal:** {plan.get('goal','')}")

            # Revenue Machine should behave like one-click run. If it launched this
            # loop, automatically approve the generated plan and continue.
            if st.session_state.get("auto_approve_loop"):
                st.session_state.auto_approve_loop = False
                st.session_state.phase = "execute"
                st.session_state.current_todo = 0
                st.session_state.repair_attempts = 0
                log("✅ Auto-approved Revenue Machine plan", "approve")
                st.rerun()

            if st.session_state.todo:
                for item in st.session_state.todo:
                    emoji = AGENTS.get(item.get("agent",""),{}).get("emoji","🤖")
                    st.markdown(f'<div class="loop-box loop-plan"><strong>#{item.get("id","")} {emoji} {item.get("agent","")}</strong><br><span style="color:#94a3b8">{item.get("task","")}</span><br><small style="color:#334155">→ {item.get("output","")}</small></div>', unsafe_allow_html=True)
            else:
                st.text_area("Plan:", value=plan.get("raw",""), height=150)

            c1, c2 = st.columns(2)
            with c1:
                if st.button("✅ APPROVE", type="primary", use_container_width=True, key="approve_plan"):
                    st.session_state.phase = "execute"
                    st.session_state.current_todo = 0
                    st.session_state.repair_attempts = 0
                    log("✅ Approved", "approve")
                    st.rerun()
            with c2:
                if st.button("❌ REJECT", use_container_width=True, key="reject_plan"):
                    st.session_state.phase = "analyze"
                    log("❌ Rejected — reanalyzing", "warn")
                    st.rerun()

        # EXECUTE
        elif phase == "execute":
            todo = st.session_state.todo
            cur = st.session_state.current_todo

            if todo:
                st.progress(cur / len(todo))
                st.caption(f"Task {cur+1} of {len(todo)}")

                for i, s in enumerate(todo):
                    if i < cur:
                        st.markdown(f'<div class="loop-box loop-done">✅ {s.get("agent")}</div>', unsafe_allow_html=True)
                    elif i == cur:
                        st.markdown(f'<div class="loop-box loop-execute">▶ {s.get("agent")} — Running...</div>', unsafe_allow_html=True)
                    else:
                        st.markdown(f'<div class="loop-box" style="border-left:4px solid #1e293b">⏳ {s.get("agent")}</div>', unsafe_allow_html=True)

                if cur < len(todo):
                    step = todo[cur]
                    raw_name = step.get("agent","")
                    agent_match = None
                    for n, d in AGENTS.items():
                        if raw_name.lower() in n.lower() or n.lower() in raw_name.lower():
                            agent_match = (n, d)
                            break

                    if agent_match:
                        aname_loop, adata = agent_match
                        ctx = get_memory_context()
                        last_ctx = ""
                        if st.session_state.outputs:
                            last_key = list(st.session_state.outputs.keys())[-1]
                            last_val = st.session_state.outputs[last_key]
                            last_ctx = f"\n\nPrevious output:\n{last_val.get('content','')[:600]}"

                        with st.spinner(f"⚡ {aname_loop} executing..."):
                            result, err = call_brain(
                                adata["system"],
                                step.get("task","") + ctx + last_ctx,
                                brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl,
                                adata.get("temperature", 0.7), adata.get("max_tokens", 3000)
                            )

                        if err:
                            st.session_state.plan["repair_context"] = {"error":err,"agent":aname_loop,"task":step.get("task","")}
                            st.session_state.phase = "repair"
                            log(f"🔴 Fault in {aname_loop}", "repair")
                            st.rerun()
                        else:
                            output_key = save_output(aname_loop, result, "loop")
                            add_memory(aname_loop, result, "execute")
                            st.session_state.tasks_done += 1
                            st.session_state.current_todo = cur + 1
                            st.session_state.plan["last_output"] = result
                            st.session_state.plan["last_agent"] = aname_loop
                            log(f"✅ #{cur+1} {aname_loop} done", "success")

                            st.markdown(f'<div class="loop-box loop-done"><strong>✅ {aname_loop}:</strong><br>{result[:500]}{"..." if len(result)>500 else ""}</div>', unsafe_allow_html=True)
                            st.download_button(
                                f"⬇ Download #{cur+1}",
                                data=result,
                                file_name=f"step_{cur+1}_{aname_loop.replace(' ','_')}_{datetime.now().strftime('%H%M%S')}.txt",
                                mime="text/plain",
                                key=f"dl_loop_{cur+1}_{uuid.uuid4().hex[:6]}"
                            )

                            if st.session_state.current_todo >= len(todo):
                                st.session_state.phase = "done"
                                st.rerun()
                            else:
                                st.session_state.phase = "observe"
                                st.rerun()

        # OBSERVE
        elif phase == "observe":
            last_output = st.session_state.plan.get("last_output","")
            last_agent = st.session_state.plan.get("last_agent","")

            with st.spinner("🧪 QA reviewing..."):
                result, err = call_brain(
                    AGENTS["QA Sentinel"]["system"],
                    f"Review output from {last_agent}:\n\n{last_output}",
                    brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl,
                    AGENTS["QA Sentinel"].get("temperature", 0.7),
                    AGENTS["QA Sentinel"].get("max_tokens", 3000)
                )

            if err or not result:
                log(f"⚠️ QA skipped: {err}", "warn")
                st.session_state.phase = "execute"
                st.rerun()
            else:
                qa_data, _ = parse_json(result)
                if qa_data:
                    score = qa_data.get("score",100)
                    passed = qa_data.get("passed",True)
                    trigger = qa_data.get("trigger_repair",False)
                    add_memory("QA Sentinel", f"Score:{score} Passed:{passed}", "observe")

                    c1, c2 = st.columns(2)
                    c1.metric("QA Score", f"{score}/100")
                    c2.metric("Status", "✅ PASS" if passed else "❌ FAIL")

                    if (trigger or not passed) and st.session_state.repair_attempts < st.session_state.max_repairs:
                        st.session_state.fault_count += 1
                        st.session_state.repair_attempts += 1
                        st.session_state.plan["repair_context"] = {
                            "error": qa_data.get("repair_instruction","QA failed"),
                            "agent": last_agent,
                            "task": st.session_state.todo[st.session_state.current_todo-1].get("task","") if st.session_state.current_todo > 0 else "",
                            "bad_output": last_output,
                        }
                        log(f"🔴 QA repair triggered (score:{score})", "repair")
                        st.session_state.phase = "repair"
                    else:
                        log(f"🟢 QA passed (score:{score})", "observe")
                        st.session_state.phase = "execute"
                    st.rerun()
                else:
                    log("🟢 QA done", "observe")
                    st.session_state.phase = "execute"
                    st.rerun()

        # REPAIR
        elif phase == "repair":
            repair_ctx = st.session_state.plan.get("repair_context",{})
            st.markdown(f'<div class="fault-box">🩺 <strong>Self-repair activating...</strong><br>Agent: {repair_ctx.get("agent","")}<br>Issue: {repair_ctx.get("error","")}</div>', unsafe_allow_html=True)

            with st.spinner("🩺 Debug Doctor diagnosing..."):
                result, err = call_brain(
                    AGENTS["Debug Doctor"]["system"],
                    f"Fault in {repair_ctx.get('agent','')}.\nTask: {repair_ctx.get('task','')}\nError: {repair_ctx.get('error','')}\nBad output: {repair_ctx.get('bad_output','')[:400]}\n{get_memory_context()}",
                    brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl,
                    AGENTS["Debug Doctor"].get("temperature", 0.7),
                    AGENTS["Debug Doctor"].get("max_tokens", 3000)
                )

            if err:
                st.error(f"Repair failed: {err}")
                st.session_state.phase = "idle"
            else:
                repair_data, _ = parse_json(result)
                if repair_data:
                    fixed = repair_data.get("fix", result)
                    confidence = repair_data.get("confidence",0)
                    output_key = save_output(f"{repair_ctx.get('agent','')} [REPAIRED]", fixed, "repair")
                    add_memory("Debug Doctor", f"Repaired: {repair_data.get('root_cause','')}", "repair")
                    st.metric("Confidence", f"{confidence}%")
                    st.session_state.plan["last_output"] = fixed
                    log(f"🩺 Repaired ({confidence}%)", "repair")
                    st.session_state.phase = "observe" if repair_data.get("loop_again") else "execute"
                else:
                    output_key = save_output(f"{repair_ctx.get('agent','')} [REPAIRED]", result, "repair")
                    st.session_state.plan["last_output"] = result
                    log("🩺 Repair done", "repair")
                    st.session_state.phase = "observe"
                st.rerun()

        # DONE
        elif phase == "done":
            st.success("🎉 ROOMAN COMPLETE!")
            st.markdown(f"Loops: {st.session_state.loop_count} | Repairs: {st.session_state.fault_count} | Tasks: {st.session_state.tasks_done}")

            if not is_privacy_mode():
                all_out = "\n\n".join([f"{'='*40}\n{v.get('title','')}\n{'='*40}\n{v.get('content','')}" for v in st.session_state.outputs.values()])
                st.download_button(
                    "⬇ Download All Outputs",
                    data=all_out,
                    file_name=f"rooman_complete_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key=f"dl_complete_{uuid.uuid4().hex[:6]}"
                )

                if gh_token and gh_repo:
                    if st.button("💾 Save to GitHub Memory", key="save_gh"):
                        ok, err = save_to_github(all_out, f"rooman_outputs/session_{st.session_state.session_id}.txt", gh_token, gh_repo)
                        if ok:
                            st.success("✅ Saved to GitHub permanently!")
                        else:
                            st.error(f"GitHub error: {err}")
            else:
                st.caption("Always-private mode: exports are disabled.")

            if st.button("🔄 New Goal", type="primary", key="new_goal"):
                for k in ["phase","todo","current_todo","plan","repair_attempts","loop_count","fault_count","tasks_done"]:
                    st.session_state[k] = DEFAULTS[k]
                st.rerun()

    # ── COMPARE ──
    with centre_tabs[2]:
        st.markdown("### ⚔️ Compare Agents")
        st.caption("Run two agents in Single mode, then score and select a winner here.")

        if privacy_mode:
            st.caption("Compare is hidden in always-private mode.")
        else:
            compare_results = st.session_state.get("_last_single_results", [])
            if len(compare_results) < 2:
                st.info("Run a two-agent compare in Single mode first.")
            else:
                left_result, right_result = compare_results[0], compare_results[1]
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"#### {left_result['agent']}")
                    st.markdown(f'<div class="output-box">{left_result["content"]}</div>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f"#### {right_result['agent']}")
                    st.markdown(f'<div class="output-box">{right_result["content"]}</div>', unsafe_allow_html=True)

                if st.button("🧪 Score Winner", type="primary", use_container_width=True, key="score_compare_winner"):
                    judge_prompt = f"""Score these two outputs for business execution quality and revenue impact.\n\nOutput A (agent: {left_result['agent']}):\n{left_result['content'][:7000]}\n\nOutput B (agent: {right_result['agent']}):\n{right_result['content'][:7000]}\n\nReturn ONLY valid JSON:\n{{\n  \"winner\": \"{left_result['agent']} or {right_result['agent']}\",\n  \"scores\": {{\"{left_result['agent']}\": 0, \"{right_result['agent']}\": 0}},\n  \"reason\": \"short reason for winner\",\n  \"money_impact\": \"how the winner is more likely to make money\",\n  \"next_action\": \"single best next action\"\n}}"""
                    with st.spinner("Scoring winner..."):
                        judge_result, judge_err = call_brain(
                            AGENTS["QA Sentinel"]["system"],
                            judge_prompt,
                            brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl,
                            0.05, 1400
                        )

                    if judge_err:
                        st.error(judge_err)
                    else:
                        judge_data, parse_err = parse_json(judge_result)
                        if judge_data:
                            st.session_state["_compare_judgement"] = judge_data
                            log("⚔️ Compare winner scored", "observe")
                        else:
                            st.error("Could not parse score JSON")
                            st.session_state["_compare_judgement_raw"] = judge_result

                verdict = st.session_state.get("_compare_judgement")
                if isinstance(verdict, dict):
                    winner = str(verdict.get("winner", "")).strip()
                    scores = verdict.get("scores", {}) if isinstance(verdict.get("scores", {}), dict) else {}
                    score_left = scores.get(left_result["agent"], "-")
                    score_right = scores.get(right_result["agent"], "-")

                    m1, m2 = st.columns(2)
                    m1.metric(left_result["agent"], score_left)
                    m2.metric(right_result["agent"], score_right)

                    st.success(f"Winner: {winner}")
                    st.markdown(f"**Why:** {verdict.get('reason', '')}")
                    st.markdown(f"**Money Impact:** {verdict.get('money_impact', '')}")
                    st.markdown(f"**Next Action:** {verdict.get('next_action', '')}")

                    winner_result = None
                    for item in compare_results:
                        if item.get("agent", "").strip().lower() == winner.lower():
                            winner_result = item
                            break

                    if winner_result and st.button("💾 Save Winner To Outputs", use_container_width=True, key="save_compare_winner"):
                        save_output(f"Compare Winner: {winner_result['agent']}", winner_result["content"], "single")
                        add_memory("Compare", f"Winner selected: {winner_result['agent']}", "observe")
                        st.success("Winner saved to outputs")

                raw_verdict = st.session_state.get("_compare_judgement_raw")
                if raw_verdict:
                    with st.expander("Raw Score Output"):
                        st.markdown(f'<div class="output-box">{raw_verdict}</div>', unsafe_allow_html=True)

    # ── ALL OUTPUTS ──
    with centre_tabs[3]:
        st.markdown("### 📋 All Outputs")
        st.caption(f"Session: `{st.session_state.session_id}` — {len(st.session_state.outputs)} outputs saved")

        if privacy_mode:
            st.caption("Outputs are hidden in always-private mode.")
        else:
            if st.session_state.outputs:
                all_out = "\n\n".join([f"{'='*40}\n{v.get('title','')}\n{'='*40}\n{v.get('content','')}" for v in st.session_state.outputs.values()])
                st.download_button(
                    "⬇ Download ALL",
                    data=all_out,
                    file_name=f"rooman_all_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                    mime="text/plain",
                    key=f"dl_all_{uuid.uuid4().hex[:6]}"
                )
                st.markdown("---")

                for uid, output in list(st.session_state.outputs.items())[::-1]:
                    with st.expander(f"📄 {output.get('title','Output')} — {output.get('time','')}"):
                        st.markdown(f'<div class="output-box">{output.get("content","")}</div>', unsafe_allow_html=True)
                        st.download_button(
                            "⬇ Download",
                            data=output.get("content",""),
                            file_name=f"{uid}.txt",
                            mime="text/plain",
                            key=f"dl_out_{uid}"
                        )
            else:
                st.info("No outputs yet. Run agents or start a loop.")

# ═══════════════════════════════════════
# RIGHT — MEMORY + LOG
# ═══════════════════════════════════════

with right_col:
    right_tabs = st.tabs(["🧠 Memory", "🎯 Track", "📊 Log"])

    with right_tabs[0]:
        st.markdown("### 🧠 Memory")
        st.caption("Auto-injected into every agent call and saved locally in .rooman_memory.json")

        if is_privacy_mode():
            st.caption("Memory is hidden in always-private mode.")
        else:
            if st.session_state.circular_memory:
                st.caption(f"{len(st.session_state.circular_memory)} memory items loaded")
                for m in reversed(st.session_state.circular_memory[-10:]):
                    icons = {"analyze":"🔵","plan":"🟣","execute":"🟡","observe":"🟢","repair":"🔴","single":"⚪","chat":"💬","preload":"💜"}
                    icon = icons.get(m.get("phase",""),"⚪")
                    st.markdown(f'<div class="mem-box">{icon} <strong>{m["agent"]}</strong> [{m["time"]}]<br>{m["content"][:150]}</div>', unsafe_allow_html=True)

                if st.button("🗑️ Clear Memory", key="clear_mem"):
                    st.session_state.circular_memory = []
                    clear_persistent_memory()
                    st.rerun()
            else:
                st.info("Empty — fills as agents run")

            st.markdown("---")
            mk = st.text_input("Add context:", placeholder="Label", key="mem_key")
            mv = st.text_area("Content:", height=60, key="mem_val")
            if st.button("💾 Save", key="save_mem") and mk and mv:
                add_memory("User", f"{mk}: {mv}", "preload")
                st.success("✅ Saved")
                st.rerun()

    with right_tabs[1]:
        st.markdown("### 🎯 Operator Track")
        st.caption("Tick off non-negotiables as you go. Use Load Focus to get agent help on unfinished items.")

        _daily_items = [
            ("outbound_3", "3 new outbound conversations"),
            ("followups_3", "3 follow-ups on old leads"),
            ("sales_ask_1", "1 direct sales ask"),
            ("proof_asset_1", "1 proof asset posted"),
            ("kpis_updated", "5 KPIs updated"),
        ]
        _weekly_items = [
            ("monday_target", "Monday: pipeline + cash target"),
            ("tue_thu_push", "Tue-Thu: sales and delivery push"),
            ("friday_review", "Friday: KPI review + kill one low-value task"),
            ("saturday_cleanup", "Saturday: system cleanup + content batch"),
            ("sunday_reset", "Sunday: family time + weekly reset"),
        ]

        st.markdown("#### Daily non-negotiables")
        for _k, _lbl in _daily_items:
            st.session_state.operator_daily[_k] = st.checkbox(
                _lbl, value=bool(st.session_state.operator_daily.get(_k, False)), key=f"opd_{_k}"
            )

        st.markdown("#### Weekly rhythm")
        for _k, _lbl in _weekly_items:
            st.session_state.operator_weekly[_k] = st.checkbox(
                _lbl, value=bool(st.session_state.operator_weekly.get(_k, False)), key=f"opw_{_k}"
            )

        _d_done = sum(1 for v in st.session_state.operator_daily.values() if v)
        _w_done = sum(1 for v in st.session_state.operator_weekly.values() if v)
        st.caption(f"Daily {_d_done}/5 complete · Weekly {_w_done}/5 complete")

        if _d_done == 5:
            st.success("All daily non-negotiables done. That's a good day.")
        elif _d_done >= 3:
            st.info(f"{5 - _d_done} item(s) left today. Don't leave without them.")
        else:
            st.warning("Focus. Complete the daily non-negotiables before anything else.")

        _tc1, _tc2 = st.columns(2)
        with _tc1:
            if st.button("Load Focus", use_container_width=True, key="op_load_focus"):
                _open = [lbl for k, lbl in _daily_items if not st.session_state.operator_daily.get(k)]
                _open += [lbl for k, lbl in _weekly_items if not st.session_state.operator_weekly.get(k)]
                _task_list = "\n".join([f"- {i}" for i in _open]) or "- All done — plan tomorrow"
                st.session_state["single_task"] = (
                    "Give me exact execution steps, outreach message templates, and one KPI target "
                    "per action for these unfinished operator tasks today:\n\n" + _task_list
                )
                st.session_state["agent_sel_multi"] = [f"{AGENTS['Workflow Director']['emoji']} Workflow Director"]
                add_memory("Operator Tracker", f"Loaded focus: {_task_list[:120]}", "preload")
                st.success("Loaded into Single → Run it.")
        with _tc2:
            if st.button("Reset Daily", use_container_width=True, key="op_reset_daily"):
                st.session_state.operator_daily = _default_op_daily()
                st.rerun()

        st.markdown("---")
        st.caption("**Red flags** — fix same day if any hit:")
        st.caption("• 90+ min tool tinkering before sales work")
        st.caption("• No follow-up sent")
        st.caption("• No direct offer made")
        st.caption("• Built something nobody asked to buy")

    with right_tabs[2]:
        st.markdown("### 📊 Log")
        icons = {"success":"🟢","plan":"🔵","analyze":"🔵","observe":"🟢","repair":"🔴","fault":"💀","warn":"🟡","start":"🚀","approve":"✅","memory":"🧠","normal":"⚪"}
        if is_privacy_mode():
            st.caption("Logs are hidden in always-private mode.")
        else:
            if st.session_state.log:
                for e in reversed(st.session_state.log[-30:]):
                    st.markdown(f"`{e['time']}` {icons.get(e['type'],'⚪')} {e['msg']}")
            else:
                st.info("No log yet")

            if st.button("🗑️ Clear Log", key="clear_log"):
                st.session_state.log = []
                st.rerun()


# ── Floating operator corner sheet ─────────────────────────────────────────
_float_daily_items = [
    ("outbound_3", "3 outbound convos"),
    ("followups_3", "3 follow-ups"),
    ("sales_ask_1", "1 sales ask"),
    ("proof_asset_1", "1 proof asset"),
    ("kpis_updated", "5 KPIs updated"),
]
_float_weekly_items = [
    ("monday_target", "Mon: pipeline target"),
    ("tue_thu_push", "Tue-Thu: sales push"),
    ("friday_review", "Fri: KPI review"),
    ("saturday_cleanup", "Sat: cleanup + batch"),
    ("sunday_reset", "Sun: family + reset"),
]

_fd = "".join(
    f"<li class='{'op-done' if st.session_state.operator_daily.get(k) else 'op-todo'}'"
    f">{'✅' if st.session_state.operator_daily.get(k) else '○'} {lbl}</li>"
    for k, lbl in _float_daily_items
)
_fw = "".join(
    f"<li class='{'op-done' if st.session_state.operator_weekly.get(k) else 'op-todo'}'"
    f">{'✅' if st.session_state.operator_weekly.get(k) else '○'} {lbl}</li>"
    for k, lbl in _float_weekly_items
)
_fd_n = sum(1 for k, _ in _float_daily_items if st.session_state.operator_daily.get(k))
_fw_n = sum(1 for k, _ in _float_weekly_items if st.session_state.operator_weekly.get(k))

st.markdown(
    f"""
    <div class="operator-float">
        <h5>Operator Sheet</h5>
        <div class="op-progress">Today {_fd_n}/5 &nbsp;·&nbsp; Week {_fw_n}/5</div>
        <h5>Daily</h5><ul>{_fd}</ul>
        <h5>Weekly</h5><ul>{_fw}</ul>
    </div>
    """,
    unsafe_allow_html=True,
)


"""
saas_platform.py — FlowForge: Done-For-You Business Automation & Workflow Services
A complete SaaS platform for selling custom automation/workflow solutions.
"""

import streamlit as st
import sqlite3
import json
import uuid
import hashlib
import os
from datetime import datetime
from pathlib import Path

# ── Optional Stripe ────────────────────────────────────────────────────────────
try:
    import stripe
    STRIPE_AVAILABLE = True
except ImportError:
    STRIPE_AVAILABLE = False

# ── Config ─────────────────────────────────────────────────────────────────────
DB_PATH = Path(__file__).with_name("saas_platform.db")
APP_NAME = "FlowForge"
APP_TAGLINE = "Business Automation & Workflow Solutions"


def get_secret(key, fallback=""):
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, fallback)


STRIPE_SECRET_KEY = get_secret("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE = get_secret("STRIPE_PUBLISHABLE_KEY")
ADMIN_PASSWORD_HASH = get_secret(
    "ADMIN_PASSWORD_HASH", hashlib.sha256(b"admin1234").hexdigest()
)
APP_BASE_URL = get_secret("APP_BASE_URL", "http://localhost:8501")

if STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

# ── Database ───────────────────────────────────────────────────────────────────

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS inquiries (
            id          TEXT PRIMARY KEY,
            created_at  TEXT,
            name        TEXT,
            email       TEXT,
            company     TEXT,
            phone       TEXT,
            bottleneck  TEXT,
            hours_saved TEXT,
            tasks       TEXT,
            budget      TEXT,
            notes       TEXT,
            quote_total REAL,
            quote_pkg   TEXT,
            status      TEXT DEFAULT 'new'
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS projects (
            id           TEXT PRIMARY KEY,
            inquiry_id   TEXT,
            created_at   TEXT,
            client_name  TEXT,
            client_email TEXT,
            package      TEXT,
            status       TEXT DEFAULT 'pending',
            progress     INTEGER DEFAULT 0,
            notes        TEXT,
            deliverables TEXT,
            access_token TEXT UNIQUE
        )
        """
    )
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS payments (
            id             TEXT PRIMARY KEY,
            inquiry_id     TEXT,
            created_at     TEXT,
            amount         REAL,
            currency       TEXT DEFAULT 'usd',
            stripe_session TEXT,
            status         TEXT DEFAULT 'pending'
        )
        """
    )
    conn.commit()
    conn.close()


def db_conn():
    return sqlite3.connect(DB_PATH)


# ── Pricing ────────────────────────────────────────────────────────────────────

PACKAGES = {
    "Starter": {
        "price": 2500,
        "desc": "1–2 core workflow automations to eliminate your biggest bottleneck.",
        "includes": [
            "1 automated workflow (email, data, or CRM)",
            "Custom-built for your existing tools",
            "2 rounds of revisions",
            "30-day support window",
            "Setup documentation",
        ],
        "color": "#06b6d4",
        "timeline": "1–2 weeks",
    },
    "Growth": {
        "price": 5500,
        "desc": "3–4 workflow automations plus branded design assets.",
        "includes": [
            "Up to 4 automated workflows",
            "Email campaign sequences",
            "Branded design asset pack",
            "Customer service automation",
            "3 rounds of revisions",
            "60-day support window",
            "Video walkthrough",
        ],
        "color": "#6366f1",
        "timeline": "2–4 weeks",
    },
    "Enterprise": {
        "price": 9500,
        "desc": "Complete business automation suite — end-to-end.",
        "includes": [
            "Unlimited workflow automations",
            "Full email marketing system",
            "Full design asset library",
            "Customer service & chatbot automation",
            "CRM & reporting setup",
            "Unlimited revisions",
            "90-day priority support",
        ],
        "color": "#8b5cf6",
        "timeline": "4–6 weeks",
    },
}

BUDGET_MULT = {
    "Under 2,000": 0.9,
    "2,000 – 5,000": 1.0,
    "5,000 – 10,000": 1.0,
    "10,000+": 1.0,
    "Not sure yet": 1.0,
}


def calculate_quote(bottleneck: list, hours_saved: str, budget: str) -> dict:
    score = len(bottleneck)
    if hours_saved in ("11–20 hours", "20+ hours"):
        score += 1
    if budget in ("5,000 – 10,000", "10,000+"):
        score += 1
    if score <= 2:
        pkg_name = "Starter"
    elif score <= 4:
        pkg_name = "Growth"
    else:
        pkg_name = "Enterprise"
    pkg = PACKAGES[pkg_name]
    price = pkg["price"] * BUDGET_MULT.get(budget, 1.0)
    return {**pkg, "package": pkg_name, "price": price}


# ── Page routing ───────────────────────────────────────────────────────────────

def goto(page: str, **kwargs):
    st.session_state["page"] = page
    for k, v in kwargs.items():
        st.session_state[k] = v
    st.rerun()


# ── CSS ────────────────────────────────────────────────────────────────────────

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #050816; color: #f1f5f9; }
#MainMenu { visibility: hidden; }
footer    { visibility: hidden; }
header    { visibility: hidden; }
.block-container { padding: 0 !important; max-width: 100% !important; }
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #0a0f1e; }
::-webkit-scrollbar-thumb { background: #334155; border-radius: 3px; }

/* --- Cards --- */
.glass-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 16px; padding: 2rem;
    backdrop-filter: blur(12px);
}
.glass-card-sm {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 12px; padding: 1.25rem 1.5rem;
    backdrop-filter: blur(8px);
}

/* --- Hero --- */
.hero-section {
    min-height: 92vh;
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    text-align: center; padding: 5rem 2rem;
    background:
        radial-gradient(ellipse 80% 50% at 50% -10%, rgba(99,102,241,.25) 0%, transparent 60%),
        radial-gradient(ellipse 60% 40% at 80% 80%, rgba(6,182,212,.12) 0%, transparent 50%),
        #050816;
}
.hero-badge {
    display: inline-block;
    background: rgba(99,102,241,.15);
    border: 1px solid rgba(99,102,241,.4);
    color: #a5b4fc;
    font-size: .78rem; font-weight: 600;
    letter-spacing: .12em; text-transform: uppercase;
    padding: .45rem 1.2rem; border-radius: 100px; margin-bottom: 1.5rem;
}
.hero-title {
    font-size: clamp(2.2rem, 6vw, 4.2rem);
    font-weight: 800; line-height: 1.12;
    letter-spacing: -.03em; margin-bottom: 1.25rem; color: #fff;
}
.hero-title .accent {
    background: linear-gradient(135deg, #6366f1 0%, #06b6d4 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-sub {
    font-size: 1.15rem; color: #94a3b8; line-height: 1.7;
    max-width: 580px; margin: 0 auto 2.5rem;
}

/* --- Buttons --- */
.stButton > button {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%) !important;
    color: #fff !important; font-weight: 600 !important;
    border: none !important; border-radius: 50px !important;
    padding: .75rem 2rem !important; font-size: .95rem !important;
    box-shadow: 0 0 20px rgba(99,102,241,.3) !important;
    transition: all .2s ease !important; width: 100% !important;
}
.stButton > button:hover {
    box-shadow: 0 0 36px rgba(99,102,241,.55) !important;
    transform: translateY(-1px) !important;
}

/* --- Section --- */
.section { padding: 5rem 2rem; max-width: 1100px; margin: 0 auto; }
.section-title {
    font-size: clamp(1.6rem, 4vw, 2.4rem); font-weight: 700;
    text-align: center; margin-bottom: .75rem; color: #f1f5f9;
}
.section-sub {
    text-align: center; color: #94a3b8; font-size: 1.05rem;
    max-width: 540px; margin: 0 auto 3rem; line-height: 1.65;
}

/* --- Problem cards --- */
.problem-card {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,80,80,.15);
    border-radius: 14px; padding: 1.5rem; text-align: center; height: 100%;
}
.problem-card .icon { font-size: 2rem; margin-bottom: .75rem; }
.problem-card h4 { color: #f87171; font-size: .95rem; font-weight: 600; margin: 0 0 .5rem; }
.problem-card p  { color: #94a3b8; font-size: .88rem; line-height: 1.55; margin: 0; }

/* --- Service cards --- */
.service-card {
    background: rgba(255,255,255,.03);
    border-radius: 14px; padding: 1.75rem;
    border: 1px solid rgba(255,255,255,.07);
    transition: border-color .2s, transform .2s; height: 100%;
}
.service-card:hover { border-color: rgba(99,102,241,.35); transform: translateY(-2px); }
.service-card .icon { font-size: 1.75rem; margin-bottom: 1rem; }
.service-card h4 { color: #f1f5f9; font-size: 1rem; font-weight: 600; margin-bottom: .5rem; }
.service-card p  { color: #94a3b8; font-size: .88rem; line-height: 1.6; margin: 0; }

/* --- Step cards --- */
.step-card {
    display: flex; gap: 1rem; align-items: flex-start;
    padding: 1.25rem 0; border-bottom: 1px solid rgba(255,255,255,.05);
}
.step-num {
    min-width: 2.2rem; height: 2.2rem; border-radius: 50%;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    display: flex; align-items: center; justify-content: center;
    font-size: .85rem; font-weight: 700; color: #fff; flex-shrink: 0;
}
.step-text h4 { color: #f1f5f9; margin: 0 0 .25rem; font-size: .95rem; font-weight: 600; }
.step-text p  { color: #94a3b8; margin: 0; font-size: .87rem; line-height: 1.55; }

/* --- Package cards --- */
.pkg-card {
    background: rgba(255,255,255,.03);
    border-radius: 16px; padding: 2rem;
    border: 1px solid rgba(255,255,255,.07);
    position: relative; transition: all .25s; height: 100%;
}
.pkg-card.recommended {
    border-color: rgba(99,102,241,.45);
    background: rgba(99,102,241,.06);
}
.pkg-card:hover { transform: translateY(-3px); }
.pkg-badge {
    position: absolute; top: -12px; left: 50%;
    transform: translateX(-50%);
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    color: #fff; font-size: .72rem; font-weight: 700;
    padding: .3rem 1rem; border-radius: 100px;
    letter-spacing: .1em; text-transform: uppercase; white-space: nowrap;
}
.pkg-price { font-size: 2.4rem; font-weight: 800; color: #f1f5f9; line-height: 1; margin: .75rem 0 .25rem; }
.pkg-price span { font-size: 1.1rem; color: #94a3b8; }

/* --- Form --- */
.form-section {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 20px; padding: 2.5rem;
    max-width: 720px; margin: 0 auto;
}
.form-step-indicator { display: flex; gap: .5rem; margin-bottom: 2rem; align-items: center; }
.form-step-dot { height: 8px; border-radius: 100px; transition: all .3s; }
.form-step-dot.active   { background: #6366f1; width: 28px; }
.form-step-dot.done     { background: #10b981; width: 8px; }
.form-step-dot.inactive { background: rgba(255,255,255,.1); width: 8px; }

/* --- Streamlit widget overrides --- */
.stTextInput > div > div > input,
.stTextArea  > div > div > textarea,
.stSelectbox > div > div > div {
    background: rgba(255,255,255,.05) !important;
    border: 1px solid rgba(255,255,255,.1) !important;
    color: #f1f5f9 !important; border-radius: 10px !important;
}
.stTextInput > div > div > input:focus,
.stTextArea  > div > div > textarea:focus {
    border-color: rgba(99,102,241,.6) !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,.15) !important;
}
.stMultiSelect > div > div {
    background: rgba(255,255,255,.05) !important;
    border: 1px solid rgba(255,255,255,.1) !important;
    border-radius: 10px !important;
}
div[data-testid="stRadio"] label {
    background: rgba(255,255,255,.03);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 10px; padding: .65rem 1rem;
    cursor: pointer; transition: all .2s; display: block;
    color: #94a3b8 !important;
}

/* --- Metric boxes --- */
.metric-box {
    background: rgba(255,255,255,.04);
    border: 1px solid rgba(255,255,255,.07);
    border-radius: 14px; padding: 1.25rem 1.5rem; text-align: center;
}
.metric-box .metric-num   { font-size: 2.2rem; font-weight: 800; color: #f1f5f9; line-height: 1; }
.metric-box .metric-label { font-size: .82rem; color: #64748b; margin-top: .35rem; text-transform: uppercase; letter-spacing: .06em; }

/* --- Status badges --- */
.status-badge {
    display: inline-block; font-size: .75rem; font-weight: 600;
    padding: .3rem .85rem; border-radius: 100px;
    text-transform: uppercase; letter-spacing: .07em;
}
.status-new         { background: rgba(99,102,241,.15);  color: #a5b4fc; border: 1px solid rgba(99,102,241,.3); }
.status-pending     { background: rgba(251,191,36,.12);  color: #fcd34d; border: 1px solid rgba(251,191,36,.3); }
.status-contacted   { background: rgba(6,182,212,.12);   color: #67e8f9; border: 1px solid rgba(6,182,212,.3); }
.status-quoted      { background: rgba(139,92,246,.15);  color: #c4b5fd; border: 1px solid rgba(139,92,246,.3); }
.status-in_progress { background: rgba(6,182,212,.12);   color: #67e8f9; border: 1px solid rgba(6,182,212,.3); }
.status-completed   { background: rgba(16,185,129,.12);  color: #6ee7b7; border: 1px solid rgba(16,185,129,.3); }
.status-paid        { background: rgba(16,185,129,.12);  color: #6ee7b7; border: 1px solid rgba(16,185,129,.3); }

/* --- Progress bar --- */
.prog-bar-bg   { background: rgba(255,255,255,.07); border-radius: 100px; height: 8px; overflow: hidden; }
.prog-bar-fill { height: 100%; border-radius: 100px; background: linear-gradient(90deg,#6366f1,#06b6d4); transition: width .5s; }

/* --- Nav --- */
.nav-bar {
    position: sticky; top: 0; z-index: 100;
    background: rgba(5,8,22,.88); backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255,255,255,.06);
    padding: .9rem 2rem;
    display: flex; align-items: center; justify-content: space-between;
}
.nav-logo { font-size: 1.2rem; font-weight: 700; color: #f1f5f9; letter-spacing: -.02em; }
.nav-logo .accent {
    background: linear-gradient(135deg, #6366f1, #06b6d4);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}

/* --- Quote highlight --- */
.quote-highlight {
    background: linear-gradient(135deg, rgba(99,102,241,.15), rgba(139,92,246,.1));
    border: 1px solid rgba(99,102,241,.3); border-radius: 16px;
    padding: 2rem; text-align: center;
}
.quote-amount { font-size: 3rem; font-weight: 800; color: #f1f5f9; }
.quote-pkg    { font-size: 1.1rem; color: #a5b4fc; font-weight: 600; margin-top: .25rem; }

/* --- Misc --- */
.divider  { height: 1px; background: rgba(255,255,255,.06); margin: 3rem 0; }
.check-item {
    display: flex; align-items: flex-start; gap: .6rem;
    padding: .5rem 0; font-size: .9rem; color: #cbd5e1;
}
.check-icon { color: #10b981; font-weight: 700; flex-shrink: 0; }
.success-bar {
    background: rgba(16,185,129,.12); border: 1px solid rgba(16,185,129,.3);
    border-radius: 10px; padding: .85rem 1.25rem; color: #6ee7b7; font-size: .9rem; font-weight: 500;
}
.warning-bar {
    background: rgba(251,191,36,.1); border: 1px solid rgba(251,191,36,.3);
    border-radius: 10px; padding: .85rem 1.25rem; color: #fcd34d; font-size: .9rem;
}
.data-table { width: 100%; border-collapse: collapse; font-size: .88rem; }
.data-table th {
    color: #64748b; font-weight: 600; text-transform: uppercase;
    letter-spacing: .07em; font-size: .75rem; padding: .75rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,.06); text-align: left;
}
.data-table td {
    color: #cbd5e1; padding: .9rem 1rem;
    border-bottom: 1px solid rgba(255,255,255,.04); vertical-align: middle;
}
.data-table tr:hover td { background: rgba(255,255,255,.02); }

@media (max-width: 768px) {
    .hero-title { font-size: 2.2rem; }
    .section    { padding: 3rem 1.25rem; }
    .form-section { padding: 1.5rem; }
}
</style>
"""


# ── Shared nav ─────────────────────────────────────────────────────────────────

def render_nav():
    st.markdown(
        f'<div class="nav-bar">'
        f'<div class="nav-logo"><span class="accent">{APP_NAME}</span></div>'
        f'<div style="font-size:.82rem;color:#475569;">{APP_TAGLINE}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )


# ── Landing page ───────────────────────────────────────────────────────────────

def render_landing():
    render_nav()

    st.markdown(
        """
        <div class="hero-section">
            <div class="hero-badge">✦ Done-For-You Business Automation</div>
            <h1 class="hero-title">
                Stop Doing Work<br>
                <span class="accent">Your Business Should Do Itself.</span>
            </h1>
            <p class="hero-sub">
                We build custom automation systems and workflow tools that handle
                the repetitive work — so you can focus on growing your business,
                not running it.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    _, c, _ = st.columns([2, 2, 2])
    with c:
        if st.button("🚀  Fix My Problem — Get a Free Quote", key="hero_cta"):
            goto("intake")
        st.markdown(
            '<p style="text-align:center;font-size:.82rem;color:#475569;margin-top:.4rem;">'
            "No commitment · Custom quote in 24 hours</p>",
            unsafe_allow_html=True,
        )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Problems
    st.markdown(
        '<div class="section">'
        '<h2 class="section-title">Sound Familiar?</h2>'
        '<p class="section-sub">Most business owners lose 10–30 hours a week '
        "to tasks that should run on autopilot. Here's what we fix.</p>"
        "</div>",
        unsafe_allow_html=True,
    )

    problems = [
        ("😩", "Drowning in Emails", "Manually sending follow-ups, campaigns, and replies that should be automatic."),
        ("📋", "Repetitive Admin Work", "Copy-pasting between tools, updating spreadsheets, creating reports by hand."),
        ("🎨", "Slow Design Turnaround", "Waiting days for graphics, social posts, or marketing assets you need now."),
        ("📞", "Customer Service Bottlenecks", "Answering the same questions over and over, chasing responses manually."),
    ]
    for col, (icon, title, desc) in zip(st.columns(4), problems):
        with col:
            st.markdown(
                f'<div class="problem-card"><div class="icon">{icon}</div>'
                f"<h4>{title}</h4><p>{desc}</p></div>",
                unsafe_allow_html=True,
            )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Services
    st.markdown(
        '<div class="section">'
        '<h2 class="section-title">What We Build For You</h2>'
        '<p class="section-sub">Every system is custom-built for your business '
        "— not a template, not a cookie-cutter solution.</p></div>",
        unsafe_allow_html=True,
    )

    services = [
        ("⚙️", "Workflow Automation", "Connect your existing tools and let data move automatically — no manual work needed."),
        ("✉️", "Email Campaigns", "Automated sequences that nurture leads, follow up on enquiries, and keep clients engaged."),
        ("🎨", "Design Assets", "On-brand graphics, social content, and marketing materials produced fast."),
        ("💬", "Customer Service", "Smart response systems that handle FAQs, route enquiries, and keep clients updated."),
    ]
    for col, (icon, title, desc) in zip(st.columns(4), services):
        with col:
            st.markdown(
                f'<div class="service-card"><div class="icon">{icon}</div>'
                f"<h4>{title}</h4><p>{desc}</p></div>",
                unsafe_allow_html=True,
            )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # How it works
    st.markdown(
        '<div class="section"><h2 class="section-title">How It Works</h2>'
        '<p class="section-sub">Simple, straightforward, zero headache.</p></div>',
        unsafe_allow_html=True,
    )
    steps_col, _ = st.columns([3, 2])
    with steps_col:
        for i, (title, desc) in enumerate(
            [
                ("Tell us your problem", "Fill in our quick form. No tech knowledge needed — just describe what's slowing you down."),
                ("Get a custom quote", "We review your needs and send you a clear, honest quote within 24 hours."),
                ("We build it for you", "Your custom automation system is built, tested, and documented by our team."),
                ("You get your time back", "Your new workflows run automatically. You focus on growth, we handle support."),
            ],
            1,
        ):
            st.markdown(
                f'<div class="step-card"><div class="step-num">{i}</div>'
                f'<div class="step-text"><h4>{title}</h4><p>{desc}</p></div></div>',
                unsafe_allow_html=True,
            )

    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # Pricing
    st.markdown(
        '<div class="section"><h2 class="section-title">Investment</h2>'
        '<p class="section-sub">Packages start at $2,500. Final pricing is based on your '
        "specific requirements — fill in the form for your exact quote.</p></div>",
        unsafe_allow_html=True,
    )

    for col, (name, pkg) in zip(st.columns(3), PACKAGES.items()):
        rec = name == "Growth"
        badge = '<div class="pkg-badge">Most Popular</div>' if rec else ""
        rec_cls = "recommended" if rec else ""
        includes_html = "".join(
            f'<div class="check-item"><span class="check-icon">✓</span>{item}</div>'
            for item in pkg["includes"][:4]
        )
        with col:
            st.markdown(
                f'<div class="pkg-card {rec_cls}">{badge}'
                f'<div style="font-size:.8rem;color:{pkg["color"]};font-weight:700;'
                f'text-transform:uppercase;letter-spacing:.1em;">{name}</div>'
                f'<div class="pkg-price">${int(pkg["price"]):,}<span>+</span></div>'
                f'<div style="font-size:.83rem;color:#64748b;margin-bottom:1rem;">{pkg["timeline"]} timeline</div>'
                f'<div style="font-size:.87rem;color:#94a3b8;margin-bottom:1rem;line-height:1.55;">{pkg["desc"]}</div>'
                f"{includes_html}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # Final CTA
    st.markdown(
        '<div class="glass-card" style="text-align:center;max-width:700px;margin:0 auto 4rem;">'
        '<h2 style="font-size:1.9rem;font-weight:700;margin-bottom:.75rem;color:#f1f5f9;">'
        "Ready to get your time back?</h2>"
        '<p style="color:#94a3b8;margin-bottom:1.75rem;line-height:1.6;">'
        "Tell us your biggest bottleneck and we'll build a custom solution — "
        "no jargon, no fluff, just results.</p></div>",
        unsafe_allow_html=True,
    )

    _, c2, _ = st.columns([2, 2, 2])
    with c2:
        if st.button("Get My Free Custom Quote →", key="bottom_cta"):
            goto("intake")

    # Admin link (subtle)
    st.markdown(
        '<div style="text-align:center;margin-top:3rem;margin-bottom:2rem;">'
        '<span style="color:#1e293b;font-size:.75rem;cursor:pointer;" '
        'id="admin-link">Admin</span></div>',
        unsafe_allow_html=True,
    )
    _, ac, _ = st.columns([3, 1, 3])
    with ac:
        if st.button("⚙️ Admin", key="admin_link", help="Owner admin dashboard"):
            goto("admin")


# ── Intake form ────────────────────────────────────────────────────────────────

def render_intake():
    render_nav()
    st.markdown('<div style="padding:2rem 0;"></div>', unsafe_allow_html=True)

    _, col_main, _ = st.columns([1, 3, 1])
    with col_main:
        step = st.session_state.get("intake_step", 1)
        total = 3

        dots = "".join(
            f'<div class="form-step-dot {"active" if s == step else "done" if s < step else "inactive"}"></div>'
            for s in range(1, total + 1)
        )

        st.markdown(
            f'<div class="form-section">'
            f'<div style="font-size:.8rem;color:#64748b;margin-bottom:.4rem;">Step {step} of {total}</div>'
            f'<div class="form-step-indicator">{dots}</div>',
            unsafe_allow_html=True,
        )

        if step == 1:
            _intake_step1()
        elif step == 2:
            _intake_step2()
        elif step == 3:
            _intake_step3()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br><br>", unsafe_allow_html=True)


def _intake_step1():
    st.markdown(
        '<h2 style="color:#f1f5f9;font-size:1.5rem;font-weight:700;margin-bottom:.4rem;">'
        "Let's talk about your business</h2>"
        '<p style="color:#94a3b8;font-size:.92rem;margin-bottom:1.5rem;">'
        "We need a couple of quick details first.</p>",
        unsafe_allow_html=True,
    )
    name    = st.text_input("Your Name *",           value=st.session_state.get("f_name", ""),    placeholder="Jane Smith")
    email   = st.text_input("Email Address *",       value=st.session_state.get("f_email", ""),   placeholder="jane@business.com")
    company = st.text_input("Company / Business Name", value=st.session_state.get("f_company", ""), placeholder="Acme Ltd")
    phone   = st.text_input("Phone (optional)",      value=st.session_state.get("f_phone", ""),   placeholder="+1 555 000 0000")

    if st.button("Continue →", key="step1_next"):
        if not name.strip() or not email.strip():
            st.error("Please fill in your name and email to continue.")
        elif "@" not in email:
            st.error("Please enter a valid email address.")
        else:
            st.session_state.update(f_name=name, f_email=email, f_company=company, f_phone=phone, intake_step=2)
            st.rerun()


def _intake_step2():
    st.markdown(
        '<h2 style="color:#f1f5f9;font-size:1.5rem;font-weight:700;margin-bottom:.4rem;">'
        "What's slowing you down?</h2>"
        '<p style="color:#94a3b8;font-size:.92rem;margin-bottom:1.5rem;">'
        "Select everything that applies — the more you tell us, the better we can tailor your quote.</p>",
        unsafe_allow_html=True,
    )
    options = [
        "📧  Email marketing & follow-ups",
        "⚙️  Manual / repetitive data work",
        "🎨  Slow design & content creation",
        "💬  Customer service & enquiry handling",
        "📊  Reporting & tracking (manual)",
        "🔗  Tools not talking to each other",
        "📅  Scheduling & appointment management",
        "🛒  Sales & checkout process",
    ]
    bottleneck = st.multiselect(
        "What are your biggest bottlenecks? *",
        options,
        default=st.session_state.get("f_bottleneck", []),
        placeholder="Select all that apply…",
    )
    tasks = st.text_area(
        "Describe the tasks taking the most time",
        value=st.session_state.get("f_tasks", ""),
        placeholder="e.g. 'I manually copy data from forms into a spreadsheet every morning…'",
        height=100,
    )
    hours_options = ["Under 5 hours", "5–10 hours", "11–20 hours", "20+ hours", "Not sure"]
    current_hours = st.session_state.get("f_hours", "5–10 hours")
    hours_idx = hours_options.index(current_hours) if current_hours in hours_options else 1
    hours_saved = st.radio(
        "How many hours per week could automation save you?",
        hours_options,
        index=hours_idx,
        horizontal=True,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", key="step2_back"):
            st.session_state["intake_step"] = 1
            st.rerun()
    with c2:
        if st.button("Continue →", key="step2_next"):
            if not bottleneck:
                st.error("Please select at least one bottleneck.")
            else:
                st.session_state.update(f_bottleneck=bottleneck, f_tasks=tasks, f_hours=hours_saved, intake_step=3)
                st.rerun()


def _intake_step3():
    st.markdown(
        '<h2 style="color:#f1f5f9;font-size:1.5rem;font-weight:700;margin-bottom:.4rem;">'
        "Almost done — investment range</h2>"
        '<p style="color:#94a3b8;font-size:.92rem;margin-bottom:1.5rem;">'
        "This helps us match you with the right package. No commitment at this stage. (USD)</p>",
        unsafe_allow_html=True,
    )
    budget_options = ["Under 2,000", "2,000 – 5,000", "5,000 – 10,000", "10,000+", "Not sure yet"]
    current_budget = st.session_state.get("f_budget", "2,000 – 5,000")
    budget_idx = budget_options.index(current_budget) if current_budget in budget_options else 1
    budget = st.radio("What's your approximate budget? *", budget_options, index=budget_idx)
    notes = st.text_area(
        "Anything else you'd like us to know?",
        value=st.session_state.get("f_notes", ""),
        placeholder="Any tools you use, specific deadlines, or other context…",
        height=80,
    )
    c1, c2 = st.columns(2)
    with c1:
        if st.button("← Back", key="step3_back"):
            st.session_state["intake_step"] = 2
            st.rerun()
    with c2:
        if st.button("🚀  Get My Custom Quote", key="step3_submit"):
            st.session_state["f_budget"] = budget
            st.session_state["f_notes"]  = notes
            _submit_inquiry()


def _submit_inquiry():
    inquiry_id = str(uuid.uuid4())[:12]
    bottleneck = st.session_state.get("f_bottleneck", [])
    hours      = st.session_state.get("f_hours", "Not sure")
    budget     = st.session_state.get("f_budget", "Not sure yet")
    quote      = calculate_quote(bottleneck, hours, budget)

    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO inquiries
                (id,created_at,name,email,company,phone,
                 bottleneck,hours_saved,tasks,budget,notes,
                 quote_total,quote_pkg,status)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,'new')
            """,
            (
                inquiry_id,
                datetime.utcnow().isoformat(),
                st.session_state.get("f_name"),
                st.session_state.get("f_email"),
                st.session_state.get("f_company", ""),
                st.session_state.get("f_phone", ""),
                json.dumps(bottleneck),
                hours,
                st.session_state.get("f_tasks", ""),
                budget,
                st.session_state.get("f_notes", ""),
                quote["price"],
                quote["package"],
            ),
        )

    st.session_state["current_inquiry_id"] = inquiry_id
    st.session_state["current_quote"]       = quote
    st.session_state.pop("intake_step", None)
    goto("quote")


# ── Quote page ─────────────────────────────────────────────────────────────────

def render_quote():
    render_nav()
    st.markdown('<div style="padding:2rem 0;"></div>', unsafe_allow_html=True)

    quote      = st.session_state.get("current_quote")
    name       = st.session_state.get("f_name", "there")

    if not quote:
        st.warning("No quote found. Please fill in the form first.")
        if st.button("← Back to Form"):
            goto("intake")
        return

    pkg = PACKAGES[quote["package"]]
    _, col_main, _ = st.columns([1, 4, 1])

    with col_main:
        st.markdown(
            f'<div style="text-align:center;margin-bottom:2.5rem;">'
            f'<div style="font-size:1.8rem;margin-bottom:.5rem;">🎉</div>'
            f'<h1 style="color:#f1f5f9;font-size:2rem;font-weight:700;margin-bottom:.5rem;">'
            f"Here's your custom quote, {name.split()[0]}</h1>"
            f'<p style="color:#94a3b8;font-size:1rem;">'
            f"Based on your answers, here's what we recommend — and what it'll cost.</p></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="quote-highlight">'
            f'<div style="font-size:.82rem;color:#a5b4fc;font-weight:700;text-transform:uppercase;letter-spacing:.1em;margin-bottom:.5rem;">Recommended Package</div>'
            f'<div class="quote-amount">${int(quote["price"]):,}</div>'
            f'<div class="quote-pkg">{quote["package"]} Package</div>'
            f'<div style="font-size:.85rem;color:#64748b;margin-top:.5rem;">{pkg["timeline"]} · One-time investment</div>'
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<br>", unsafe_allow_html=True)

        st.markdown(
            '<div class="glass-card">'
            '<h3 style="color:#f1f5f9;font-size:1.1rem;font-weight:600;margin-bottom:1.25rem;">What\'s included in your package</h3>',
            unsafe_allow_html=True,
        )
        for item in pkg["includes"]:
            st.markdown(
                f'<div class="check-item"><span class="check-icon">✓</span>{item}</div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        bottleneck = st.session_state.get("f_bottleneck", [])
        if bottleneck:
            st.markdown('<div class="glass-card-sm">', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.85rem;color:#64748b;font-weight:600;text-transform:uppercase;letter-spacing:.07em;margin-bottom:.75rem;">Your pain points we\'ll fix</div>',
                unsafe_allow_html=True,
            )
            for b in bottleneck:
                st.markdown(
                    f'<div class="check-item"><span style="color:#6366f1;font-weight:700;">→</span>&nbsp;{b}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(
            '<div class="warning-bar">💡 <strong>What happens next:</strong> After payment, '
            "we'll schedule a 30-minute kick-off call to finalise the details and start building.</div>",
            unsafe_allow_html=True,
        )
        st.markdown("<br>", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Adjust my answers", key="quote_back"):
                goto("intake")
        with c2:
            if st.button(f"✅  Proceed to Checkout — ${int(quote['price']):,}", key="quote_checkout"):
                goto("checkout")

    st.markdown("<br><br>", unsafe_allow_html=True)


# ── Checkout ───────────────────────────────────────────────────────────────────

def render_checkout():
    render_nav()
    st.markdown('<div style="padding:2rem 0;"></div>', unsafe_allow_html=True)

    quote      = st.session_state.get("current_quote")
    inquiry_id = st.session_state.get("current_inquiry_id")
    name       = st.session_state.get("f_name", "")
    email      = st.session_state.get("f_email", "")

    if not quote:
        st.warning("No quote found.")
        if st.button("← Start over"):
            goto("intake")
        return

    _, col_main, _ = st.columns([1, 4, 1])
    with col_main:
        st.markdown(
            '<h1 style="color:#f1f5f9;font-size:1.9rem;font-weight:700;margin-bottom:.25rem;">Secure Checkout</h1>'
            '<p style="color:#94a3b8;font-size:.95rem;margin-bottom:2rem;">Review your order and complete payment.</p>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="glass-card" style="margin-bottom:1.5rem;">'
            f'<div style="font-size:.8rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-bottom:1rem;">Order Summary</div>'
            f'<div style="display:flex;justify-content:space-between;align-items:center;padding:.6rem 0;border-bottom:1px solid rgba(255,255,255,.06);">'
            f'<div><div style="color:#f1f5f9;font-weight:600;">{quote["package"]} Automation Package</div>'
            f'<div style="color:#64748b;font-size:.83rem;">{quote.get("timeline","1-4 weeks")} · {quote.get("desc","Custom build")}</div></div>'
            f'<div style="color:#f1f5f9;font-size:1.1rem;font-weight:700;">${int(quote["price"]):,}</div></div>'
            f'<div style="display:flex;justify-content:space-between;padding-top:.75rem;">'
            f'<span style="color:#94a3b8;font-size:.88rem;">Total due today</span>'
            f'<span style="color:#f1f5f9;font-size:1.35rem;font-weight:800;">${int(quote["price"]):,} USD</span></div></div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'<div class="glass-card-sm" style="margin-bottom:1.5rem;">'
            f'<div style="font-size:.8rem;color:#64748b;text-transform:uppercase;letter-spacing:.08em;font-weight:600;margin-bottom:.75rem;">Your Details</div>'
            f'<div style="color:#cbd5e1;font-size:.9rem;">📧 {email} &nbsp;|&nbsp; 👤 {name}</div></div>',
            unsafe_allow_html=True,
        )

        stripe_ready = STRIPE_AVAILABLE and bool(STRIPE_SECRET_KEY)
        if stripe_ready:
            if st.button(f"💳  Pay ${int(quote['price']):,} with Stripe", key="pay_stripe"):
                _create_stripe_session(inquiry_id, quote, name, email)
        else:
            st.markdown(
                '<div class="warning-bar" style="margin-bottom:1rem;">'
                "⚠️ <strong>Stripe not configured.</strong> "
                "Add <code>STRIPE_SECRET_KEY</code> to Streamlit secrets to enable live payments.</div>",
                unsafe_allow_html=True,
            )
            if st.button("✅  Confirm Order (Test Mode)", key="pay_test"):
                _confirm_order_test(inquiry_id, quote, name, email)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Back to quote", key="checkout_back"):
            goto("quote")

        st.markdown(
            '<div style="display:flex;gap:1.5rem;justify-content:center;margin-top:1.5rem;flex-wrap:wrap;">'
            '<span style="color:#334155;font-size:.8rem;">🔒 Secure payment</span>'
            '<span style="color:#334155;font-size:.8rem;">💳 Stripe powered</span>'
            '<span style="color:#334155;font-size:.8rem;">✅ Money-back guarantee</span>'
            '<span style="color:#334155;font-size:.8rem;">📞 30-min kick-off call included</span></div>',
            unsafe_allow_html=True,
        )

    st.markdown("<br><br>", unsafe_allow_html=True)


def _create_stripe_session(inquiry_id: str, quote: dict, name: str, email: str):
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": f"{quote['package']} Automation Package",
                        "description": quote.get("desc", APP_TAGLINE),
                    },
                    "unit_amount": int(quote["price"]) * 100,
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=email,
            success_url=(
                f"{APP_BASE_URL}?page=confirmation"
                f"&session_id={{CHECKOUT_SESSION_ID}}&inquiry={inquiry_id}"
            ),
            cancel_url=f"{APP_BASE_URL}?page=checkout",
            metadata={"inquiry_id": inquiry_id, "package": quote["package"]},
        )

        with db_conn() as conn:
            conn.execute(
                "INSERT INTO payments (id,inquiry_id,created_at,amount,stripe_session,status) VALUES (?,?,?,?,?,'pending')",
                (str(uuid.uuid4())[:12], inquiry_id, datetime.utcnow().isoformat(), quote["price"], session.id),
            )

        st.markdown(
            f'<meta http-equiv="refresh" content="0; URL={session.url}">',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<a href="{session.url}" target="_self" style="color:#a5b4fc;">Click here if not redirected</a>',
            unsafe_allow_html=True,
        )
    except Exception as exc:
        st.error(f"Payment setup failed: {exc}")


def _confirm_order_test(inquiry_id: str, quote: dict, name: str, email: str):
    token      = str(uuid.uuid4())
    project_id = str(uuid.uuid4())[:12]

    with db_conn() as conn:
        conn.execute(
            """
            INSERT INTO projects
                (id,inquiry_id,created_at,client_name,client_email,
                 package,status,progress,notes,deliverables,access_token)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                project_id, inquiry_id, datetime.utcnow().isoformat(),
                name, email, quote["package"],
                "pending", 0,
                "Kick-off call to be scheduled.",
                json.dumps([]),
                token,
            ),
        )
        conn.execute("UPDATE inquiries SET status='paid' WHERE id=?", (inquiry_id,))
        conn.execute(
            "INSERT INTO payments (id,inquiry_id,created_at,amount,stripe_session,status) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4())[:12], inquiry_id, datetime.utcnow().isoformat(), quote["price"], "TEST_MODE", "paid"),
        )

    st.session_state["access_token"] = token
    st.session_state["project_id"]   = project_id
    goto("confirmation")


# ── Confirmation ───────────────────────────────────────────────────────────────

def render_confirmation():
    render_nav()
    st.markdown('<div style="padding:3rem 0;"></div>', unsafe_allow_html=True)

    # Handle Stripe return
    params = st.query_params
    session_id       = params.get("session_id", "")
    inquiry_id_param = params.get("inquiry", "")

    if session_id and STRIPE_AVAILABLE and STRIPE_SECRET_KEY:
        try:
            sess = stripe.checkout.Session.retrieve(session_id)
            if sess.payment_status == "paid":
                _handle_stripe_success(inquiry_id_param, sess)
        except Exception:
            pass

    name  = st.session_state.get("f_name", "")
    token = st.session_state.get("access_token", "")

    _, col_main, _ = st.columns([1, 4, 1])
    with col_main:
        st.markdown(
            f'<div style="text-align:center;margin-bottom:2.5rem;">'
            f'<div style="font-size:4rem;margin-bottom:1rem;">🎉</div>'
            f'<h1 style="color:#f1f5f9;font-size:2.2rem;font-weight:700;margin-bottom:.75rem;">'
            f'You\'re all set{", " + name.split()[0] if name else ""}!</h1>'
            f'<p style="color:#94a3b8;font-size:1.05rem;line-height:1.65;max-width:520px;margin:0 auto;">'
            f"Your order has been received. We'll be in touch within 24 hours to schedule "
            f"your kick-off call and get started on your custom build.</p></div>",
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="glass-card" style="margin-bottom:1.5rem;">'
            '<h3 style="color:#f1f5f9;font-size:1.05rem;font-weight:600;margin-bottom:1.25rem;">What happens next</h3>',
            unsafe_allow_html=True,
        )
        for icon, title, desc in [
            ("📧", "Check your email", "Confirmation and kick-off details arrive within 1 business day."),
            ("📞", "Kick-off call",    "A 30-minute session to align on goals, tools, and timeline."),
            ("⚙️", "We build",         "Your custom automation solution is built, tested, and documented."),
            ("✅", "You receive",       "Delivered with a walkthrough video and 30+ days of support."),
        ]:
            st.markdown(
                f'<div class="step-card"><div style="font-size:1.5rem;flex-shrink:0;">{icon}</div>'
                f'<div class="step-text"><h4>{title}</h4><p>{desc}</p></div></div>',
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        if token:
            st.markdown(
                f'<div class="success-bar" style="margin-bottom:1rem;">'
                f'✅ <strong>Your portal access token:</strong> '
                f'<code style="color:#a7f3d0;">{token}</code><br>'
                f"<small>Save this — you'll need it to log into your client dashboard.</small></div>",
                unsafe_allow_html=True,
            )
            if st.button("🔐  Go to My Project Dashboard", key="conf_dashboard"):
                goto("client_dashboard")
        else:
            if st.button("🏠  Back to Home", key="conf_home"):
                goto("landing")

    st.markdown("<br><br>", unsafe_allow_html=True)


def _handle_stripe_success(inquiry_id: str, stripe_session):
    with db_conn() as conn:
        existing = conn.execute(
            "SELECT access_token FROM projects WHERE inquiry_id=?", (inquiry_id,)
        ).fetchone()
        if existing:
            st.session_state["access_token"] = existing[0]
            return

        inq = conn.execute(
            "SELECT name, email, quote_pkg, quote_total FROM inquiries WHERE id=?",
            (inquiry_id,),
        ).fetchone()
        if not inq:
            return

        name, email, pkg_name, price = inq
        token      = str(uuid.uuid4())
        project_id = str(uuid.uuid4())[:12]

        conn.execute(
            """
            INSERT INTO projects
               (id,inquiry_id,created_at,client_name,client_email,
                package,status,progress,notes,deliverables,access_token)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
            """,
            (
                project_id, inquiry_id, datetime.utcnow().isoformat(),
                name, email, pkg_name,
                "pending", 0, "Kick-off call to be scheduled.",
                json.dumps([]), token,
            ),
        )
        conn.execute("UPDATE inquiries SET status='paid' WHERE id=?", (inquiry_id,))
        conn.execute(
            "INSERT INTO payments (id,inquiry_id,created_at,amount,stripe_session,status) VALUES (?,?,?,?,?,?)",
            (str(uuid.uuid4())[:12], inquiry_id, datetime.utcnow().isoformat(),
             price, stripe_session.id, "paid"),
        )

    st.session_state["access_token"] = token
    st.session_state["project_id"]   = project_id


# ── Client Dashboard ───────────────────────────────────────────────────────────

def render_client_dashboard():
    render_nav()
    st.markdown('<div style="padding:2rem 0;"></div>', unsafe_allow_html=True)

    if "access_token" not in st.session_state:
        _, col_main, _ = st.columns([1, 3, 1])
        with col_main:
            st.markdown(
                '<div class="glass-card">'
                '<h2 style="color:#f1f5f9;font-size:1.4rem;font-weight:700;margin-bottom:.5rem;">🔐 Client Portal</h2>'
                '<p style="color:#94a3b8;font-size:.9rem;margin-bottom:1.5rem;">'
                "Enter your access token from your order confirmation email.</p></div>",
                unsafe_allow_html=True,
            )
            token_input = st.text_input("Access Token", placeholder="Paste your access token…", type="password")
            if st.button("Access My Dashboard", key="portal_login"):
                with db_conn() as conn:
                    row = conn.execute(
                        "SELECT id FROM projects WHERE access_token=?", (token_input.strip(),)
                    ).fetchone()
                if row:
                    st.session_state["access_token"] = token_input.strip()
                    st.rerun()
                else:
                    st.error("Token not found. Please check your email or contact support.")
        st.markdown("<br><br>", unsafe_allow_html=True)
        return

    token = st.session_state["access_token"]
    with db_conn() as conn:
        row = conn.execute(
            """
            SELECT p.id, p.created_at, p.client_name, p.client_email,
                   p.package, p.status, p.progress, p.notes, p.deliverables,
                   i.bottleneck
            FROM projects p
            JOIN inquiries i ON p.inquiry_id = i.id
            WHERE p.access_token=?
            """,
            (token,),
        ).fetchone()

    if not row:
        st.error("Project not found. Please check your access token.")
        if st.button("← Log out"):
            del st.session_state["access_token"]
            st.rerun()
        return

    p_id, p_created, p_cname, p_cemail, p_pkg, p_status, p_progress, p_notes, p_deliverables, bottleneck_raw = row
    deliverables = json.loads(p_deliverables) if p_deliverables else []
    bottlenecks  = json.loads(bottleneck_raw)  if bottleneck_raw  else []

    _, col_main, _ = st.columns([1, 6, 1])
    with col_main:
        st.markdown(
            f'<div style="margin-bottom:2rem;">'
            f'<h1 style="color:#f1f5f9;font-size:1.9rem;font-weight:700;margin-bottom:.3rem;">'
            f"Welcome back, {p_cname.split()[0]} 👋</h1>"
            f'<p style="color:#64748b;font-size:.9rem;">{p_pkg} Package · Project #{p_id}</p></div>',
            unsafe_allow_html=True,
        )

        status_label = p_status.replace("_", " ").title()
        st.markdown(
            f'<div class="glass-card" style="margin-bottom:1.5rem;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">'
            f'<h3 style="color:#f1f5f9;font-weight:600;margin:0;">Project Status</h3>'
            f'<span class="status-badge status-{p_status}">{status_label}</span></div>'
            f'<div class="prog-bar-bg"><div class="prog-bar-fill" style="width:{p_progress}%;"></div></div>'
            f'<div style="display:flex;justify-content:space-between;margin-top:.5rem;">'
            f'<span style="color:#64748b;font-size:.82rem;">{p_progress}% complete</span>'
            f'<span style="color:#64748b;font-size:.82rem;">Started {p_created[:10]}</span></div></div>',
            unsafe_allow_html=True,
        )

        if p_notes:
            st.markdown(
                f'<div class="glass-card-sm" style="margin-bottom:1.5rem;">'
                f'<div style="font-size:.78rem;color:#6366f1;font-weight:700;text-transform:uppercase;letter-spacing:.08em;margin-bottom:.5rem;">'
                f"Latest Update From The Team</div>"
                f'<p style="color:#cbd5e1;font-size:.9rem;margin:0;line-height:1.6;">{p_notes}</p></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="glass-card" style="margin-bottom:1.5rem;">'
            '<h3 style="color:#f1f5f9;font-weight:600;margin-bottom:1rem;font-size:1rem;">Deliverables</h3>',
            unsafe_allow_html=True,
        )
        if deliverables:
            for d in deliverables:
                st.markdown(f'<div class="check-item"><span class="check-icon">✓</span>{d}</div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div style="color:#475569;font-size:.88rem;padding:1rem 0;text-align:center;">'
                "🔨 Build in progress — deliverables will appear here once ready.</div>",
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)

        if bottlenecks:
            st.markdown('<div class="glass-card-sm" style="margin-bottom:1.5rem;">', unsafe_allow_html=True)
            st.markdown(
                '<div style="font-size:.78rem;color:#64748b;font-weight:600;text-transform:uppercase;'
                'letter-spacing:.08em;margin-bottom:.75rem;">Problems We\'re Solving</div>',
                unsafe_allow_html=True,
            )
            for b in bottlenecks:
                st.markdown(
                    f'<div class="check-item"><span style="color:#6366f1;font-weight:700;">→</span>&nbsp;{b}</div>',
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            '<div class="success-bar" style="margin-bottom:1.5rem;">'
            "📧 <strong>Need an update?</strong> Reply to your order confirmation email "
            "and we'll get back to you within 1 business day.</div>",
            unsafe_allow_html=True,
        )

        if st.button("← Log out", key="client_logout"):
            del st.session_state["access_token"]
            goto("landing")

    st.markdown("<br><br>", unsafe_allow_html=True)


# ── Admin Dashboard ────────────────────────────────────────────────────────────

def render_admin():
    render_nav()
    st.markdown('<div style="padding:2rem 0;"></div>', unsafe_allow_html=True)

    if not st.session_state.get("admin_authed"):
        _, col_main, _ = st.columns([1, 2, 1])
        with col_main:
            st.markdown(
                '<div class="glass-card">'
                '<h2 style="color:#f1f5f9;font-size:1.4rem;font-weight:700;margin-bottom:.5rem;">🛡 Admin Access</h2>'
                '<p style="color:#94a3b8;font-size:.9rem;margin-bottom:1.5rem;">Enter your admin password to continue.</p>'
                "</div>",
                unsafe_allow_html=True,
            )
            pwd = st.text_input("Password", type="password", key="admin_pwd_input")
            if st.button("Log In", key="admin_login"):
                if hashlib.sha256(pwd.encode()).hexdigest() == ADMIN_PASSWORD_HASH:
                    st.session_state["admin_authed"] = True
                    st.rerun()
                else:
                    st.error("Incorrect password.")
            st.markdown(
                "<small style='color:#334155;'>Default password: admin1234 — "
                "override via ADMIN_PASSWORD_HASH secret (SHA-256 hex).</small>",
                unsafe_allow_html=True,
            )
        return

    with db_conn() as conn:
        inquiries = conn.execute("SELECT * FROM inquiries ORDER BY created_at DESC").fetchall()
        projects  = conn.execute("SELECT * FROM projects  ORDER BY created_at DESC").fetchall()
        payments  = conn.execute("SELECT * FROM payments  ORDER BY created_at DESC").fetchall()

    total_revenue = sum(p[3] for p in payments if p[6] == "paid")
    new_inquiries = sum(1 for i in inquiries if i[13] == "new")
    active_proj   = sum(1 for p in projects  if p[6] in ("pending", "in_progress"))

    _, col_main, _ = st.columns([1, 8, 1])
    with col_main:
        st.markdown(
            '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:2rem;">'
            '<h1 style="color:#f1f5f9;font-size:1.9rem;font-weight:700;margin:0;">⚙️ Admin Dashboard</h1></div>',
            unsafe_allow_html=True,
        )

        m1, m2, m3, m4 = st.columns(4)
        for col_m, num, label in [
            (m1, f"${total_revenue:,.0f}", "Total Revenue"),
            (m2, str(len(inquiries)),       "Total Inquiries"),
            (m3, str(new_inquiries),         "New / Unread"),
            (m4, str(active_proj),           "Active Projects"),
        ]:
            with col_m:
                st.markdown(
                    f'<div class="metric-box">'
                    f'<div class="metric-num">{num}</div>'
                    f'<div class="metric-label">{label}</div></div>',
                    unsafe_allow_html=True,
                )

        st.markdown('<div style="height:1.5rem;"></div>', unsafe_allow_html=True)

        tab_inq, tab_proj, tab_pay = st.tabs(["📋  Inquiries", "⚙️  Projects", "💳  Payments"])

        # ── Inquiries ──
        with tab_inq:
            st.markdown("<br>", unsafe_allow_html=True)
            if not inquiries:
                st.info("No inquiries yet.")
            else:
                for row in inquiries:
                    (i_id, i_created, i_name, i_email, i_company, i_phone,
                     i_bottleneck, i_hours, i_tasks, i_budget, i_notes,
                     i_quote_total, i_quote_pkg, i_status) = row

                    bns = json.loads(i_bottleneck) if i_bottleneck else []
                    bns_text = ", ".join(b.split("  ")[-1].strip() for b in bns) if bns else "—"

                    with st.expander(
                        f"📩  {i_name} ({i_email}) — {i_quote_pkg} — ${i_quote_total:,.0f}",
                        expanded=False,
                    ):
                        c1, c2 = st.columns(2)
                        with c1:
                            st.markdown(
                                f'<div class="glass-card-sm">'
                                f'<div style="margin-bottom:.5rem;"><strong style="color:#94a3b8;font-size:.8rem;">CONTACT</strong></div>'
                                f'<div style="color:#cbd5e1;font-size:.9rem;line-height:1.8;">'
                                f"<b>Name:</b> {i_name}<br><b>Email:</b> {i_email}<br>"
                                f"<b>Company:</b> {i_company or '—'}<br>"
                                f"<b>Phone:</b> {i_phone or '—'}<br>"
                                f"<b>Date:</b> {i_created[:10]}</div></div>",
                                unsafe_allow_html=True,
                            )
                        with c2:
                            st.markdown(
                                f'<div class="glass-card-sm">'
                                f'<div style="margin-bottom:.5rem;"><strong style="color:#94a3b8;font-size:.8rem;">QUOTE</strong></div>'
                                f'<div style="color:#cbd5e1;font-size:.9rem;line-height:1.8;">'
                                f"<b>Package:</b> {i_quote_pkg}<br>"
                                f"<b>Amount:</b> ${i_quote_total:,.0f}<br>"
                                f"<b>Budget:</b> {i_budget}<br>"
                                f"<b>Hours saved:</b> {i_hours}<br>"
                                f'<b>Status:</b> <span class="status-badge status-{i_status}">{i_status}</span>'
                                f"</div></div>",
                                unsafe_allow_html=True,
                            )

                        detail_parts = [f'<b style="color:#94a3b8;font-size:.8rem;">BOTTLENECKS:</b><div style="color:#cbd5e1;font-size:.88rem;margin-top:.25rem;">{bns_text}</div>']
                        if i_tasks:
                            detail_parts.append(f'<br><b style="color:#94a3b8;font-size:.8rem;">TASKS:</b><div style="color:#cbd5e1;font-size:.88rem;margin-top:.25rem;">{i_tasks}</div>')
                        if i_notes:
                            detail_parts.append(f'<br><b style="color:#94a3b8;font-size:.8rem;">NOTES:</b><div style="color:#cbd5e1;font-size:.88rem;margin-top:.25rem;">{i_notes}</div>')
                        st.markdown(
                            f'<div class="glass-card-sm" style="margin-top:.75rem;">{"".join(detail_parts)}</div>',
                            unsafe_allow_html=True,
                        )

                        status_opts = ["new", "contacted", "quoted", "paid", "in_progress", "completed"]
                        new_status = st.selectbox(
                            "Update status",
                            status_opts,
                            index=status_opts.index(i_status) if i_status in status_opts else 0,
                            key=f"inq_status_{i_id}",
                        )
                        if st.button("Save status", key=f"save_inq_{i_id}"):
                            with db_conn() as conn:
                                conn.execute("UPDATE inquiries SET status=? WHERE id=?", (new_status, i_id))
                            st.success("Status updated ✓")
                            st.rerun()

        # ── Projects ──
        with tab_proj:
            st.markdown("<br>", unsafe_allow_html=True)
            if not projects:
                st.info("No projects yet.")
            else:
                for row in projects:
                    (p_id, p_inquiry, p_created, p_cname, p_cemail,
                     p_pkg, p_status, p_progress, p_notes, p_deliverables, p_token) = row

                    deliverables = json.loads(p_deliverables) if p_deliverables else []
                    with st.expander(
                        f"⚙️  {p_cname} — {p_pkg} — {p_status.replace('_',' ').title()}",
                        expanded=False,
                    ):
                        st.markdown(
                            f'<div class="glass-card-sm" style="margin-bottom:.75rem;">'
                            f'<div style="color:#cbd5e1;font-size:.9rem;line-height:1.8;">'
                            f"<b>Client:</b> {p_cname} ({p_cemail})<br>"
                            f"<b>Package:</b> {p_pkg}<br>"
                            f"<b>Progress:</b> {p_progress}%<br>"
                            f'<b>Status:</b> <span class="status-badge status-{p_status}">{p_status}</span><br>'
                            f'<b>Portal Token:</b> <code style="color:#a5b4fc;">{p_token}</code>'
                            f"</div></div>",
                            unsafe_allow_html=True,
                        )

                        proj_status_opts = ["pending", "in_progress", "completed"]
                        new_proj_status = st.selectbox(
                            "Status",
                            proj_status_opts,
                            index=proj_status_opts.index(p_status) if p_status in proj_status_opts else 0,
                            key=f"proj_status_{p_id}",
                        )
                        new_progress = st.slider("Progress %", 0, 100, p_progress, key=f"proj_prog_{p_id}")
                        new_notes    = st.text_area("Update / notes for client", value=p_notes or "", key=f"proj_notes_{p_id}", height=80)
                        new_deliv_str = st.text_area(
                            "Deliverables (one per line)",
                            value="\n".join(deliverables),
                            key=f"proj_deliv_{p_id}",
                            height=80,
                        )

                        if st.button("💾  Save changes", key=f"save_proj_{p_id}"):
                            new_deliv = [d.strip() for d in new_deliv_str.splitlines() if d.strip()]
                            with db_conn() as conn:
                                conn.execute(
                                    "UPDATE projects SET status=?,progress=?,notes=?,deliverables=? WHERE id=?",
                                    (new_proj_status, new_progress, new_notes, json.dumps(new_deliv), p_id),
                                )
                            st.success("Project updated ✓")
                            st.rerun()

        # ── Payments ──
        with tab_pay:
            st.markdown("<br>", unsafe_allow_html=True)
            if not payments:
                st.info("No payments recorded yet.")
            else:
                st.markdown(
                    '<table class="data-table"><thead><tr>'
                    "<th>Date</th><th>Amount</th><th>Status</th><th>Stripe Ref</th>"
                    "</tr></thead><tbody>",
                    unsafe_allow_html=True,
                )
                for p in payments:
                    pay_id, pay_inq, pay_date, pay_amt, pay_curr, pay_stripe, pay_status = p
                    st.markdown(
                        f"<tr><td>{pay_date[:10]}</td>"
                        f'<td style="color:#f1f5f9;font-weight:600;">${pay_amt:,.0f}</td>'
                        f'<td><span class="status-badge status-{pay_status}">{pay_status}</span></td>'
                        f'<td style="color:#475569;font-size:.8rem;">{(pay_stripe or "—")[:40]}</td></tr>',
                        unsafe_allow_html=True,
                    )
                st.markdown("</tbody></table>", unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("← Log out", key="admin_logout"):
            del st.session_state["admin_authed"]
            goto("landing")

    st.markdown("<br><br>", unsafe_allow_html=True)


# ── Entry point ────────────────────────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title=f"{APP_NAME} — Business Automation & Workflow Solutions",
        page_icon="⚙️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    init_db()
    st.markdown(CSS, unsafe_allow_html=True)

    # Honour query-param page on first load (e.g. Stripe redirect)
    params = st.query_params
    if "page" in params and "page" not in st.session_state:
        st.session_state["page"] = params["page"]

    page = st.session_state.get("page", "landing")
    {
        "landing":          render_landing,
        "intake":           render_intake,
        "quote":            render_quote,
        "checkout":         render_checkout,
        "confirmation":     render_confirmation,
        "client_dashboard": render_client_dashboard,
        "admin":            render_admin,
    }.get(page, render_landing)()


if __name__ == "__main__":
    main()

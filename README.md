# 🤖 ROOMAN — 100-Year Brain

**AI-powered multi-agent platform for business automation, code generation, and revenue intelligence.**

Built on [Streamlit](https://streamlit.io). Runs locally, on Termux, or free on Streamlit Cloud. Powered by DeepSeek, Ollama, or any local LLM.

---

## What It Does

ROOMAN gives you a team of 13+ specialized AI agents that plan, execute, review, and repair complex tasks autonomously — without writing a single line of code.

| Agent | What It Does |
|-------|-------------|
| 🎯 **Workflow Director** | Breaks big goals into agent tasks and orchestrates execution |
| 🔍 **Research Brain** | Deep research on any topic |
| ⚒️ **Prompt Forge** | Builds precision prompts for any use case |
| 🧪 **QA Sentinel** | Reviews outputs and scores quality |
| 🗂️ **Data Wrangler** | Cleans, transforms, and structures data |
| 🧠 **Memory Guardian** | Manages context and circular memory |
| ⚡ **Apex Coder** | Generates production-ready code |
| 🔬 **Code Reviewer** | Flags bugs, security issues, and performance problems |
| 🧬 **Test Brain** | Writes complete test suites |
| 🩺 **Debug Doctor** | Self-repair engine for broken code |
| 🏛️ **Arch Mind** | Designs scalable system architecture |
| 📖 **Doc Writer** | Creates developer documentation |
| 🚀 **InsForge** | Full-stack backend + deployment scripts |
| 🧠 **Predict Anything** | Revenue, demand, and cash flow forecasting |

---

## Quick Start

```bash
git clone https://github.com/silenttecguy-quagnew/agent-studio-2.git
cd agent-studio-2
pip install -r requirements-2.txt
streamlit run app-2.py
```

See [`QUICKSTART.md`](QUICKSTART.md) for full setup, including Streamlit Cloud deployment and API key configuration.

---

## AI Brain Options

| Brain | Setup | Cost |
|-------|-------|------|
| **DeepSeek API** | Free key from [platform.deepseek.com](https://platform.deepseek.com) | ~Free |
| **Ollama Local** | Install [ollama.ai](https://ollama.ai) | Free |
| **LM Studio** | Install [lmstudio.ai](https://lmstudio.ai) | Free |

---

## Key Features

### 🔁 APOR Loop — Autonomous Execution
The **Loop** tab runs a 5-phase autonomous cycle: **Analyze → Plan → Execute → Observe → Repair**. Give it a goal and let it run.

### 💼 Revenue Machine
Business profile tracking, offer ladder design, 7-day sprint planning, and 30-day revenue machine execution.

### 📊 Predict Anything
Month-by-month forecasts with confidence intervals, risk scenarios, and recommended actions for any business metric.

### 🚀 InsForge — Backend Generator
Describe what you want to build. InsForge returns a database schema, API spec, auth strategy, deployment script, and cost estimate.

### 🎬 Avatar Automation
HeyGen integration for AI avatar video generation from trend research and content scripts.

### 🧠 GitHub Memory
Connect a GitHub repo to persist all agent outputs across sessions.

### ⚡ Always-On Background Engine
Autonomous background automation for lead tracking, KPI collection, and scheduled AI tasks. See [`QUICKSTART.md`](QUICKSTART.md#7-always-on-background-automation) for setup.

---

## Secrets / API Keys

For Streamlit Cloud, add these in **App settings → Secrets**:

```toml
DEEPSEEK_API_KEY = "your_key"
HEYGEN_API_KEY  = "your_key"        # optional — for avatar videos
GITHUB_TOKEN    = "your_token"      # optional — for memory persistence
GITHUB_REPO     = "owner/repo"      # optional — for memory persistence
```

For local use, set them as environment variables or paste directly in the sidebar.

---

## Streamlit Cloud vs Local

| | Streamlit Cloud | Local / Termux |
|--|----------------|----------------|
| **Entry point** | `app.py` | `app-2.py` |
| **Requirements** | `requirements.txt` | `requirements-2.txt` |
| **Run command** | *(set in Cloud settings)* | `streamlit run app-2.py` |

`app.py` is a thin launcher that imports `app-2.py`, ensuring Streamlit Cloud always runs the current build.

**Cloud settings:**
- Main file path: `app.py`
- Requirements file: `requirements.txt`
- Branch: `main`

---

## Workflow Templates

See [`WORKFLOWS.md`](WORKFLOWS.md) for 4 ready-to-use business workflow templates:

1. **Build a Multi-Tenant SaaS from Scratch**
2. **E-Commerce Demand Forecasting + Inventory Optimization**
3. **Financial Risk Dashboard & Cash Flow Planning**
4. **Multi-Client Agency Scaling System**

---

## File Structure

```
agent-studio-2/
├── app.py                  # Streamlit Cloud launcher
├── app-2.py                # Main application (3,000+ lines)
├── requirements.txt        # Streamlit Cloud dependencies
├── requirements-2.txt      # Local dev dependencies
├── automation/
│   └── always_on_engine.py # Autonomous background engine (CLI)
├── QUICKSTART.md           # 5-minute setup guide
└── WORKFLOWS.md            # 4 business workflow templates
```

---

## License

MIT

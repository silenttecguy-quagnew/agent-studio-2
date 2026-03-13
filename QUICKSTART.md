# 🤖 ROOMAN — Quick Start Guide

Get up and running in **5 minutes**. No coding required.

---

## 1. Get the Code & Install (2 minutes)

Open a terminal (or Termux on mobile).

**First time? Clone the repo:**
```bash
git clone https://github.com/silenttecguy-quagnew/agent-studio-2.git
cd agent-studio-2
```

**Already cloned? Just pull latest changes:**
```bash
cd agent-studio-2
git pull
```

**Then install and run:**
```bash
pip install -r requirements-2.txt
streamlit run app-2.py
```

Your browser opens automatically at `http://localhost:8501`.

> **On Termux/tablet:** Run the same commands. Streamlit opens in your browser tab.

---

## 2. Pick Your AI Brain (30 seconds)

In the left sidebar, choose one of three options:

| Brain | What You Need | Cost |
|-------|---------------|------|
| **DeepSeek API** | Free API key from [platform.deepseek.com](https://platform.deepseek.com) | ~Free |
| **Ollama Local** | [ollama.ai](https://ollama.ai) installed locally | Free |
| **LM Studio / Custom** | [lmstudio.ai](https://lmstudio.ai) running locally | Free |

Paste your API key in the sidebar field. That's it.

---

## 3. Use the Agents (30 seconds)

### Option A — Single Agent (quick tasks)
1. Click the **Single** tab in the left panel
2. Pick an agent from the dropdown
3. Type your task in plain English
4. Click **▶ RUN**
5. Download the result

### Option B — Full Loop (complex projects)
1. Click the **Loop** tab in the left panel
2. Type your goal (e.g. *"Build me an inventory system for my shop"*)
3. Click **🚀 START LOOP**
4. ROOMAN automatically plans, executes, reviews, and repairs
5. Download all outputs when done

---

## 4. New Agents: InsForge & Predict Anything

### 🚀 InsForge — Build Backends Automatically
Select **🚀 InsForge** from the agent dropdown and describe what you want to build:

```
"Build a multi-tenant SaaS backend with user accounts,
subscription billing, and a REST API for a task manager"
```

InsForge will return:
- Full database schema (SQL ready to run)
- API endpoints list
- Auth strategy
- **One-click deployment script** (download from sidebar → Operations Dashboard)
- Monthly cost estimate

### 🧠 Predict Anything — Forecast Your Business
Select **🧠 Predict Anything** from the agent dropdown and describe what to forecast:

```
"Forecast revenue for my e-commerce store over the next 12 months.
We currently sell 50 products and have 200 monthly customers."
```

Predict Anything will return:
- Month-by-month predictions with confidence intervals
- Key business insights
- Risk factors and opportunities
- Recommended actions to hit targets

---

## 5. Operations Dashboard

In the sidebar, expand **🚀 Operations Dashboard** to see:
- Latest infrastructure status from InsForge
- Active forecasts from Predict Anything
- One-click deployment script download
- Monthly cost estimates

---

## 6. Save Your Work

- **Download button** appears after every agent run
- **GitHub Memory** (sidebar): Connect your GitHub repo to save all outputs permanently
- All outputs stay in the **📋 Outputs** tab during your session

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `streamlit: command not found` | Run `pip install streamlit` first |
| API key error | Double-check your key has no extra spaces |
| Agent gives empty response | Try a different brain or check your internet connection |
| App won't start | Run `pip install -r requirements-2.txt` again |

---

## You're Ready! 🎉

You don't need to know any code. Just:
1. **Describe** what you want in plain English
2. **Click** the run button
3. **Download** or deploy the results

See `WORKFLOWS.md` for 4 ready-to-use business workflow examples.

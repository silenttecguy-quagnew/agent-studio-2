import streamlit as st
import requests
from datetime import datetime

st.set_page_config(
    page_title="Agent Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main { background-color: #040810; }
    .stApp { background-color: #040810; }
    .agent-card {
        background: #060c16;
        border: 1px solid #0f1d2e;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
    }
    .output-box {
        background: #060c16;
        border: 1px solid #0f1d2e;
        border-radius: 10px;
        padding: 16px;
        white-space: pre-wrap;
        font-family: monospace;
        font-size: 13px;
        color: #94a3b8;
    }
    h1, h2, h3 { color: #00ff94 !important; }
    .stSelectbox label { color: #06b6d4 !important; }
    .stTextInput label { color: #94a3b8 !important; }
    .stTextArea label { color: #94a3b8 !important; }
    div[data-testid="stSidebar"] { background-color: #060c16; }
</style>
""", unsafe_allow_html=True)

# ─── AGENTS ───────────────────────────────────────────────────────────────────

AGENTS = {
    "🎯 Workflow Director": {
        "group": "TASKLET", "role": "ORCHESTRATION",
        "description": "Master coordinator. Reads the task, assigns the right agents in sequence, routes outputs between them.",
        "system": "You are Workflow Director, the master orchestrator. Given any task or goal, produce a clear execution plan: which agents to use, in what order, what inputs each needs, and how outputs connect. Think like a senior project manager. Be decisive and structured.",
        "inputs": "task / goal / constraints",
        "outputs": "execution-plan, agent-queue, dependency-map",
    },
    "🔍 Research Scout": {
        "group": "TASKLET", "role": "RESEARCH",
        "description": "Deep-dives topics and documents. Returns structured briefings ready for downstream agents.",
        "system": "You are Research Scout. Given a topic, URL, or document, extract the most relevant facts, stats, and insights. Return a structured response with: title, key points, data references, and recommended next action. Be thorough and concise.",
        "inputs": "topic / url / document",
        "outputs": "briefing, summary, data-pack",
    },
    "⚒️ Prompt Forge": {
        "group": "TASKLET", "role": "PROMPT ENGINEERING",
        "description": "Takes raw user intent and builds precision-engineered prompts for any agent or model.",
        "system": "You are Prompt Forge. Take raw user intent and craft precise, structured prompts optimised for the target agent or model. Include: optimised prompt, system prompt suggestion, chain recommendation, and complexity estimate. Be surgical and specific.",
        "inputs": "intent / target agent / context",
        "outputs": "optimised-prompt, system-prompt, chain",
    },
    "🧪 QA Sentinel": {
        "group": "TASKLET", "role": "QUALITY ASSURANCE",
        "description": "Reviews any agent output for accuracy, tone, completeness and compliance.",
        "system": "You are QA Sentinel. Review any content or output submitted. Check: accuracy, tone, completeness, consistency, and compliance. Score 0-100. List issues with severity. Provide a corrected version if needed. Be ruthless but fair.",
        "inputs": "agent output / ruleset / brand voice",
        "outputs": "pass-fail, score, annotated output, fixes",
    },
    "🗂️ Data Parser": {
        "group": "TASKLET", "role": "DATA TRANSFORMATION",
        "description": "Converts raw inputs into clean typed schemas for any agent.",
        "system": "You are Data Parser. Transform any raw input into clean, structured data. Detect and fix anomalies. Normalise formats. Return: clean structured output, schema description, anomalies found, and confidence score.",
        "inputs": "csv / json / raw text / api response",
        "outputs": "clean-json, typed-schema, normalised rows",
    },
    "🧠 Memory Keeper": {
        "group": "TASKLET", "role": "CONTEXT MANAGEMENT",
        "description": "Stores, retrieves, and injects persistent context across all agents in a session.",
        "system": "You are Memory Keeper. Manage context across agent interactions. Summarise and store information clearly. When asked to retrieve, return the most relevant context for the current task. Track: decisions made, outputs produced, and key facts.",
        "inputs": "context / session info / key-value pairs",
        "outputs": "retrieved-context, updated-memory, summary",
    },
    "⚡ Apex Coder": {
        "group": "CODE BRAIN", "role": "ELITE CODE AGENT",
        "description": "The best coding agent. Writes production-grade code in any language.",
        "system": "You are Apex Coder, an elite software engineer. Write clean, production-ready, well-documented code. Always explain your approach first. Write tests alongside code when relevant. Flag potential issues proactively. Suggest optimisations. Never produce placeholder or TODO code unless explicitly asked.",
        "inputs": "task / codebase / language / framework",
        "outputs": "code, tests, docs, review",
    },
    "🔬 Code Reviewer": {
        "group": "CODE BRAIN", "role": "REVIEW & CRITIQUE",
        "description": "Deep code review. Checks for bugs, security holes, performance issues and code smells.",
        "system": "You are Code Reviewer. Perform exhaustive code reviews. Check: security vulnerabilities, performance bottlenecks, code smells, anti-patterns, readability, maintainability, and test coverage gaps. Score overall quality 0-100. List issues by severity: critical, high, medium, low. Always provide fix suggestions.",
        "inputs": "code / language / ruleset",
        "outputs": "annotated code, issue list, severity scores, fixes",
    },
    "🧬 Test Brain": {
        "group": "CODE BRAIN", "role": "TEST ENGINEERING",
        "description": "Generates exhaustive test suites — unit, integration, e2e, edge cases.",
        "system": "You are Test Brain. Generate comprehensive test suites for any code or specification. Cover: happy path, edge cases, error states, boundary values, and negative tests. Specify the framework. Estimate coverage percentage. Highlight gaps. Always include test data examples.",
        "inputs": "code / function spec / framework",
        "outputs": "test suite, coverage report, edge cases",
    },
    "🩺 Debug Doctor": {
        "group": "CODE BRAIN", "role": "DIAGNOSIS & FIX",
        "description": "Diagnoses broken code and stack traces. Root cause analysis not surface fixes.",
        "system": "You are Debug Doctor. Diagnose any code error, stack trace, or broken behaviour. Always find the root cause not just the symptom. Provide: root cause explanation, precise fix with code, why the bug occurred, and how to prevent it in future.",
        "inputs": "error message / stack trace / code / logs",
        "outputs": "root cause, fix, explanation, prevention advice",
    },
    "🏛️ Arch Mind": {
        "group": "CODE BRAIN", "role": "SYSTEM ARCHITECTURE",
        "description": "Designs scalable system architectures. Picks the right patterns, databases and tech stack.",
        "system": "You are Arch Mind. Design robust, scalable system architectures. Consider: scale requirements, cost, team size, latency, and existing stack. Produce: architecture overview, tech stack with reasoning, component breakdown, data flow, key tradeoffs, and infrastructure recommendations.",
        "inputs": "requirements / scale / existing stack",
        "outputs": "architecture plan, tech stack, tradeoffs",
    },
    "📖 Doc Writer": {
        "group": "CODE BRAIN", "role": "DOCUMENTATION",
        "description": "Transforms code and specs into developer-grade docs. READMEs, API docs, guides.",
        "system": "You are Doc Writer. Produce clear, comprehensive developer documentation from any code, spec, or architecture. Match tone to audience. Always include: overview, setup instructions, usage examples, and API reference where relevant.",
        "inputs": "code / architecture / api spec",
        "outputs": "readme, api docs, inline comments, guide",
    },
}

# ─── SESSION STATE ────────────────────────────────────────────────────────────

if "log" not in st.session_state:
    st.session_state.log = []
if "outputs" not in st.session_state:
    st.session_state.outputs = {}

# ─── API CALLS ────────────────────────────────────────────────────────────────

def call_deepseek(system, message, api_key):
    try:
        res = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={
                "model": "deepseek-chat",
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": message}],
                "max_tokens": 2000, "temperature": 0.7,
            },
            timeout=60
        )
        data = res.json()
        if "error" in data:
            return f"Error: {data['error']['message']}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"DeepSeek error: {str(e)}"

def call_ollama(system, message, endpoint, model):
    try:
        res = requests.post(
            f"{endpoint.rstrip('/')}/api/chat",
            json={
                "model": model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": message}],
                "stream": False,
            },
            timeout=120
        )
        return res.json().get("message", {}).get("content", "No response.")
    except Exception as e:
        return f"Ollama error: {str(e)}"

def call_openai_compatible(system, message, api_key, base_url, model):
    try:
        res = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "system", "content": system}, {"role": "user", "content": message}],
                "max_tokens": 2000,
            },
            timeout=120
        )
        data = res.json()
        if "error" in data:
            return f"Error: {data['error']['message']}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"API error: {str(e)}"

# ─── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("# ⚡ AGENT STUDIO")
    st.markdown("### 🧠 Brain Connection")

    brain = st.radio("Select Brain", ["DeepSeek API", "Ollama Local", "LM Studio / Custom"])

    api_key = ""
    ollama_endpoint = "http://localhost:11434"
    ollama_model = "llama3"
    custom_url = ""
    custom_model = ""

    if brain == "DeepSeek API":
        api_key = st.text_input("DeepSeek API Key", type="password", placeholder="sk-...")
        st.caption("Key stays private in your session only")

    elif brain == "Ollama Local":
        ollama_endpoint = st.text_input("Ollama Endpoint", value="http://localhost:11434")
        ollama_model = st.text_input("Model", value="llama3", placeholder="llama3 / qwen3 / mistral")
        st.caption("✅ Free — no API key needed")

    elif brain == "LM Studio / Custom":
        custom_url = st.text_input("API Base URL", placeholder="http://localhost:1234/v1")
        api_key = st.text_input("API Key (if needed)", type="password", placeholder="optional")
        custom_model = st.text_input("Model name", placeholder="qwen3 / llama3 etc")
        st.caption("✅ Works with LM Studio, Qwen, any OpenAI-compatible API")

    st.markdown("---")
    st.markdown("### 🤖 Select Agent")

    groups = {"TASKLET": [], "CODE BRAIN": []}
    for name, data in AGENTS.items():
        groups[data["group"]].append(name)

    st.markdown("**◆ TASKLET AGENTS**")
    agent_name = st.selectbox("", list(AGENTS.keys()), label_visibility="collapsed")

    st.markdown("---")
    agent = AGENTS[agent_name]
    st.markdown(f"**Role:** `{agent['role']}`")
    st.markdown(f"**Inputs:** {agent['inputs']}")
    st.markdown(f"**Outputs:** {agent['outputs']}")

# ─── MAIN AREA ────────────────────────────────────────────────────────────────

st.markdown(f"## {agent_name}")
st.markdown(f"*{agent['description']}*")
st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    task = st.text_area(
        "Give this agent a task",
        height=150,
        placeholder=f"Tell {agent_name} what to do...\n\nExample: Review this Python function for bugs and performance issues:\n\ndef add(a, b):\n    return a + b"
    )

    run = st.button(f"▶ RUN {agent_name}", type="primary", use_container_width=True)

    if run:
        if not task.strip():
            st.warning("Give the agent a task first.")
        else:
            with st.spinner(f"{agent_name} is thinking..."):
                timestamp = datetime.now().strftime("%H:%M:%S")

                if brain == "DeepSeek API":
                    if not api_key:
                        st.error("Add your DeepSeek API key in the sidebar.")
                    else:
                        result = call_deepseek(agent["system"], task, api_key)
                        st.session_state.outputs[agent_name] = result
                        st.session_state.log.append(f"[{timestamp}] ✓ {agent_name} — complete")

                elif brain == "Ollama Local":
                    result = call_ollama(agent["system"], task, ollama_endpoint, ollama_model)
                    st.session_state.outputs[agent_name] = result
                    st.session_state.log.append(f"[{timestamp}] ✓ {agent_name} — complete")

                elif brain == "LM Studio / Custom":
                    if not custom_url:
                        st.error("Add your API base URL in the sidebar.")
                    else:
                        result = call_openai_compatible(agent["system"], task, api_key, custom_url, custom_model)
                        st.session_state.outputs[agent_name] = result
                        st.session_state.log.append(f"[{timestamp}] ✓ {agent_name} — complete")

    if agent_name in st.session_state.outputs:
        st.markdown("### ✅ Output")
        st.markdown(f'<div class="output-box">{st.session_state.outputs[agent_name]}</div>', unsafe_allow_html=True)
        st.download_button(
            "⬇ Download Output",
            data=st.session_state.outputs[agent_name],
            file_name=f"{agent_name.replace(' ', '_')}_output.txt",
            mime="text/plain"
        )

with col2:
    st.markdown("### 📊 Execution Log")
    if st.session_state.log:
        log_text = "\n".join(st.session_state.log[-20:])
        st.code(log_text, language=None)
    else:
        st.caption("No executions yet.")

    if st.button("⟳ Clear Log", use_container_width=True):
        st.session_state.log = []
        st.rerun()

    st.markdown("### 📋 All Outputs")
    if st.session_state.outputs:
        for name, output in st.session_state.outputs.items():
            with st.expander(name):
                st.write(output[:300] + "..." if len(output) > 300 else output)
    else:
        st.caption("No outputs yet.")

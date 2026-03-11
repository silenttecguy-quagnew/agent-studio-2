import streamlit as st
import requests
import json
from datetime import datetime
import uuid

# ─── SECRETS ──────────────────────────────────────────────────────────────────
def get_secret(key, fallback=""):
    try:
        return st.secrets[key]
    except:
        return fallback

DEEPSEEK_KEY_DEFAULT = get_secret("DEEPSEEK_API_KEY")
HEYGEN_KEY_DEFAULT = get_secret("HEYGEN_API_KEY")
GITHUB_TOKEN_DEFAULT = get_secret("GITHUB_TOKEN")
GITHUB_REPO_DEFAULT = get_secret("GITHUB_REPO", "")  # format: username/reponame

st.set_page_config(page_title="ROOMAN", page_icon="🤖", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #040810; }
    div[data-testid="stSidebar"] { background-color: #060c16; border-right: 1px solid #0f1d2e; }
    h1,h2,h3 { color: #00ff94 !important; }
    .loop-box { background:#060c16; border:1px solid #0f1d2e; border-radius:10px; padding:14px; margin:6px 0; font-family:monospace; font-size:12px; color:#94a3b8; }
    .loop-analyze { border-left:4px solid #38bdf8; }
    .loop-plan    { border-left:4px solid #a855f7; }
    .loop-execute { border-left:4px solid #f59e0b; }
    .loop-observe { border-left:4px solid #00ff94; }
    .loop-repair  { border-left:4px solid #f43f5e; }
    .loop-done    { border-left:4px solid #00ff94; background:#0a1a12; }
    .mem-box { background:#060c16; border:1px solid #0f1d2e; border-radius:8px; padding:10px; margin:4px 0; font-size:11px; color:#64748b; }
    .todo-done { color:#00ff94; text-decoration:line-through; padding:4px; display:block; }
    .todo-active { color:#f59e0b; font-weight:bold; padding:4px; display:block; }
    .todo-pending { color:#334155; padding:4px; display:block; }
    .fault-box { background:#1a0608; border:1px solid #f43f5e; border-radius:8px; padding:12px; margin:6px 0; }
    .output-box { background:#060c16; border:1px solid #0f1d2e; border-radius:10px; padding:14px; white-space:pre-wrap; font-family:monospace; font-size:12px; color:#94a3b8; max-height:380px; overflow-y:auto; }
    .heygen-box { background:#060c16; border:2px solid #00ff94; border-radius:12px; padding:16px; margin:8px 0; }
    .brain-panel { background:#060c16; border:1px solid #0f1d2e; border-radius:12px; padding:16px; height:500px; overflow-y:auto; }
    .chat-user { background:#0f2027; border-radius:8px; padding:10px; margin:6px 0; color:#94a3b8; }
    .chat-ai { background:#0a1a12; border-left:3px solid #00ff94; border-radius:8px; padding:10px; margin:6px 0; color:#94a3b8; }
    .phase-active { background:#0f1d2e; border:1px solid #00ff94; border-radius:6px; padding:4px 8px; color:#00ff94; font-weight:bold; }
    .phase-inactive { color:#334155; padding:4px 8px; }
</style>
""", unsafe_allow_html=True)

# ─── AGENTS ───────────────────────────────────────────────────────────────────

AGENTS = {
    "Workflow Director": {
        "emoji":"🎯", "group":"TASKLET", "role":"ORCHESTRATION",
        "description":"Master orchestrator. Decomposes goals into todo.md steps.",
        "system":"""You are Workflow Director for ROOMAN.
Decompose any goal into ordered steps. Return ONLY this JSON:
{
  "goal": "what we are building",
  "analysis": "what this requires and why",
  "todo": [
    {"id": 1, "agent": "Apex Coder", "task": "specific task", "output": "what this produces"}
  ],
  "self_repair_triggers": ["what would cause a retry"],
  "notes": "context"
}
Available agents: Research Scout, Prompt Forge, QA Sentinel, Data Parser, Memory Keeper, Apex Coder, Code Reviewer, Test Brain, Debug Doctor, Arch Mind, Doc Writer.
Return ONLY valid JSON. No text outside JSON.""",
    },
    "Research Scout": {
        "emoji":"🔍", "group":"TASKLET", "role":"RESEARCH",
        "description":"Deep research on any topic.",
        "system":"You are Research Scout inside ROOMAN. Research any topic thoroughly. Return key facts, insights, data points, and actionable next steps. Be specific.",
    },
    "Prompt Forge": {
        "emoji":"⚒️", "group":"TASKLET", "role":"PROMPT ENGINEERING",
        "description":"Builds precision prompts.",
        "system":"You are Prompt Forge inside ROOMAN. Craft precise optimised prompts for any target. Return the optimised prompt, system prompt, and usage notes.",
    },
    "QA Sentinel": {
        "emoji":"🧪", "group":"TASKLET", "role":"QUALITY ASSURANCE",
        "description":"Reviews every output. Scores it.",
        "system":"""You are QA Sentinel inside ROOMAN.
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
        "system":"You are Data Parser inside ROOMAN. Clean and structure any raw data. Fix anomalies. Return clean structured output with schema and confidence score.",
    },
    "Memory Keeper": {
        "emoji":"🧠", "group":"TASKLET", "role":"CIRCULAR MEMORY",
        "description":"Manages circular memory. Never loses context.",
        "system":"You are Memory Keeper inside ROOMAN. Maintain the 100-year brain. Summarise and store all decisions, outputs, and context. Return relevant context for the current task.",
    },
    "Apex Coder": {
        "emoji":"⚡", "group":"CODE BRAIN", "role":"ELITE CODE AGENT",
        "description":"Writes production code. No shortcuts.",
        "system":"""You are Apex Coder inside ROOMAN.
Write complete production-ready code. Rules:
1. Always explain your approach first
2. Write COMPLETE working code — no placeholders, no TODOs
3. Include error handling
4. Flag anything that could cause issues
5. If given context from previous steps, build on it
End every response with: OBSERVE: [what to check to confirm this worked]""",
    },
    "Code Reviewer": {
        "emoji":"🔬", "group":"CODE BRAIN", "role":"REVIEW & CRITIQUE",
        "description":"Reviews code for bugs, security, performance.",
        "system":"""You are Code Reviewer inside ROOMAN.
Review code exhaustively. Return JSON:
{"score":85,"passed":true,"critical_issues":[],"all_issues":[],"fixed_code":"improved code","trigger_repair":false}""",
    },
    "Test Brain": {
        "emoji":"🧬", "group":"CODE BRAIN", "role":"TEST ENGINEERING",
        "description":"Generates complete test suites.",
        "system":"You are Test Brain inside ROOMAN. Write comprehensive tests: unit, integration, edge cases, error states. Name the framework. Estimate coverage. Flag gaps.",
    },
    "Debug Doctor": {
        "emoji":"🩺", "group":"CODE BRAIN", "role":"SELF-REPAIR",
        "description":"Self-repair engine. Activates on any fault.",
        "system":"""You are Debug Doctor — ROOMAN's self-repair engine.
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
        "system":"You are Arch Mind inside ROOMAN. Design robust scalable architectures. Justify every tech choice. Cover components, data flow, infra, tradeoffs, cost.",
    },
    "Doc Writer": {
        "emoji":"📖", "group":"CODE BRAIN", "role":"DOCUMENTATION",
        "description":"Writes developer-grade docs.",
        "system":"You are Doc Writer inside ROOMAN. Write clear complete documentation. Include overview, setup, usage examples, API reference.",
    },
}

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
    "session_id": str(uuid.uuid4())[:8],
}

for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v if not isinstance(v, (list, dict)) else ([] if isinstance(v, list) else {})

if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

# ─── API FUNCTIONS ────────────────────────────────────────────────────────────

def call_brain(system, message, brain, api_key, ollama_ep="", ollama_mdl="llama3", custom_url="", custom_mdl=""):
    try:
        if brain == "DeepSeek API":
            res = requests.post(
                "https://api.deepseek.com/chat/completions",
                headers={"Content-Type":"application/json","Authorization":f"Bearer {api_key}"},
                json={"model":"deepseek-chat","messages":[{"role":"system","content":system},{"role":"user","content":message}],"max_tokens":3000,"temperature":0.7},
                timeout=90
            )
            data = res.json()
            if "error" in data:
                return None, f"API Error: {data['error']['message']}"
            return data["choices"][0]["message"]["content"], None

        elif brain == "Ollama Local":
            res = requests.post(
                f"{ollama_ep.rstrip('/')}/api/chat",
                json={"model":ollama_mdl,"messages":[{"role":"system","content":system},{"role":"user","content":message}],"stream":False},
                timeout=180
            )
            return res.json().get("message",{}).get("content","No response."), None

        elif brain == "LM Studio / Custom":
            res = requests.post(
                f"{custom_url.rstrip('/')}/chat/completions",
                headers={"Content-Type":"application/json","Authorization":f"Bearer {api_key}"},
                json={"model":custom_mdl,"messages":[{"role":"system","content":system},{"role":"user","content":message}],"max_tokens":3000},
                timeout=180
            )
            data = res.json()
            if "error" in data:
                return None, f"API Error: {data['error']['message']}"
            return data["choices"][0]["message"]["content"], None

    except Exception as e:
        return None, f"Connection error: {str(e)}"

def call_heygen(script, avatar_id, voice_id, api_key):
    """Call HeyGen API to generate a video"""
    try:
        res = requests.post(
            "https://api.heygen.com/v2/video/generate",
            headers={"X-Api-Key": api_key, "Content-Type": "application/json"},
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
        data = res.json()
        if data.get("error"):
            return None, data["error"]
        return data.get("data", {}).get("video_id"), None
    except Exception as e:
        return None, str(e)

def check_heygen_video(video_id, api_key):
    """Check HeyGen video status"""
    try:
        res = requests.get(
            f"https://api.heygen.com/v1/video_status.get?video_id={video_id}",
            headers={"X-Api-Key": api_key},
            timeout=30
        )
        data = res.json()
        return data.get("data", {}), None
    except Exception as e:
        return None, str(e)

def get_heygen_avatars(api_key):
    """Get list of available HeyGen avatars"""
    try:
        res = requests.get(
            "https://api.heygen.com/v2/avatars",
            headers={"X-Api-Key": api_key},
            timeout=30
        )
        data = res.json()
        return data.get("data", {}).get("avatars", []), None
    except Exception as e:
        return [], str(e)

def get_heygen_voices(api_key):
    """Get list of available HeyGen voices"""
    try:
        res = requests.get(
            "https://api.heygen.com/v2/voices",
            headers={"X-Api-Key": api_key},
            timeout=30
        )
        data = res.json()
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

def add_memory(agent, content, phase):
    entry = {
        "time": datetime.now().strftime("%H:%M:%S"),
        "agent": agent, "phase": phase,
        "content": content[:400],
    }
    st.session_state.circular_memory.append(entry)
    if len(st.session_state.circular_memory) > 30:
        st.session_state.circular_memory.pop(0)

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
        api_key = st.text_input("DeepSeek API Key", type="password", value=DEEPSEEK_KEY_DEFAULT, placeholder="sk-...")
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

    st.markdown("---")

    # HeyGen
    with st.expander("🎬 HeyGen Settings"):
        heygen_key = st.text_input("HeyGen API Key", type="password", value=HEYGEN_KEY_DEFAULT, placeholder="paste key here")
        if HEYGEN_KEY_DEFAULT:
            st.success("✅ HeyGen loaded")

    # GitHub memory
    with st.expander("💾 GitHub Memory"):
        gh_token = st.text_input("GitHub Token", type="password", value=GITHUB_TOKEN_DEFAULT, placeholder="ghp_...")
        gh_repo = st.text_input("Repo", value=GITHUB_REPO_DEFAULT, placeholder="username/reponame")
        if GITHUB_TOKEN_DEFAULT:
            st.success("✅ GitHub connected")

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
            elif isinstance(v, list):
                st.session_state[k] = []
            elif isinstance(v, dict):
                st.session_state[k] = {}
            else:
                st.session_state[k] = v
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

    agent_tabs = st.tabs(["Single", "Loop"])

    with agent_tabs[0]:
        sel = st.selectbox("Agent", [f"{d['emoji']} {n}" for n, d in AGENTS.items()], key="agent_sel")
        aname = sel.split(" ",1)[1] if " " in sel else sel
        agent = AGENTS.get(aname, list(AGENTS.values())[0])
        st.caption(f"*{agent['description']}*")

        task = st.text_area("Task:", height=100, placeholder=f"Tell {aname} what to do...", key="single_task")
        use_mem = st.checkbox("Use memory", value=True, key="use_mem")

        if st.button(f"▶ RUN", type="primary", use_container_width=True, key="run_single"):
            if task.strip():
                full = task + (get_memory_context() if use_mem else "")
                with st.spinner(f"Running {aname}..."):
                    result, err = call_brain(agent["system"], full, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl)

                if err:
                    st.error(err)
                else:
                    output_key = save_output(aname, result, "single")
                    add_memory(aname, result, "single")
                    st.session_state.tasks_done += 1
                    log(f"✅ {aname} done", "success")
                    st.session_state["_last_output"] = result
                    st.session_state["_last_agent"] = aname
                    st.rerun()

        if st.session_state.get("_last_output") and st.session_state.get("_last_agent") == aname:
            st.download_button(
                "⬇ Download",
                data=st.session_state["_last_output"],
                file_name=f"{aname.replace(' ','_')}_{datetime.now().strftime('%H%M%S')}.txt",
                mime="text/plain",
                key=f"dl_single_{aname}_{datetime.now().strftime('%H%M%S')}"
            )

    with agent_tabs[1]:
        goal = st.text_area("Goal:", height=80, placeholder="What do you want to build?", key="loop_goal")
        mem_pre = st.text_area("Pre-load context:", height=50, placeholder="Brand voice, business context...", key="loop_mem")

        if st.button("🚀 START LOOP", type="primary", use_container_width=True, key="start_loop"):
            if goal.strip():
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

    hg_script = st.text_area("Script:", height=80, placeholder="Paste avatar script here...", key="hg_script")
    hg_avatar = st.text_input("Avatar ID:", placeholder="avatar_id from HeyGen", key="hg_avatar")
    hg_voice = st.text_input("Voice ID:", placeholder="voice_id from HeyGen", key="hg_voice")

    if st.button("🎬 GENERATE VIDEO", type="primary", use_container_width=True, key="gen_video"):
        hk = heygen_key if 'heygen_key' in dir() else ""
        if not hk:
            st.error("Add HeyGen API key in sidebar settings")
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
                st.session_state[f"video_{video_id}"] = {"status": "processing", "id": video_id}
                st.success(f"✅ Video generating! ID: `{video_id}`")
                log(f"🎬 HeyGen video started: {video_id}", "success")

    # Check video status
    if st.button("🔄 Check Video Status", use_container_width=True, key="check_vid"):
        hk = heygen_key if 'heygen_key' in dir() else ""
        vid_keys = [k for k in st.session_state.keys() if k.startswith("video_")]
        if vid_keys and hk:
            for vk in vid_keys[-3:]:
                vid_data = st.session_state[vk]
                status_data, err = check_heygen_video(vid_data["id"], hk)
                if status_data:
                    status = status_data.get("status","")
                    if status == "completed":
                        url = status_data.get("video_url","")
                        st.success(f"✅ Video ready!")
                        st.markdown(f"[▶ Watch Video]({url})")
                        st.markdown(f"[⬇ Download]({url})")
                    else:
                        st.info(f"Status: {status}")

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

    centre_tabs = st.tabs(["🧠 Brain Chat", "🔄 Loop Output", "📋 Outputs"])

    # ── BRAIN CHAT ──
    with centre_tabs[0]:
        st.markdown("### 🧠 Brain Chat")
        st.caption("Chat directly with your AI brain. Full memory context included.")

        # Chat history display
        st.markdown('<div class="brain-panel">', unsafe_allow_html=True)
        if st.session_state.chat_history:
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
                            full_msg, brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
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
                    brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
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
                                brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
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
                    brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
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
                    brain, api_key, ollama_ep, ollama_mdl, custom_url, custom_mdl
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

            if st.button("🔄 New Goal", type="primary", key="new_goal"):
                for k in ["phase","todo","current_todo","plan","repair_attempts","loop_count","fault_count","tasks_done"]:
                    st.session_state[k] = DEFAULTS[k]
                st.rerun()

    # ── ALL OUTPUTS ──
    with centre_tabs[2]:
        st.markdown("### 📋 All Outputs")
        st.caption(f"Session: `{st.session_state.session_id}` — {len(st.session_state.outputs)} outputs saved")

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
    right_tabs = st.tabs(["🧠 Memory", "📊 Log"])

    with right_tabs[0]:
        st.markdown("### 🧠 Memory")
        st.caption("Auto-injected into every agent call")

        if st.session_state.circular_memory:
            for m in reversed(st.session_state.circular_memory[-10:]):
                icons = {"analyze":"🔵","plan":"🟣","execute":"🟡","observe":"🟢","repair":"🔴","single":"⚪","chat":"💬","preload":"💜"}
                icon = icons.get(m.get("phase",""),"⚪")
                st.markdown(f'<div class="mem-box">{icon} <strong>{m["agent"]}</strong> [{m["time"]}]<br>{m["content"][:150]}</div>', unsafe_allow_html=True)

            if st.button("🗑️ Clear Memory", key="clear_mem"):
                st.session_state.circular_memory = []
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
        st.markdown("### 📊 Log")
        icons = {"success":"🟢","plan":"🔵","analyze":"🔵","observe":"🟢","repair":"🔴","fault":"💀","warn":"🟡","start":"🚀","approve":"✅","memory":"🧠","normal":"⚪"}
        if st.session_state.log:
            for e in reversed(st.session_state.log[-30:]):
                st.markdown(f"`{e['time']}` {icons.get(e['type'],'⚪')} {e['msg']}")
        else:
            st.info("No log yet")

        if st.button("🗑️ Clear Log", key="clear_log"):
            st.session_state.log = []
            st.rerun()


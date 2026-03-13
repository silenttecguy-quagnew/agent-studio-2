# ROOMAN — 100-Year AI Agent Studio

ROOMAN is a multi-agent AI system built with [Streamlit](https://streamlit.io/). It provides a full CodeAct loop (ANALYZE → PLAN → EXECUTE → OBSERVE → REPAIR) powered by DeepSeek, Ollama, or a custom LLM endpoint.

## Quick Start (GitHub Codespaces)

1. Open in Codespaces — dependencies install automatically.
2. The app starts on port **8501** and opens in the preview pane.
3. Enter your API keys in the sidebar and set a goal.

## Manual Setup

```bash
pip install -r requirements.txt
streamlit run app-2.py
```

## Configuration

Set the following in `.streamlit/secrets.toml` (or Codespaces secrets):

| Key | Description |
|-----|-------------|
| `DEEPSEEK_API_KEY` | DeepSeek API key |
| `HEYGEN_API_KEY` | HeyGen API key (optional, for avatar video) |
| `GITHUB_TOKEN` | GitHub PAT for persistent memory storage |
| `GITHUB_REPO` | Target repo for memory (`username/reponame`) |

## Agents

| Agent | Role |
|-------|------|
| Workflow Director | Orchestrates goals into todo steps |
| Research Scout | Deep research on any topic |
| Prompt Forge | Builds precision prompts |
| QA Sentinel | Reviews and scores outputs |
| Data Parser | Cleans and structures raw data |
| Memory Keeper | Manages circular memory |
| Apex Coder | Full-stack code generation |
| Code Reviewer | Reviews code for quality |
| Test Brain | Generates tests |
| Debug Doctor | Diagnoses and fixes bugs |
| Arch Mind | System architecture design |
| Doc Writer | Writes documentation |

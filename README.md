# TEM AI Agent

An AI-driven agent that autonomously controls a Transmission Electron Microscope (TEM).
Supports **Claude** (Anthropic) and **Gemini** (Google) as interchangeable AI backends,
selectable with a single command-line flag.

---

## Repository Layout

```
TEM_code/
│
├── invoke_tem_ai_model.py      ← CANONICAL ENTRY POINT
│
├── config/
│   ├── tools.yaml              ← all 12 tool definitions (add tools here)
│   └── instrument_autoscript.yaml  ← all safety limits (swap per instrument)
│
├── policies/
│   ├── base_policy.py          ← abstract interface for any AI backend
│   ├── claude_policy.py        ← Claude (Anthropic Messages API)
│   └── gemini_policy.py        ← Gemini (Google Generative AI)
│
├── connectors/
│   └── autoscript_connector.py ← wraps autoscript_interface; swap for real TEM
│
├── tem_capabilities.py         ← shared tool execution layer (model-agnostic)
├── tem_agent.py                ← generic agent loop
├── tool_registry.py            ← loads config/tools.yaml
├── instrument_registry.py      ← loads config/instrument_autoscript.yaml
│
├── autoscript_interface.py     ← low-level AutoScript hardware bindings
├── tem_context.txt             ← system prompt / domain rules for the AI
│
├── tests/
│   └── mock_connector.py       ← in-memory fake connector for --dry-run mode
│
│ ── Legacy / integration scripts (require live microscope connection)
├── claude_tem_agent.py         ← original Claude-only agent (now uses registries)
├── ai_policy.py                ← original Claude policy (now uses ToolRegistry)
├── test_claude_policy.py       ← verifies Claude picks a valid tool (no microscope)
├── test_claude_tem_focus.py    ← focus optimization run against simulator
├── test_claude_tem_tomography.py ← tomography tilt series run against simulator
└── workflows.py                ← rule-based policy helpers (model-free)
```

---

## Quickstart

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
export ANTHROPIC_API_KEY="your-anthropic-key"   # required for Claude
export GEMINI_API_KEY="your-gemini-key"          # required for Gemini
export AUTOSCRIPT_HOST="<microscope-ip>"         # required for live runs
export AUTOSCRIPT_PORT="7521"                    # default port
```

> **Never put API keys in a file.** Always export them in your terminal session.

### 3. Run (no microscope needed)

```bash
# Dry-run with Claude — uses an in-memory mock connector, no hardware required
python invoke_tem_ai_model.py --model claude --dry-run

# Dry-run with Gemini
python invoke_tem_ai_model.py --model gemini --dry-run
```

### 4. Run against the AutoScript simulator

```bash
# Focus optimisation with Claude
python invoke_tem_ai_model.py --model claude

# Focus optimisation with Gemini
python invoke_tem_ai_model.py --model gemini

# Custom goal
python invoke_tem_ai_model.py --model claude \
  --goal "Perform a tomography tilt series at -20, 0, and +20 degrees at 4300x magnification"

# Limit iterations
python invoke_tem_ai_model.py --model claude --max-iterations 20
```

---

## Adding a New Tool

1. Add the entry (name, description, JSON schema) to `config/tools.yaml`
2. Add the implementation to `tem_capabilities.py`
3. Add the hardware call to `connectors/autoscript_connector.py`

No changes are needed to `tem_agent.py`, `invoke_tem_ai_model.py`, or any policy file.

---

## Swapping to a Real Instrument

1. Copy `connectors/autoscript_connector.py` → `connectors/real_tem_connector.py`
2. Replace method bodies with the real instrument API calls
3. Copy `config/instrument_autoscript.yaml` → `config/instrument_real.yaml` and update limits
4. Pass `--instrument-config config/instrument_real.yaml` at runtime

---

## Safety Controls

All safety limits are defined in `config/instrument_autoscript.yaml` — not hardcoded:

| Parameter | Limit |
|---|---|
| Defocus change per call | ±5 µm |
| Stage translation per call | ±10 µm (X/Y/Z) |
| Stage tilt per call | ±45° (Alpha/Beta) |
| Acceleration voltage range | 60–300 kV |
| Defocus restoration tolerance (finish) | ±10 nm |

The beam is **always blanked** and the column valve **always closed** on exit,
even if the agent loop raises an exception.

---

## Legacy Integration Scripts

The following scripts require `AUTOSCRIPT_HOST` and `ANTHROPIC_API_KEY` to be set
and a live connection to the AutoScript simulator:

```bash
# Verify Claude selects a valid tool (no microscope needed)
python test_claude_policy.py

# Run focus optimisation end-to-end against the simulator
python test_claude_tem_focus.py

# Run tomography tilt series end-to-end against the simulator
python test_claude_tem_tomography.py
```

> These are **integration scripts**, not automated unit tests. They require
> a running AutoScript server and will make real API calls to Claude.

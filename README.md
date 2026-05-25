# Verified Chain-of-Thought Solver

> LLM reasoning with **Lean4** as a symbolic verifier for GSM8K math problems — an agentic verify-repair pipeline.

## Results

| Metric | Score |
|--------|-------|
| pass@1 (first attempt) | **80%** (40/50) |
| pass@5 (with repair loop) | **94%** (47/50) |
| Avg repair iterations | **2.4** |
| Failed | 6% (3/50) |

## How it works

```
GSM8K problem
     ↓
LLM (Llama 3.3 70B via Groq)
generates Lean4 theorem
     ↓
Lean4 verifier checks it
     ↓
✓ pass → log result
✗ fail → error fed back to LLM → retry (max 5 attempts)
```

The key insight: instead of checking only the final numeric answer, every reasoning step is expressed as a **formal Lean4 theorem** verified by the `omega` tactic — a decision procedure for linear arithmetic. This catches reasoning errors even when the final answer is accidentally correct.

## Architecture

```
pipeline/
├── verifier.py      # calls lean.exe as subprocess, parses errors
├── llm.py           # prompts LLM to generate Lean4 theorems
├── repair_loop.py   # verify → fail → feed error back → retry
└── evaluate.py      # runs on GSM8K subset, logs pass@1 / pass@5
lean/
├── lakefile.toml    # Lean4 project config
└── lean-toolchain   # pins Lean 4.29.1
```

## Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Lean4](https://img.shields.io/badge/Lean4-4.29.1-orange?style=flat)
![Groq](https://img.shields.io/badge/Groq-API-red?style=flat)
![HuggingFace](https://img.shields.io/badge/HuggingFace-GSM8K-yellow?style=flat)

- **Lean 4.29.1** — formal theorem prover (verifier environment)
- **Llama 3.3 70B** via Groq API — LLM proof generator
- **Python** — pipeline orchestration
- **GSM8K** (openai/gsm8k) — benchmark dataset

## Setup

```bash
# 1. Clone
git clone https://github.com/ShardulMore112/lean-gsm8k-verifier.git
cd lean-gsm8k-verifier

# 2. Install Python deps
pip install -r requirements.txt

# 3. Set API key
cp .env.example .env
# edit .env and add your GROQ_API_KEY

# 4. Install Lean4
# Windows: follow https://leanprover.github.io/lean4/doc/setup.html
# Update LEAN_BINARY path in pipeline/verifier.py

# 5. Run evaluation
python pipeline/evaluate.py
```

## Example

**Problem:** Each box holds 12 bottles. If there are 8 boxes, how many bottles in total?

**LLM reasoning:** 8 boxes x 12 bottles = 96 bottles total

**Generated Lean4:**
```lean
theorem solution : 12 * 8 = 96 := by omega
```

**Verifier:** Goals accomplished

## Why Lean4?

Most LLM math pipelines check only the final number. Using Lean4 as a verifier means:
- Every arithmetic step is a **machine-checked proof**
- Errors produce **typed, parseable feedback** the LLM can act on
- The repair loop is grounded in formal logic, not heuristics

## Results log

See `results/results.json` for full per-problem breakdown.
# Verified Chain-of-Thought Solver

> Agentic LLM pipeline that uses **Lean4** as a formal verifier for GSM8K math problems — with an automated verify-repair loop that catches reasoning errors even when the final answer is accidentally correct.

> *LLMs fail at math not because they can't reason, but because they have no external ground truth to fail against. Lean4 changes that.*

---

## Results

| Metric | Lean Pipeline | Baseline (LLM only) |
|---|---|---|
| pass@1 | **84%** (168/200) | 96% (192/200) |
| pass@5 (with repair) | **97%** (194/200) | — |
| Hard failures (5 attempts) | 6 (3%) | 8 (4%) |
| Avg repair iterations | ~1.4 | — |
| Problems baseline missed, Lean fixed | 8 | — |

> Full 500-problem evaluation in progress.

### What the numbers mean

The Lean pipeline and baseline fail on **different problems**. The advantage of Lean is not raw accuracy but **verifiability**: the baseline checks only the final number, while Lean verifies every arithmetic step as a machine-checked proof. A problem where the LLM reaches the right answer via wrong reasoning would pass the baseline but fail Lean — and the repair loop would catch it.

### Failure analysis

All hard failures (5 attempts, unsolved) fall into identifiable categories:

| Problem type | Example | Root cause |
|---|---|---|
| Relative motion | "John drives 60mph, turns around..." | Non-integer time steps (0.5hr) exceed `omega` |
| Fractional rate chaining | "Dana runs 4x faster than walk..." | Multi-step fractional arithmetic |
| Compound interest / percentages | "Price increases by 20% every 2 months..." | Exponentiation not supported by `omega` |
| Implicit unit conversion | "300g bag, 5 servings, 250 cal/serving..." | Implicit division step |

All failures trace to one root cause: **`omega` is a decision procedure for linear integer arithmetic only**. Non-linear, fractional, or exponential reasoning requires `norm_num` or `field_simp` (Mathlib) — a direction for future work.

---

## How it works

```
GSM8K problem
     ↓
LLM (Llama 3.3 70B via OpenRouter)
generates Lean4 theorem + chain-of-thought reasoning
     ↓
Lean4 verifier checks the theorem (omega tactic)
     ↓
pass  → log result
fail  → typed Lean error fed back to LLM → retry (max 5 attempts)
```

The key insight: instead of checking only the final numeric answer, every reasoning step is expressed as a **formal Lean4 theorem** verified by the `omega` tactic. This catches reasoning errors even when the final answer is accidentally correct.

---

## Architecture

```
pipeline/
├── verifier.py      # calls lean.exe as subprocess, parses stdout errors
├── llm.py           # OpenRouter client with 3-key rotation + rate limit handling
├── repair_loop.py   # verify → fail → feed typed error back → retry (max 5)
└── evaluate.py      # checkpoint/resume evaluation, logs pass@1 / pass@5
lean/
├── examples.lean    # representative theorems from the pipeline
├── lakefile.toml    # Lean4 project config
└── lean-toolchain   # pins Lean 4.29.1
results/
└── results.json     # per-problem breakdown: attempts, lean code, reasoning
```

---

## Lean4 examples

Simple theorem (pass@1):
```lean
-- Each box holds 12 bottles. 8 boxes. How many bottles?
theorem solution : 12 * 8 = 96 := by omega
```

Multi-step theorem:
```lean
-- Janet's ducks lay 16 eggs/day. She eats 3, bakes with 4, sells rest at $2.
-- Reasoning: 16 - 3 - 4 = 9 eggs. 9 * 2 = $18
theorem solution : (16 - 3 - 4) * 2 = 18 := by omega
```

Repair loop example (wrong then fixed):
```lean
-- Attempt 1 — REJECTED by Lean:
theorem solution : 180 - (30 * 0 + 80 * 1) = 45 := by omega
-- Error: omega could not prove the goal

-- Attempt 2 — ACCEPTED after repair:
theorem solution : 180 - 15 - 120 = 45 := by omega
```

See `lean/examples.lean` for the full annotated set.

---

## Stack

![Python](https://img.shields.io/badge/Python-3776AB?style=flat&logo=python&logoColor=white)
![Lean4](https://img.shields.io/badge/Lean4-4.29.1-orange?style=flat)
![OpenRouter](https://img.shields.io/badge/OpenRouter-API-blue?style=flat)
![HuggingFace](https://img.shields.io/badge/HuggingFace-GSM8K-yellow?style=flat)

- **Lean 4.29.1** — formal theorem prover (verifier environment)
- **Llama 3.3 70B** via OpenRouter API — LLM proof generator
- **Python** — pipeline orchestration with checkpoint/resume
- **GSM8K** (`openai/gsm8k`) — benchmark dataset

---

## Setup

```bash
# 1. Clone
git clone https://github.com/ShardulMore112/lean-gsm8k-verifier.git
cd lean-gsm8k-verifier

# 2. Install Python deps
pip install -r requirements.txt

# 3. Set API keys
cp .env.example .env
# Add your OpenRouter keys: OPENROUTER_API_KEY_1, _2, _3

# 4. Install Lean4
# Windows: https://leanprover.github.io/lean4/doc/setup.html
# Update LEAN_BINARY path in pipeline/verifier.py

# 5. Run evaluation (resumes from checkpoint if interrupted)
python pipeline/evaluate.py

# 6. Run baseline comparison
python pipeline/baseline.py
```

---

## Why Lean4?

Most LLM math pipelines check only the final number. Using Lean4 as a verifier means:

- **Step-level correctness** — every arithmetic step is machine-checked, not just the final answer
- **Structured error feedback** — failures return typed, parseable Lean errors the LLM can act on directly
- **Deterministic pass/fail** — the repair loop is grounded in formal logic, not heuristics
- **Differentiable failures** — when the system fails, you know exactly why (wrong arithmetic vs wrong formalization vs tactic limitation)

The tradeoff: `omega` handles linear integer arithmetic only. Problems requiring fractions, exponents, or implicit unit conversions fall outside its scope — these are the 3% hard failures.

---

## Limitations and future work

- `omega` tactic covers linear integer arithmetic only — extending to `norm_num` (Mathlib) would handle division and percentages
- Single-theorem formulation may over-simplify multi-step problems — future: chain of theorems per reasoning step
- Evaluated on GSM8K subset — harder benchmarks (MATH, miniF2F) would stress-test the formalization more
- OpenRouter rate limits constrain throughput — 3-key rotation with checkpoint/resume mitigates this

---

## Results log

See `results/results.json` for full per-problem breakdown including per-attempt Lean code, reasoning, and error messages.
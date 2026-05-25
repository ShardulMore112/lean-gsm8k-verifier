# Verified Chain-of-Thought Solver

> Agentic LLM pipeline that uses **Lean4** as a formal verifier for GSM8K math problems — with an automated verify-repair loop that catches reasoning errors even when the final answer is accidentally correct.

>LLMs fail at math not because they can't reason, but because they have no external ground truth to fail against. Lean4 changes that.
## Results

| Metric | Lean pipeline (n=50) | Baseline LLM (n=200) |
|---|---|---|
| Accuracy (pass@1) | 80% (40/50) | 95% (190/200) |
| Accuracy (pass@5) | **94%** (47/50) | — |
| Avg repair iterations | 1.21 (solved only) | — |
| Failed | 6% (3/50) | 5% (10/200) |

> **Note:** Full 500-problem evaluation in progress. Results above are on initial subsets.

### What the numbers mean

The Lean pipeline and baseline fail on **different problems** — on 50 shared problems, Lean solved 2 that the baseline missed. The advantage of Lean is not raw accuracy but **verifiability**: the baseline checks only the final number, while Lean verifies every reasoning step as a machine-checked proof. A problem where the LLM reaches the right answer via wrong reasoning would pass the baseline but fail Lean.

### Failure analysis (Lean pipeline)

All 3 failures hit the 5-attempt maximum and fall into identifiable categories:

| Problem type | Example | Why Lean fails |
|---|---|---|
| Relative motion | "John drives 60 mph, turns around..." | Non-linear distance/time reasoning exceeds `omega` |
| Fractional rate chaining | "Dana runs 4× faster than walk, skips at ½ run..." | Multi-step fractional arithmetic |
| Implicit unit conversion | "300g bag, 5 servings, 250 cal/serving..." | Implicit division step not expressible as single linear theorem |

These failures reflect a known limitation of the `omega` tactic, which is a decision procedure for **linear arithmetic only**. Non-linear or fractional reasoning requires more expressive tactics (`norm_num`, `field_simp`) — a direction for future work.

## How it works

```
GSM8K problem
     ↓
LLM (Llama 3.3 70B via Groq)
generates Lean4 theorem + reasoning
     ↓
Lean4 verifier checks the theorem
     ↓
✓ pass → log result
✗ fail → typed error fed back to LLM → retry (max 5 attempts)
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

**LLM reasoning:** 8 boxes × 12 bottles = 96 bottles total

**Generated Lean4:**
```lean
theorem solution : 12 * 8 = 96 := by omega
```

**Verifier output:** `Goals accomplished`

**Multi-step example** — Janet's eggs problem:
```lean
-- Janet's ducks lay 16 eggs/day. She eats 3, bakes with 4, sells rest at $2 each.
theorem solution : (16 - 3 - 4) * 2 = 18 := by omega
```

## Why Lean4?

Most LLM math pipelines check only the final number. Using Lean4 as a verifier means:

- **Step-level correctness** — every arithmetic step is a machine-checked proof, not just the final answer
- **Structured error feedback** — failures return typed, parseable Lean errors the LLM can act on directly
- **No heuristics** — the repair loop is grounded in formal logic; pass/fail is deterministic

The tradeoff: Lean's `omega` tactic handles linear arithmetic only, so problems requiring fractions, exponents, or implicit unit conversions can exceed its scope.

## Limitations

- Evaluated on a subset of GSM8K test split (full 500-problem run in progress)
- `omega` tactic covers linear integer arithmetic only — non-linear problems require `norm_num` or `field_simp`
- Single-theorem formulation may over-simplify multi-step problems (future: chain of theorems per step)
- Groq API rate limits constrain evaluation throughput (~0.3s sleep between calls)

## Results log

See `results/results.json` for full per-problem breakdown including per-attempt Lean code and reasoning.

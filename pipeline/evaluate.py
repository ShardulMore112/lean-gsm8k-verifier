from datasets import load_dataset
from repair_loop import solve
import json
import os
import time

CHECKPOINT_FILE = "results/checkpoint.json"
RESULTS_FILE    = "results/results.json"

os.makedirs("results", exist_ok=True)

# ── Load dataset ──────────────────────────────────────────────────────────────
dataset = load_dataset("openai/gsm8k", "main", split="test[:200]")
total   = len(dataset)

# ── Resume from checkpoint if it exists ──────────────────────────────────────
if os.path.exists(CHECKPOINT_FILE):
    with open(CHECKPOINT_FILE) as f:
        checkpoint = json.load(f)
    results    = checkpoint["results"]
    start_idx  = checkpoint["last_completed"] + 1
    print(f"✓ Resuming from problem {start_idx + 1}/{total}  ({len(results)} already done)")
else:
    results   = []
    start_idx = 0
    print(f"Starting fresh evaluation on {total} GSM8K problems...")

print("=" * 60)

# ── Main loop ─────────────────────────────────────────────────────────────────
for i, item in enumerate(dataset):
    if i < start_idx:
        continue

    problem = item["question"]
    print(f"\n[{i+1}/{total}]", end=" ")

    result = solve(problem)
    results.append(result)

    # Save checkpoint after every single problem
    with open(CHECKPOINT_FILE, "w") as f:
        json.dump({"last_completed": i, "results": results}, f)

    time.sleep(0.5)

# ── Metrics ───────────────────────────────────────────────────────────────────
solved   = [r for r in results if r["solved"]]
failed   = [r for r in results if not r["solved"]]

pass_at_1 = sum(1 for r in solved if r["attempts"] == 1)
pass_at_k = len(solved)

print("\n" + "=" * 60)
print("EVALUATION RESULTS")
print("=" * 60)
print(f"Total problems:     {total}")
print(f"Solved (pass@1):    {pass_at_1} ({100*pass_at_1/total:.1f}%)")
print(f"Solved (pass@5):    {pass_at_k} ({100*pass_at_k/total:.1f}%)")
print(f"Failed:             {len(failed)} ({100*len(failed)/total:.1f}%)")

repaired = [r for r in solved if r["attempts"] > 1]
print(f"Needed repair:      {len(repaired)}")
if repaired:
    avg_attempts = sum(r["attempts"] for r in repaired) / len(repaired)
    print(f"Avg repair attempts:{avg_attempts:.1f}")

# ── Save final results & clean up checkpoint ──────────────────────────────────
with open(RESULTS_FILE, "w") as f:
    json.dump({
        "summary": {
            "total":     total,
            "pass_at_1": pass_at_1,
            "pass_at_5": pass_at_k,
            "failed":    len(failed)
        },
        "results": results
    }, f, indent=2)

# Remove checkpoint only after successful full completion
os.remove(CHECKPOINT_FILE)
print(f"\n✓ Results saved to {RESULTS_FILE}")
print("✓ Checkpoint cleared — run complete.")
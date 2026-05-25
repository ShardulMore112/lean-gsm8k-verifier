from datasets import load_dataset
from repair_loop import solve
import json
import time

# Load 50 problems from GSM8K test set
dataset = load_dataset("openai/gsm8k", "main", split="test[:50]")

results = []
total = len(dataset)

print(f"Running evaluation on {total} GSM8K problems...")
print("=" * 60)

for i, item in enumerate(dataset):
    problem = item["question"]
    
    print(f"\n[{i+1}/{total}]", end=" ")
    
    result = solve(problem)
    results.append(result)
    
    # Small delay to avoid rate limiting
    time.sleep(0.5)

# ── Metrics ──
solved = [r for r in results if r["solved"]]
failed = [r for r in results if not r["solved"]]

pass_at_1 = sum(1 for r in solved if r["attempts"] == 1)
pass_at_k = len(solved)

print("\n" + "=" * 60)
print("EVALUATION RESULTS")
print("=" * 60)
print(f"Total problems:     {total}")
print(f"Solved (pass@1):    {pass_at_1} ({100*pass_at_1/total:.1f}%)")
print(f"Solved (pass@5):    {pass_at_k} ({100*pass_at_k/total:.1f}%)")
print(f"Failed:             {len(failed)} ({100*len(failed)/total:.1f}%)")

# Repair loop stats
repaired = [r for r in solved if r["attempts"] > 1]
print(f"Needed repair:      {len(repaired)}")
if repaired:
    avg_attempts = sum(r["attempts"] for r in repaired) / len(repaired)
    print(f"Avg repair attempts:{avg_attempts:.1f}")

# Save results
with open("results.json", "w") as f:
    json.dump({
        "summary": {
            "total": total,
            "pass_at_1": pass_at_1,
            "pass_at_5": pass_at_k,
            "failed": len(failed)
        },
        "results": results
    }, f, indent=2)

print("\nResults saved to results.json")
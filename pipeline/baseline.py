from datasets import load_dataset
from llm import _chat
import json
import time
import re

def extract_answer(text: str) -> str:
    """Extract final numeric answer from LLM response."""
    # Match full numbers including decimals, strip commas first
    numbers = re.findall(r'\d+(?:\.\d+)?', text.replace(',', ''))
    if not numbers:
        return ""
    # Take the last number and return only the integer part
    return str(int(float(numbers[-1])))

def get_gsm8k_answer(solution: str) -> str:
    """Extract ground truth answer from GSM8K solution string."""
    numbers = re.findall(r'\d+', solution.replace(',', ''))
    return numbers[-1] if numbers else ""

def baseline_solve(problem: str) -> dict:
    """Solve without Lean — just ask LLM for the answer directly."""
    messages = [
        {"role": "system", "content": "You are a math assistant. Solve the problem step by step. At the end, state the final answer as a number on the last line."},
        {"role": "user", "content": f"Problem: {problem}"}
    ]
    raw = _chat(messages)
    answer = extract_answer(raw)
    return {"answer": answer, "raw": raw}

if __name__ == "__main__":
    dataset = load_dataset("openai/gsm8k", "main", split="test[:200]")

    correct = 0
    total = len(dataset)

    results = []
    for i, item in enumerate(dataset):
        problem = item["question"]
        ground_truth = get_gsm8k_answer(item["answer"])

        result = baseline_solve(problem)
        is_correct = result["answer"] == ground_truth

        if is_correct:
            correct += 1

        results.append({
            "problem": problem,
            "predicted": result["answer"],
            "ground_truth": ground_truth,
            "correct": is_correct
        })

        print(f"[{i+1}/{total}] GT: {ground_truth} | Pred: {result['answer']} | {'✓' if is_correct else '✗'}")
        time.sleep(0.3)

    print(f"\nBaseline accuracy: {correct}/{total} = {100*correct/total:.1f}%")

    with open("baseline_results.json", "w") as f:
        json.dump({"accuracy": correct/total, "results": results}, f, indent=2)

    print("Saved to baseline_results.json")
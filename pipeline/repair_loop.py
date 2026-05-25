from verifier import verify_lean
from llm import generate_proof, client, SYSTEM_PROMPT
import os

MAX_ATTEMPTS = 5

def repair(problem: str, failed_lean: str, error: str) -> dict:
    """Ask LLM to fix a failed Lean proof given the error message."""
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Problem: {problem}"},
            {"role": "assistant", "content": f"LEAN: {failed_lean}"},
            {"role": "user", "content": f"""The Lean4 verifier rejected your proof with this error:

{error}

Please fix the LEAN line. Respond in the same format:
REASONING: <your reasoning>
LEAN: theorem solution : <expression> = <answer> := by omega"""}
        ],
        temperature=0.1
    )

    raw = response.choices[0].message.content.strip()
    lean_code = ""
    reasoning = ""

    for line in raw.split("\n"):
        if line.startswith("REASONING:"):
            reasoning = line.replace("REASONING:", "").strip()
        elif line.startswith("LEAN:"):
            lean_code = line.replace("LEAN:", "").strip()

    return {"reasoning": reasoning, "lean_code": lean_code, "raw": raw}


def solve(problem: str) -> dict:
    """
    Full pipeline: generate → verify → repair loop.
    Returns final result with solve status and attempt count.
    """
    print(f"\nProblem: {problem}")
    print("-" * 50)

    # Step 1: first attempt
    attempt = generate_proof(problem)
    lean_code = attempt["lean_code"]
    print(f"Attempt 1 — Lean: {lean_code}")

    for i in range(1, MAX_ATTEMPTS + 1):
        result = verify_lean(lean_code)

        if result["success"]:
            print(f"✓ Verified on attempt {i}")
            return {
                "problem": problem,
                "solved": True,
                "attempts": i,
                "lean_code": lean_code,
                "reasoning": attempt["reasoning"]
            }

        print(f"✗ Attempt {i} failed: {result['error'][:80]}...")

        if i == MAX_ATTEMPTS:
            break

        # Repair
        repaired = repair(problem, lean_code, result["error"])
        lean_code = repaired["lean_code"]
        print(f"Attempt {i+1} — Lean: {lean_code}")

    return {
        "problem": problem,
        "solved": False,
        "attempts": MAX_ATTEMPTS,
        "lean_code": lean_code,
        "reasoning": attempt["reasoning"]
    }


# --- Test it ---
if __name__ == "__main__":

    problems = [
        "Janet has 3 brothers and 5 sisters. How many siblings does she have in total?",
        "A store has 48 apples. They sell 19 and get a new shipment of 25. How many apples are there now?",
        "Each box holds 12 bottles. If there are 8 boxes, how many bottles are there in total?",
    ]

    results = []
    for problem in problems:
        result = solve(problem)
        results.append(result)

    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    solved = sum(1 for r in results if r["solved"])
    print(f"Solved: {solved}/{len(results)}")
    for r in results:
        status = "✓" if r["solved"] else "✗"
        print(f"{status} [{r['attempts']} attempt(s)] {r['problem'][:60]}")
import os
import time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# ── Three OpenRouter keys ─────────────────────────────────────────────────────
_KEYS = [
    os.getenv("OPENROUTER_API_KEY_1"),
    os.getenv("OPENROUTER_API_KEY_2"),
    os.getenv("OPENROUTER_API_KEY_3"),
]

MODEL = "meta-llama/llama-3.3-70b-instruct"

_key_index = 0  # which key we're currently using


def _make_client(key: str) -> OpenAI:
    return OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=key,
    )


def _current_client() -> OpenAI:
    return _make_client(_KEYS[_key_index])


# ── System prompt (unchanged) ─────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a math reasoning assistant that solves grade school math problems.

For every problem, you must respond in EXACTLY this format and nothing else:

REASONING: <your step by step reasoning in plain english>
LEAN: theorem solution : <expression> = <answer> := by omega

Rules:
- The LEAN line must be a single valid Lean4 theorem
- Use only +, -, *, / operators and natural numbers
- The theorem must be provable by the omega tactic
- Do not add any imports or extra text
- Do not use variables, only concrete numbers

Example:
Problem: John has 5 apples. He buys 3 more. How many does he have?
REASONING: John starts with 5 apples and buys 3 more. Total = 5 + 3 = 8
LEAN: theorem solution : 5 + 3 = 8 := by omega"""


# ── Internal chat with key rotation ──────────────────────────────────────────
def _chat(messages: list) -> str:
    global _key_index

    while _key_index < len(_KEYS):
        key = _KEYS[_key_index]
        if not key:
            print(f"⚠️  OPENROUTER_API_KEY_{_key_index + 1} not set — skipping.")
            _key_index += 1
            continue

        try:
            client = _make_client(key)
            response = client.chat.completions.create(
                model=MODEL,
                messages=messages,
                temperature=0.1,
            )
            return response.choices[0].message.content.strip()

        except Exception as e:
            err = str(e)
            if "429" in err or "rate_limit_exceeded" in err or "insufficient_quota" in err:
                print(f"\n⚠️  Key {_key_index + 1} exhausted — switching to key {_key_index + 2}.\n")
                _key_index += 1
                time.sleep(2)
                continue
            raise  # non-rate-limit error → crash immediately

    raise RuntimeError("❌ All 3 OpenRouter keys exhausted. Add more keys or wait for reset.")


# ── Public API (identical to original) ───────────────────────────────────────
def generate_proof(problem: str) -> dict:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user",   "content": f"Problem: {problem}"}
    ]

    raw = _chat(messages)

    reasoning = " "
    lean_code = " "

    for line in raw.split("\n"):
        if line.startswith("REASONING:"):
            reasoning = line.replace("REASONING:", "").strip()
        elif line.startswith("LEAN:"):
            lean_code = line.replace("LEAN:", "").strip()

    return {
        "problem":   problem,
        "reasoning": reasoning,
        "lean_code": lean_code,
        "raw":       raw
    }


if __name__ == "__main__":
    problem = "Janet has 3 brothers and 5 sisters. How many siblings does she have in total?"
    result = generate_proof(problem)

    print("Problem:",   result["problem"])
    print("Reasoning:", result["reasoning"])
    print("Lean:",      result["lean_code"])
    print("---")
    print("Raw output:", result["raw"])
    print(f"Active key: #{_key_index + 1}")
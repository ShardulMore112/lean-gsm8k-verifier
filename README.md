# Verified Chain-of-Thought Solver

LLM reasoning with Lean4 as a symbolic verifier for GSM8K math problems.

## Results
- **pass@1**: 80% (40/50)
- **pass@5**: 94% (47/50)
- **Avg repair attempts**: 2.4

## Architecture
Problem → LLM generates Lean4 theorem → Lean verifier checks → 
If fail: error fed back to LLM → repair loop (max 5 attempts)

## Stack
- Lean4 4.29.1 (formal verifier)
- Llama 3.3 70B via Groq API (LLM)
- Python (orchestration)
- GSM8K dataset (HuggingFace)

## Setup
1. Install dependencies: pip install -r requirements.txt
2. Create .env file with: GROQ_API_KEY=your_key_here
3. Run: python pipeline/evaluate.py
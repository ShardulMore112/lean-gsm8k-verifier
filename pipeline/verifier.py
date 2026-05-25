import subprocess
import tempfile
import os

LEAN_BINARY = r"C:\Users\shard\.elan\bin\lean.exe"

def verify_lean(lean_code: str) -> dict:
    """
    Takes a Lean4 code string, writes it to a temp file,
    runs lean on it, returns success/failure + error message.
    """
    with tempfile.NamedTemporaryFile(
        mode='w',
        suffix='.lean',
        delete=False,
        encoding='utf-8'
    ) as f:
        f.write(lean_code)
        temp_path = f.name

    try:
        result = subprocess.run(
            [LEAN_BINARY, temp_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        success = result.returncode == 0
        # lean writes errors to stdout, not stderr
        error = result.stdout.strip() if not success else None

        return {
            "success": success,
            "error": error,
            "stdout": result.stdout.strip()
        }

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": "Lean verification timed out",
            "stdout": ""
        }

    finally:
        os.unlink(temp_path)


# --- Test it ---
if __name__ == "__main__":

    # Test 1: should succeed
    good_proof = "theorem test1 : 2 + 3 = 5 := by omega"
    result = verify_lean(good_proof)
    print("Test 1 (should pass):", result)

    # Test 2: should fail
    bad_proof = "theorem test2 : 2 + 3 = 6 := by omega"
    result = verify_lean(bad_proof)
    print("Test 2 (should fail):", result)

    # Test 3: GSM8K style
    gsm_proof = "theorem solution : 5 * 12 + 8 = 68 := by omega"
    result = verify_lean(gsm_proof)
    print("Test 3 (GSM8K style):", result)
"""main.py — Unified launcher for AcademyOps.

Starts the FastAPI backend (uvicorn, port 8000).

Usage
-----
    python main.py

Stop with Ctrl+C.
"""

import subprocess
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main() -> None:
    print("\n" + "=" * 55)
    print("  AcademyOps - Lead-to-Enrollment CRM")
    print("=" * 55)
    print()
    print("  API           -> http://localhost:8000/api/v1")
    print("  Documentation -> http://localhost:8000/docs")
    print("  Web CRM App   -> http://localhost:8000")
    print()
    print("  Press Ctrl+C to stop.\n")

    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api.app:app", "--port", "8000"],
    )

    try:
        api_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        api_proc.terminate()
        try:
            api_proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            api_proc.kill()
        print("Stopped. Goodbye.")


if __name__ == "__main__":
    main()
 
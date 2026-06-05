"""main.py — Unified launcher for AcademyOps.

Starts the FastAPI backend (uvicorn, port 8000) and the Streamlit dashboard
(port 8501) as concurrent processes.

Usage
-----
    python main.py

Stop with Ctrl+C — both processes are shut down cleanly.
"""

import subprocess
import sys
import time

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def main() -> None:
    print("\n" + "=" * 55)
    print("  AcademyOps — Lead-to-Enrollment Management System")
    print("=" * 55)
    print()
    print("  API  →  http://localhost:8000/api/v1")
    print("  Docs →  http://localhost:8000/docs")
    print("  Dashboard → http://localhost:8501")
    print()
    print("  Press Ctrl+C to stop.\n")

    api_proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "src.api.app:app", "--port", "8000"],
    )

    time.sleep(2)

    dashboard_proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", "src/dashboard/app.py", "--logger.level=error"],
    )

    try:
        api_proc.wait()
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        for proc in (api_proc, dashboard_proc):
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
        print("Stopped. Goodbye.")


if __name__ == "__main__":
    main()

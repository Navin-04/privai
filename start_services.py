import atexit
import os
import subprocess
import sys
from typing import Sequence


def stop_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        process.kill()


def run_command(command: Sequence[str]) -> subprocess.Popen:
    return subprocess.Popen(command)


def main() -> int:
    api_port = os.getenv("API_PORT", "8080")
    streamlit_port = os.getenv("STREAMLIT_PORT", "8501")
    os.environ.setdefault("BACKEND_URL", f"http://127.0.0.1:{api_port}")

    backend_process = run_command(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "api.main:app",
            "--host",
            "0.0.0.0",
            "--port",
            api_port,
        ]
    )
    atexit.register(stop_process, backend_process)

    try:
        return subprocess.call(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "app.py",
                "--server.address=0.0.0.0",
                f"--server.port={streamlit_port}",
            ]
        )
    finally:
        stop_process(backend_process)


if __name__ == "__main__":
    raise SystemExit(main())

"""Cross-platform CLI runner for RetailTech S.A.S project."""

import argparse
import os
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
VENV_DIR = PROJECT_ROOT / ".venv"

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")


def get_python():
    """Return the venv python path, cross-platform."""
    if platform.system() == "Windows":
        return str(VENV_DIR / "Scripts" / "python.exe")
    return str(VENV_DIR / "bin" / "python")


def get_bin(name):
    """Return path to a venv binary/script."""
    if platform.system() == "Windows":
        return str(VENV_DIR / "Scripts" / name)
    return str(VENV_DIR / "bin" / name)


def _ollama_is_installed():
    """Check if ollama binary is available in PATH."""
    return shutil.which("ollama") is not None


def _ollama_server_ready():
    """Check if the Ollama server is responding."""
    try:
        req = urllib.request.Request("http://localhost:11434/api/tags")
        with urllib.request.urlopen(req, timeout=5):
            return True
    except Exception:
        return False


def _install_ollama():
    """Download and install Ollama automatically based on OS."""
    system = platform.system()
    print(f"Ollama not found. Installing automatically for {system}...")

    if system == "Linux":
        subprocess.run(
            ["bash", "-c", "curl -fsSL https://ollama.com/install.sh | sh"],
            check=True,
        )
    elif system == "Darwin":
        if shutil.which("brew"):
            subprocess.run(["brew", "install", "ollama"], check=True)
        else:
            print("ERROR: Install Homebrew first (https://brew.sh) or download Ollama from https://ollama.com")
            sys.exit(1)
    elif system == "Windows":
        installer_url = "https://ollama.com/download/OllamaSetup.exe"
        tmp = Path(tempfile.gettempdir()) / "OllamaSetup.exe"
        print(f"Downloading Ollama installer to {tmp}...")
        urllib.request.urlretrieve(installer_url, str(tmp))
        print("Running installer (this may take a moment)...")
        subprocess.run([str(tmp), "/VERYSILENT", "/NORESTART"], check=True)
        # Add default install path to current session PATH
        ollama_dir = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama"
        if ollama_dir.exists():
            os.environ["PATH"] = str(ollama_dir) + os.pathsep + os.environ["PATH"]
        tmp.unlink(missing_ok=True)
    else:
        print(f"ERROR: Unsupported platform '{system}'. Install Ollama manually from https://ollama.com")
        sys.exit(1)

    if not _ollama_is_installed():
        print("ERROR: Ollama installation completed but binary not found in PATH.")
        print("Try restarting your terminal or adding Ollama to PATH manually.")
        sys.exit(1)

    print("Ollama installed successfully.")


def _ensure_ollama_server():
    """Make sure the Ollama server is running, start it if needed."""
    if _ollama_server_ready():
        return

    ollama_bin = shutil.which("ollama")
    print("Starting Ollama server in background...")
    if platform.system() == "Windows":
        subprocess.Popen(
            [ollama_bin, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
    else:
        subprocess.Popen(
            [ollama_bin, "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

    # Wait for server to be ready
    for i in range(15):
        time.sleep(1)
        if _ollama_server_ready():
            print("Ollama server is ready.")
            return
    print("WARNING: Ollama server did not start within 15 seconds.")
    print("Try running 'ollama serve' manually in another terminal.")


def _ensure_model_pulled():
    """Pull the LLM model if it's not already available."""
    ollama_bin = shutil.which("ollama")
    result = subprocess.run(
        [ollama_bin, "list"], capture_output=True, text=True,
    )
    if OLLAMA_MODEL in result.stdout:
        print(f"Model {OLLAMA_MODEL} already available.")
        return

    print(f"Pulling model {OLLAMA_MODEL} (this may take several minutes)...")
    subprocess.run([ollama_bin, "pull", OLLAMA_MODEL], check=True)
    print(f"Model {OLLAMA_MODEL} pulled successfully.")


def ensure_ollama():
    """Full Ollama bootstrap: install if missing, start server, pull model."""
    if not _ollama_is_installed():
        _install_ollama()
    _ensure_ollama_server()
    _ensure_model_pulled()


def cmd_venv(_args):
    """Create virtual environment."""
    if VENV_DIR.exists():
        print(f"Virtual environment already exists at {VENV_DIR}")
    else:
        subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True)
        print(f"Created venv at {VENV_DIR}")
    subprocess.run(
        [get_python(), "-m", "pip", "install", "--upgrade", "pip"],
        check=True,
    )


def cmd_setup(_args):
    """Install dependencies, install Ollama if needed, and pull LLM model."""
    cmd_venv(_args)
    subprocess.run(
        [get_python(), "-m", "pip", "install", "-r", "requirements.txt"],
        check=True,
    )
    ensure_ollama()


def cmd_pipeline(args):
    """Run ETL pipeline."""
    stage = getattr(args, "stage", "run")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    subprocess.run(
        [get_python(), "-m", "pipeline.pipeline", stage],
        env=env,
        check=True,
    )


def cmd_api(_args):
    """Start FastAPI agent backend (ensures Ollama is running first)."""
    if _ollama_is_installed():
        _ensure_ollama_server()
    else:
        print("WARNING: Ollama not installed. Run 'python run.py setup' first.")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    subprocess.run(
        [
            get_python(), "-m", "uvicorn", "agent.api:app",
            "--host", "0.0.0.0", "--port", "8000", "--reload",
        ],
        env=env,
    )


def cmd_app(_args):
    """Start Streamlit frontend."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    subprocess.run(
        [get_python(), "-m", "streamlit", "run", "app/main.py"],
        env=env,
    )


def cmd_test(_args):
    """Run tests."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    subprocess.run([get_python(), "-m", "pytest", "-v"], env=env)


def cmd_lint(_args):
    """Run syntax check on core modules."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT)
    modules = [
        "pipeline/src/bronze.py",
        "pipeline/src/silver.py",
        "pipeline/src/gold.py",
        "agent/agent.py",
        "agent/api.py",
        "agent/llm_backend.py",
    ]
    subprocess.run(
        [get_python(), "-m", "py_compile"] + modules,
        env=env,
    )


def cmd_clean(_args):
    """Clean pipeline output data."""
    dirs_to_clean = [
        PROJECT_ROOT / "pipeline" / "data" / d
        for d in ["raw", "bronze", "silver", "gold"]
    ]
    for d in dirs_to_clean:
        if d.exists():
            shutil.rmtree(d)
            print(f"Removed {d}")
    for db in (PROJECT_ROOT / "pipeline" / "data").glob("*.duckdb"):
        db.unlink()
        print(f"Removed {db}")
    print("Clean complete.")


def cmd_doctor(_args):
    """Check system readiness."""
    all_ok = True
    print("=" * 50)
    print("  RetailTech S.A.S - System Diagnostic")
    print("=" * 50)
    print(f"Platform:  {platform.system()} {platform.machine()}")
    print(f"Python:    {sys.version.split()[0]}")

    # Venv
    venv_ok = VENV_DIR.exists()
    print(f"Venv:      {'OK' if venv_ok else 'MISSING'}")
    all_ok = all_ok and venv_ok

    # Ollama binary
    ollama_bin = shutil.which("ollama")
    if ollama_bin:
        ver = subprocess.run([ollama_bin, "--version"], capture_output=True, text=True)
        print(f"Ollama:    OK ({ver.stdout.strip()})")
    else:
        print("Ollama:    NOT FOUND (will be installed automatically by 'python run.py setup')")
        all_ok = False

    # Ollama server
    if ollama_bin:
        server_ok = _ollama_server_ready()
        print(f"Server:    {'OK (running on :11434)' if server_ok else 'NOT RUNNING (start with: ollama serve)'}")
        all_ok = all_ok and server_ok

    # Model
    if ollama_bin:
        result = subprocess.run([ollama_bin, "list"], capture_output=True, text=True)
        if OLLAMA_MODEL in result.stdout:
            print(f"Model:     {OLLAMA_MODEL} available")
        else:
            print(f"Model:     {OLLAMA_MODEL} NOT PULLED (will be pulled by 'python run.py setup')")
            all_ok = False

    # DuckDB
    db_path = PROJECT_ROOT / "pipeline" / "data" / "retailtech.duckdb"
    db_ok = db_path.exists()
    print(f"DuckDB:    {'OK' if db_ok else 'NOT FOUND (run: python run.py pipeline)'}")
    all_ok = all_ok and db_ok

    print("-" * 50)
    if all_ok:
        print("Status:    ALL CHECKS PASSED")
    else:
        print("Status:    SOME CHECKS FAILED")
        print("Fix:       python run.py setup && python run.py pipeline")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="RetailTech S.A.S - Cross-platform project runner",
    )
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("venv", help="Create virtual environment")
    sub.add_parser("setup", help="Install all dependencies + pull model")

    p_pipeline = sub.add_parser("pipeline", help="Run ETL pipeline")
    p_pipeline.add_argument(
        "stage",
        nargs="?",
        default="run",
        choices=["run", "bronze", "silver", "gold", "queries"],
    )

    sub.add_parser("api", help="Start FastAPI agent backend (port 8000)")
    sub.add_parser("app", help="Start Streamlit frontend (port 8501)")
    sub.add_parser("test", help="Run pytest")
    sub.add_parser("lint", help="Syntax check on core modules")
    sub.add_parser("clean", help="Clean pipeline data")
    sub.add_parser("doctor", help="Check system readiness")

    args = parser.parse_args()
    commands = {
        "venv": cmd_venv,
        "setup": cmd_setup,
        "pipeline": cmd_pipeline,
        "api": cmd_api,
        "app": cmd_app,
        "test": cmd_test,
        "lint": cmd_lint,
        "clean": cmd_clean,
        "doctor": cmd_doctor,
    }
    if args.command in commands:
        commands[args.command](args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

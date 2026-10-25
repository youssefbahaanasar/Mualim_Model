"""Create a local environment and install the Hadith UI on a fresh checkout."""

import os
from pathlib import Path
import subprocess
import sys
import venv


def main():
    if not (3, 10) <= sys.version_info[:2] <= (3, 12):
        raise SystemExit("Use Python 3.10-3.12 (Python 3.12 recommended for this setup).")
    root = Path(__file__).resolve().parents[1]
    environment = root / ".venv"
    python = environment / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    if not python.is_file():
        print("Creating .venv ...", flush=True)
        venv.EnvBuilder(with_pip=True).create(environment)
    if subprocess.run([str(python), "-c", "import pip"], capture_output=True).returncode:
        subprocess.run([str(python), "-m", "ensurepip", "--upgrade"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "--upgrade", "pip"], check=True)
    subprocess.run([str(python), "-m", "pip", "install", "-e", ".[hadith]"], cwd=root, check=True)
    print("Setup complete. On Windows, open Run-Hadith.cmd.")
    print("Otherwise run: .venv/bin/python run_hadith.py")


if __name__ == "__main__":
    main()

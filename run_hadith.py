"""Start the local app with project-local model and audio tool paths."""

import os
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parent
    venv = root / ".venv"
    bundled_python = root / ".tools" / "python"
    if bundled_python in Path(sys.executable).resolve().parents and Path(sys.prefix).resolve() != venv.resolve():
        # uv's Windows launcher records an absolute base-Python path.
        # Refresh it when a project with bundled Python has been moved.
        config = venv / "pyvenv.cfg"
        if not config.is_file():
            raise RuntimeError("Project environment missing. See HADITH_README.md.")
        lines = config.read_text(encoding="utf-8").splitlines()
        lines = [f"home = {Path(sys.executable).parent}" if line.startswith("home =") else line
                 for line in lines]
        config.write_text("\n".join(lines) + "\n", encoding="utf-8")
        launcher = Path(sys.base_prefix) / "Lib" / "venv" / "scripts" / "nt" / "python.exe"
        target = venv / "Scripts" / "python.exe"
        if launcher.is_file() and target.read_bytes() != launcher.read_bytes():
            shutil.copyfile(launcher, target)
        raise SystemExit(subprocess.call([str(target), "-u", str(Path(__file__).resolve())]))
    # Editable install paths can also point to the project's previous location.
    sys.path.insert(0, str(root / "src"))
    os.environ.setdefault("HF_HOME", str(root / ".cache" / "huggingface"))
    os.environ["GRADIO_ANALYTICS_ENABLED"] = "False"
    ffmpeg = next((root / ".tools" / "ffmpeg").rglob("ffmpeg.exe"), None)
    if ffmpeg:
        os.environ["PATH"] = str(ffmpeg.parent) + os.pathsep + os.environ.get("PATH", "")
    from hadith_muaalem.gradio_app import main as launch

    launch()


if __name__ == "__main__":
    main()

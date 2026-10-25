"""Exercise real ASR without treating its output as a verified transcript.

Run with the project environment: python scripts/check_hadith_runtime.py audio.wav
"""

import argparse
import json
import os
from pathlib import Path
from time import perf_counter


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("audio", type=Path)
    parser.add_argument("--seconds", type=float, default=25)
    parser.add_argument("--output", type=Path, default=Path(".cache/smoke/runtime-result.json"))
    args = parser.parse_args()
    if not 0 < args.seconds <= 300:
        parser.error("--seconds must be between 0 and 300")
    os.environ.setdefault("HF_HOME", str(Path(".cache/huggingface").resolve()))

    import librosa
    import soundfile as sf
    import torch
    from hadith_muaalem.inference import HadithRecognizer

    args.output.parent.mkdir(parents=True, exist_ok=True)
    wave, sr = librosa.load(args.audio, sr=16000, mono=True, duration=args.seconds)
    clip = args.output.parent / "runtime-clip.wav"
    sf.write(clip, wave, sr)
    if torch.cuda.is_available():
        # Check that the CUDA build executes on the actual GPU architecture.
        value = (torch.ones((32, 32), device="cuda") @ torch.ones((32, 32), device="cuda"))[0, 0].item()
        assert value == 32
    recognizer = HadithRecognizer()
    start = perf_counter()
    transcript = recognizer.transcribe(str(clip))
    report = {
        "model": recognizer.model_name_or_path,
        "torch": torch.__version__,
        "cuda": torch.version.cuda,
        "device": torch.cuda.get_device_name(0) if torch.cuda.is_available() else "cpu",
        "audio_seconds": len(wave) / sr,
        "elapsed_seconds_including_model_load": round(perf_counter() - start, 3),
        "transcript": transcript,
        "manual_reference_available": False,
        "note": "Runtime check only. No measured ASR accuracy without a manual transcript.",
    }
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if not transcript:
        raise SystemExit("No transcription produced; inspect the recording")


if __name__ == "__main__":
    main()

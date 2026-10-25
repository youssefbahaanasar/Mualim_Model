"""Arabic ASR adapter, loaded only when audio is submitted."""

import os
from pathlib import Path
from threading import Lock


class HadithRecognizer:
    def __init__(self, model_name_or_path: str | None = None):
        self.model_name_or_path = model_name_or_path or os.getenv(
            "HADITH_ASR_MODEL", "openai/whisper-large-v3-turbo"
        )
        self._pipeline = None
        self._lock = Lock()

    def transcribe(self, audio_path: str) -> str:
        import librosa
        import numpy as np
        import torch
        from transformers import pipeline
        from huggingface_hub import try_to_load_from_cache

        wave, _ = librosa.load(audio_path, sr=16000, mono=True)
        if not len(wave) or not np.isfinite(wave).all():
            raise ValueError("Audio is empty or contains invalid samples")
        if len(wave) > 16000 * 300:
            raise ValueError("Please use a recording of at most five minutes")
        if np.max(np.abs(wave)) < 1e-5:
            raise ValueError("No audible signal found")
        # Serialize generation and lazy initialization across UI sessions.
        with self._lock:
            if self._pipeline is None:
                cuda = torch.cuda.is_available()
                model_location = self.model_name_or_path
                if not Path(model_location).is_dir():
                    weights = try_to_load_from_cache(model_location, "model.safetensors")
                    if isinstance(weights, str):
                        cached_dir = Path(weights).parent
                        required = ("config.json", "preprocessor_config.json", "tokenizer.json", "generation_config.json")
                        if all((cached_dir / name).is_file() for name in required):
                            model_location = str(cached_dir)
                self._pipeline = pipeline(
                    "automatic-speech-recognition", model=model_location,
                    device=0 if cuda else -1,
                    torch_dtype=torch.float16 if cuda else torch.float32,
                )
            # Never prompt the recognizer with the expected hadith: that can
            # conceal omissions by biasing the transcription toward the answer.
            output = self._pipeline(
                {"raw": wave, "sampling_rate": 16000},
                return_timestamps=True,
                generate_kwargs={"language": "arabic", "task": "transcribe"},
            )
        return output["text"].strip()

import json
import hashlib
import re
from typing import Literal
from functools import lru_cache
from importlib.resources import files


@lru_cache(maxsize=1)
def _collection() -> tuple[tuple[int, str], ...]:
    raw = json.loads(files("hadith_muaalem").joinpath("data/nawawi.json").read_text(encoding="utf-8-sig"))
    collection = tuple((int(item["hadithnumber"]), item["text"]) for item in raw["hadiths"])
    if sorted(number for number, _ in collection) != list(range(1, 43)):
        raise ValueError("Expected the 42 numbered Nawawi hadiths")
    return collection


def load_collection() -> list[dict]:
    return [{"number": number, "text": text} for number, text in _collection()]


@lru_cache(maxsize=1)
def _matn_spans() -> dict:
    data = json.loads(files("hadith_muaalem").joinpath("data/matn_spans.json").read_text(encoding="utf-8"))
    if set(data) != {str(i) for i in range(1, 43)}:
        raise ValueError("Missing Nawawi matn boundaries")
    return data


def _clean_text(text: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", text).split())


def get_hadith(number: int, scope: Literal["full", "matn"] = "full") -> str:
    if scope not in ("full", "matn"):
        raise ValueError("Choose full or matn")
    for hadith_number, text in _collection():
        if hadith_number == number:
            if scope == "full":
                return _clean_text(text)
            entry = _matn_spans()[str(number)]
            if hashlib.sha256(text.encode("utf-8")).hexdigest() != entry["source_sha256"]:
                raise ValueError("نص الحديث تغيّر؛ يلزم تحديث حدود المتن قبل استخدام هذا الاختيار")
            parts = []
            previous_end = 0
            for start, end in entry["spans"]:
                if not previous_end <= start < end <= len(text):
                    raise ValueError("Invalid matn boundaries")
                parts.append(text[start:end])
                previous_end = end
            if not parts:
                raise ValueError("Empty matn")
            return _clean_text(" ".join(parts))
    raise ValueError("Hadith number must be between 1 and 42")

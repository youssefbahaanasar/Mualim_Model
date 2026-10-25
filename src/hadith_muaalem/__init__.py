"""Reference-based reading practice for the Forty Hadith of al-Nawawi."""

from .catalog import get_hadith, load_collection
from .comparison import compare_texts

__all__ = ["get_hadith", "load_collection", "compare_texts"]

"""Language/script router. Dependency-free, microsecond."""
import re
from typing import Any, Dict, Union

STOP = {
    "en": {"the", "and", "please", "refund", "account", "invoice"},
    "es": {"el", "los", "por", "para", "gracias", "cuenta", "factura"},
    "pt": {"os", "para", "com", "obrigado", "conta", "fatura", "você", "voce"},
    "fr": {"le", "les", "merci", "compte", "facture", "bonjour"},
    "de": {"der", "und", "danke", "konto", "rechnung"},
}
WORD = re.compile(r"[^\W\d_]+", re.UNICODE)


def _text(state: Union[str, dict, list, None]) -> str:
    if state is None:
        return ""
    if isinstance(state, str):
        return state
    if isinstance(state, dict):
        return " ".join(str(v) for v in state.values())
    if isinstance(state, (list, tuple)):
        return " ".join(str(v) for v in state)
    return str(state)


def detect_script(text: str) -> str:
    latin = sum(1 for ch in text if ch.isalpha() and ord(ch) < 0x250)
    other = sum(1 for ch in text if ch.isalpha() and ord(ch) >= 0x250)
    if latin + other == 0:
        return "unknown"
    return "latin" if latin >= other else "non-latin"


def guess_lang(text: str):
    words = set(WORD.findall(text.lower()))
    if not words:
        return None
    scores = {lg: len(words & sw) for lg, sw in STOP.items()}
    best, val = max(scores.items(), key=lambda kv: kv[1])
    return best if val >= 1 else None


def route(state: Union[str, dict, list, None], lang: str = None) -> Dict[str, Any]:
    """Route to english/multilingual. tiny-decide runs one binary; routing keeps Laya/Jev semantics."""
    if lang:
        primary = re.split(r"[-_.@]", str(lang).strip().lower())[0].split(".")[0]
        model = "english" if primary in ("en", "eng", "english") else "multilingual"
        return {"model": model, "reason": "explicit lang=%r" % lang}
    text = _text(state)
    script = detect_script(text)
    if script == "unknown":
        return {"model": "english", "reason": "no letters; default english"}
    if script != "latin":
        return {"model": "multilingual", "reason": "non-Latin script"}
    lg = guess_lang(text)
    if lg in (None, "en"):
        return {"model": "english", "reason": "English Latin text"}
    return {"model": "multilingual", "reason": "looks like %r" % lg}

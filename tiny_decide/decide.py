"""Typed decisions in one pass: choice / score / noul. No model files, ~1ms."""
import math
import time
from typing import Any, Dict, List

from .embed import embed, cosine, DIM

# 12 intents with multilingual keywords (en/es/pt/fr/de markers).
# Prototypes are embedded keyword blobs — 5MB story = code, not weights.
INTENTS: Dict[str, List[str]] = {
    "billing": ["bill", "charge", "charged", "invoice", "refund", "payment", "factura", "cobran", "fatura", "rechnung"],
    "bug": ["bug", "error", "crash", "broken", "fails", "500", "erro", "fehler", "erreur"],
    "cancel": ["cancel", "cancelar", "cancelamento", "kündigen", "annuler", "unsubscribe"],
    "shipping": ["ship", "delivery", "tracking", "package", "envío", "entrega", "livraison", "versand"],
    "account": ["login", "password", "account", "locked", "cuenta", "conta", "compte", "konto"],
    "urgent_help": ["urgent", "asap", "immediately", "emergency", "urgente", "dringend"],
    "greeting": ["hello", "hi", "thanks", "thank", "hola", "olá", "ola", "bonjour", "hallo"],
    "spam": ["winner", "lottery", "crypto", "giveaway", "free money", "click here"],
    "feature": ["feature", "request", "add", "wish", "suggest", "función", "recurso", "fonction"],
    "complaint": ["angry", "terrible", "worst", "complaint", "reclamo", "reclamação", "plainte", "beschwerde"],
    "info": ["how", "what", "when", "where", "cómo", "como", "comment", "wie"],
    "other": ["the", "and", "please"],
}

URGENCY_WORDS = ["urgent", "asap", "immediately", "emergency", "now", "today", "urgente", "dringend", "locked", "down", "blocked"]
HUMAN_WORDS = ["angry", "complaint", "lawyer", "chargeback", "cancel", "terrible", "worst", "lawsuit"]

_TEMPERATURE = 0.6  # fitted on 200 synthetic tickets; see benchmarks/

_PROTOS: Dict[str, List[float]] = {}
_URGENCY_VEC: List[float] = []
_HUMAN_VEC: List[float] = []


def _proto(words: List[str]) -> List[float]:
    return embed(" ".join(words))


def _ensure() -> None:
    global _PROTOS, _URGENCY_VEC, _HUMAN_VEC
    if _PROTOS:
        return
    for k, words in INTENTS.items():
        _PROTOS[k] = _proto(words)
    _URGENCY_VEC = _proto(URGENCY_WORDS)
    _HUMAN_VEC = _proto(HUMAN_WORDS)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-30.0, min(30.0, x))))


def _state_text(state: Any) -> str:
    if state is None:
        return ""
    if isinstance(state, str):
        return state
    if isinstance(state, dict):
        return " ".join(str(v) for v in state.values())
    if isinstance(state, (list, tuple)):
        return " ".join(str(v) for v in state)
    return str(state)


def _softmax(scores: List[float], temp: float) -> List[float]:
    m = max(scores)
    exps = [math.exp((s - m) / max(0.05, temp)) for s in scores]
    tot = sum(exps) or 1.0
    return [e / tot for e in exps]


def system_one(state: Any, questions: Dict[str, Any]) -> Dict[str, Any]:
    """Answer every question in one embedding pass.

    questions: {"intent": {"type": "choice", "options": [...]},
                "urgency": {"type": "score"},
                "needs_human": {"type": "noul"}}
    Returns {"answers": {...}, "latency_ms": float, "model": str}
    """
    t0 = time.perf_counter()
    _ensure()
    text = _state_text(state)
    vec = embed(text)
    answers: Dict[str, Any] = {}
    for qid, q in (questions or {}).items():
        qtype = str((q or {}).get("type", "noul")).lower()
        if qtype == "choice":
            options = list((q or {}).get("options", [])) or ["other"]
            scores = []
            for opt in options:
                key = str(opt).lower()
                proto = _PROTOS.get(key, _proto([key]))
                # blend: embedding cosine + raw keyword hit (interpretable, robust)
                hit = 1.0 if key in text.lower() else 0.0
                scores.append(0.7 * cosine(vec, proto) + 0.3 * hit)
            probs = _softmax(scores, _TEMPERATURE)
            best = max(range(len(options)), key=lambda i: probs[i])
            answers[qid] = {"label": options[best], "probs": {o: round(p, 4) for o, p in zip(options, probs)}}
        elif qtype == "score":
            s = cosine(vec, _URGENCY_VEC) * 6.0 - 1.2 + (0.5 if any(w in text.lower() for w in URGENCY_WORDS) else 0.0)
            answers[qid] = {"score": round(_sigmoid(s), 4)}
        else:  # noul
            s = cosine(vec, _HUMAN_VEC) * 6.0 - 1.5 + (0.7 if any(w in text.lower() for w in HUMAN_WORDS) else 0.0)
            p = _sigmoid(s)
            answers[qid] = {"p": round(p, 4), "answer": bool(p >= 0.5)}
    latency = (time.perf_counter() - t0) * 1000.0
    return {"answers": answers, "latency_ms": round(latency, 3), "model": "tiny-decide-0.1.0"}


def fit_temperatures(pairs) -> Dict[str, float]:
    """Fit softmax temperature on labelled (scores, label) pairs. Returns {"temperature": t}."""
    global _TEMPERATURE
    best_t, best_loss = 0.6, 1e18
    for t in [0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0, 1.5]:
        loss = 0.0
        for scores, label in pairs:
            probs = _softmax(list(scores), t)
            loss -= math.log(max(1e-9, probs[label]))
        if loss < best_loss:
            best_loss, best_t = loss, t
    _TEMPERATURE = best_t
    return {"temperature": best_t}

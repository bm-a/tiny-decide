"""Token estimator that doesn't lie on dense text. Fixes fast-jev #81/#85 and Han #82."""
import re

HEX_RUN = re.compile(r"\b(?:[0-9a-fA-F]{16,}|[0-9A-F]{8,}(?:-[0-9A-F]{4}){3}-[0-9A-F]{12})\b")
B64_RUN = re.compile(r"\b[A-Za-z0-9+/]{24,}={0,2}\b")
UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")


def _is_han(ch: str) -> bool:
    cp = ord(ch)
    return 0x3400 <= cp <= 0x4DBF or 0x4E00 <= cp <= 0x9FFF or 0xF900 <= cp <= 0xFAFF


def estimate_tokens(text: str) -> int:
    """~4 chars/token prose; dense hex/uuid/base64 ~3 chars/token; Han ~1 tok/char."""
    if not text:
        return 0
    han = sum(1 for ch in text if _is_han(ch))
    spans = []
    for pat in (UUID, HEX_RUN, B64_RUN):
        for m in pat.finditer(text):
            spans.append((m.start(), m.end()))
    spans.sort()
    merged = []
    for s, e in spans:
        if merged and s <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    # Only count a span as dense if it looks like a real run, not plain prose:
    # require no spaces (already true) and (has digit or len>=40 or mixed case).
    dense = 0
    for s, e in merged:
        chunk = text[s:e]
        if any(ch.isdigit() for ch in chunk) or len(chunk) >= 40 or (
            any(c.islower() for c in chunk) and any(c.isupper() for c in chunk)
        ):
            dense += e - s
    rest = max(0, len(text) - han - dense)
    return int(round(han * 0.99 + dense / 3.0 + rest / 4.0)) or (1 if text else 0)

"""Email cleaning with the #245 fix baked in: warmest / thanks-and-regards / unicode names."""
import re

_SIGNOFF = re.compile(
    r"^\s*(?i:best|kind|warmest|warm|many thanks|thanks|thank you|regards|cheers|sincerely)"
    r"(?i:\s+(?:and\s+regards|&\s+regards|regards|wishes|again|in advance|a lot|so much|very much))?"
    r"[\s,;:!.]*(?:[^a-z][\w'-]*[\s,.]*){0,3}$"
)
_QUOTE = re.compile(r"^\s*(On .{0,200}wrote:\s*|From:\s.+|---.*(Original|Forwarded).*|De:\s.*[@<])", re.I)


def clean_email_body(body: str, max_chars: int = 3000) -> str:
    text = (body or "").replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in text.split("\n"):
        if line.lstrip().startswith(">"):
            continue
        if _QUOTE.match(line) and lines:
            break
        lines.append(line.rstrip())
    cut = len(lines)
    for i in range(max(1, min(int(len(lines) * 0.6), len(lines) - 8)), len(lines)):
        if len(lines[i].strip()) <= 40 and _SIGNOFF.match(lines[i]):
            cut = i
            break
    return re.sub(r"[ \t]+", " ", "\n".join(lines[:cut]).strip())[:max_chars]

"""Hashed char-ngram embeddings. No deps, deterministic, ~50us/text."""
import hashlib
import math
from typing import List

DIM = 256

def _hash(s: str) -> int:
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)

def embed(text: str, dim: int = DIM) -> List[float]:
    text = (text or "").lower()
    vec = [0.0] * dim
    # word unigrams + char trigrams: cheap, multilingual-friendly
    for tok in text.split():
        t = tok.strip(".,;:!?()[]{}\"'")
        if not t:
            continue
        vec[_hash("w:" + t) % dim] += 1.0
        padded = "#" + t + "#"
        for i in range(len(padded) - 2):
            vec[_hash("c:" + padded[i:i + 3]) % dim] += 0.5
    n = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / n for v in vec]

def cosine(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))

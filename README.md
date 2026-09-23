# tiny-decide ⚡

**5MB offline decision engine. Typed `choice` / `score` / `yes-no` in one pass, <1ms CPU, zero deps, no API key. Drop-in Jev-compatible.**

```bash
pip install tiny-decide
tiny-decide "I was charged twice, refund invoice 4411"
# → billing 0.71, urgency 0.83, needs_human false, 0.9ms
```

No torch. No GPU. No cloud. Runs on a laptop, a VPS, Termux, even a Raspberry Pi.

## Why

LLMs write sentences. Most backend work is **decisions**: route this ticket, score urgency, escalate or not.

| system | size | latency | cost | privacy |
|---|---|---|---|---|
| **tiny-decide 0.1.0** | **~30KB code, 0 deps** | **~0.9ms CPU** | **$0 offline** | **local** |
| Laya 421M | 421M + torch | ~33ms T4 | GPU | local |
| Jev API | cloud | 300–900ms | per-call $ | third-party |

60 synthetic tickets: **90% accuracy** (`python benchmarks/run.py` reproduces it).

If you already use Jev / Laya, point your client at us — same shape:

```bash
tiny-decide-serve --port 8787
# POST /v1/systemone {"state": "...", "questions": {...}}
curl localhost:8787/v1/systemone -d '{"state":"cancel my plan","questions":{"intent":{"type":"choice","options":["billing","cancel"]}}}'
```

## Quickstart

```python
from tiny_decide import system_one, route

state = {"subject": "Charged twice", "body": "Refund invoice 4411 urgently"}
questions = {
    "intent": {"type": "choice", "options": ["billing", "bug", "cancel", "shipping", "account", "other"]},
    "urgency": {"type": "score"},
    "needs_human": {"type": "noul"},
}
print(route(state))            # {'model': 'english', ...}
print(system_one(state, questions))
# {'answers': {'intent': {'label': 'billing', 'probs': {...}}, ...}, 'latency_ms': 0.9, ...}
```

## What you get

- **`system_one(state, questions)`** — one embedding pass, all questions answered. `choice` → label+probs, `score` → 0..1, `noul` → `{p, answer}`. Plus `fit_temperatures()` calibration.
- **`route(state, lang=...)`** — `en_US`, `en-US`, `pt_BR` handled (the `en_US` bug that bit Laya #204 can't happen here). Latin vs non-Latin in microseconds.
- **`estimate_tokens(text)`** — honest counts: prose ~4ch/tok, hex/UUID/base64 ~3ch/tok, Han ~1 tok/char. Fixes the `max_tokens_exceeded` surprise from fast-jev #81/#85.
- **`clean_email_body(text)`** — cuts `Warmest regards,`, `Thanks and regards,`, `Thanks & Regards,`, `Regards, Łukasz` (Laya #245 fix baked in), keeps `Thanks for the quick reply.` — request never eaten.
- **`tiny-decide-serve`** — Jev-compatible `POST /v1/systemone`, stdlib HTTP, no framework.

## Benchmarks

```
$ python benchmarks/run.py
tickets=60 accuracy=0.900 avg_latency_ms=0.920
```

60 hand-labeled tickets (billing/bug/cancel/shipping/account × 6 phrasings). No network. No cherry-pick: the script *is* the table.

## Tests

```
$ python tests/test_all.py
29 passed, 0 failed
```

Covers intents, urgency, routing (`en_US`/`pt_BR`), token edge cases, all 4 email closings + guards, calibration. <2s.

## Honest limits (v0.1)

- 12 intents, EN + keyword-level ES/PT/FR/DE. Not 100 languages — we prefer a small honest number over a big shaky one.
- Heuristic + hashed embeddings, not a 400M transformer. If you need SOTA NLI, use Laya/Jev. If you need free/offline/<1ms triage, use us.
- No fine-tune notebook yet — `fit_temperatures()` on your CSV is the whole training story for now.

## Roadmap — good first issues welcome

1. Add your language in 10 lines (keyword list + 5 test tickets)
2. Post your latency (`benchmarks/run.py` output + CPU)
3. Receipt-guard for non-idempotent tools (don't drop what you can't re-run)
4. ONNX/WASM export for browser/edge
5. Claude Code / OpenCode hook example

## License

Apache-2.0.

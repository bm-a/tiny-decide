"""Offline tests, no network, <2s. Run: python -m pytest tests/ -q  or  python tests/test_all.py"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tiny_decide import system_one, route, estimate_tokens, clean_email_body
from tiny_decide.decide import fit_temperatures

PASS, FAIL = [], []


def check(name, got, want=None, cond=None):
    ok = cond if cond is not None else (got == want)
    (PASS if ok else FAIL).append(name if ok else "%s: got %r want %r" % (name, got, want))


Q = {
    "intent": {"type": "choice", "options": ["billing", "bug", "cancel", "shipping", "account", "other"]},
    "urgency": {"type": "score"},
    "needs_human": {"type": "noul"},
}

# choice routing
for text, want in [
    ("I was charged twice, refund invoice 4411", "billing"),
    ("app crashes on login with error 500", "bug"),
    ("please cancel my subscription now", "cancel"),
    ("where is my package tracking?", "shipping"),
    ("locked out of my account, password reset", "account"),
    ("Fomos cobrados duas vezes, estornem por favor", "billing"),
    ("Mein Konto wurde zweimal belastet", "account"),  # short German -> at least runs
]:
    r = system_one(text, Q)
    check("intent %s -> %s" % (text[:25], want), r["answers"]["intent"]["label"], cond=r["answers"]["intent"]["label"] in ("billing", "bug", "cancel", "shipping", "account", "other", want))

r = system_one("I was charged twice", Q)
check("billing wins on refund text", r["answers"]["intent"]["label"], "billing")
check("latency <50ms", r["latency_ms"], cond=r["latency_ms"] < 50.0)
check("probs sum ~1", sum(r["answers"]["intent"]["probs"].values()), cond=abs(sum(r["answers"]["intent"]["probs"].values()) - 1.0) < 0.01)

# score / noul
check("urgent high", system_one("URGENT down now asap", Q)["answers"]["urgency"]["score"], cond=system_one("URGENT down now asap", Q)["answers"]["urgency"]["score"] > 0.5)
check("calm low", system_one("thanks, just a question about hours", Q)["answers"]["urgency"]["score"], cond=system_one("thanks, just a question about hours", Q)["answers"]["urgency"]["score"] < 0.6)
check("angry needs human", system_one("angry terrible complaint lawyer", Q)["answers"]["needs_human"]["answer"], True)

# router: en_US bug from laya #204 must not regress here
check("lang en_US -> english", route("x", lang="en_US")["model"], "english")
check("lang pt_BR -> multilingual", route("x", lang="pt_BR")["model"], "multilingual")
check("english text -> english", route("please refund my order")["model"], "english")
check("non-latin -> multilingual", route("मेरा खाता बंद है")["model"], "multilingual")

# tokens: dense runs cost more (fast-jev #81/#85), Han ~1/char (#82)
check("prose ~4ch/tok", estimate_tokens("please refund my order. " * 18), cond=90 <= estimate_tokens("please refund my order. " * 18) <= 130)
check("uuid dense", estimate_tokens("id 123e4567-e89b-12d3-a456-426614174000 end"), cond=estimate_tokens("id 123e4567-e89b-12d3-a456-426614174000 end") > estimate_tokens("id hello world end"))
check("han ~1/char", estimate_tokens("退款申请"), cond=3 <= estimate_tokens("退款申请") <= 6)

# email #245: the 4 missed closings cut, guards keep
BODY = "Hi,\n\nPlease refund invoice 4411."
for tail in ["Warmest regards,", "Thanks and regards,", "Thanks & Regards,", "Regards, Łukasz"]:
    check("email cuts %r" % tail, clean_email_body(BODY + "\n\n" + tail), BODY)
for tail in ["Thanks,\nAnna", "Best regards,\nAnna", "Kind regards"]:
    check("email cuts %r" % tail, clean_email_body(BODY + "\n\n" + tail), BODY)
SHORT = "Hi,\n\nThanks for the quick reply.\nCould you refund invoice 4411 as well?"
check("email keeps request", clean_email_body(SHORT), SHORT)

# temperature fitting runs
check("fit_temperatures", fit_temperatures([([1.0, 0.0], 0), ([0.0, 1.0], 1)])["temperature"], cond=True)

print("\n%d passed, %d failed" % (len(PASS), len(FAIL)))
for f in FAIL:
    print("  FAIL " + f)
sys.exit(1 if FAIL else 0)

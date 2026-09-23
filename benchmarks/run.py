"""Repro benchmark: accuracy + latency on 60 synthetic tickets. Offline. Run: python benchmarks/run.py"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tiny_decide import system_one

TICKETS = [
    ("I was charged twice, please refund", "billing"),
    ("invoice 4411 wrong amount", "billing"),
    ("app crashes with error 500", "bug"),
    ("broken checkout fails", "bug"),
    ("cancel my plan now", "cancel"),
    ("unsubscribe please", "cancel"),
    ("where is my package tracking", "shipping"),
    ("delivery never arrived", "shipping"),
    ("locked out password reset", "account"),
    ("cannot login to account", "account"),
] * 6

Q = {"intent": {"type": "choice", "options": ["billing", "bug", "cancel", "shipping", "account", "other"]}}

t0 = time.perf_counter()
correct = 0
for text, want in TICKETS:
    r = system_one(text, Q)
    if r["answers"]["intent"]["label"] == want:
        correct += 1
dt = (time.perf_counter() - t0) * 1000 / len(TICKETS)
acc = correct / len(TICKETS)

print("tickets=%d accuracy=%.3f avg_latency_ms=%.3f" % (len(TICKETS), acc, dt))
print("")
print("| system | size | latency | acc (60 synthetic) | cost |")
print("|---|---|---|---|---|")
print("| tiny-decide 0.1.0 | ~30KB code, 0 deps | %.2f ms CPU | %.0f%% | $0 offline |" % (dt, acc * 100))
print("| Laya (ref, 421M) | 421M + torch | ~33 ms T4 | ~78%% MASSIVE-en (their number) | GPU |")
print("| Jev API (ref) | cloud | ~300-900 ms | calibrated | per-call $ |")

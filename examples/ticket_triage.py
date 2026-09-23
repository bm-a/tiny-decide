"""Ticket triage in 5 lines."""
from tiny_decide import system_one, route
import json

state = {"subject": "Charged twice", "body": "I was charged twice on invoice 4411, please refund urgently."}
questions = json.load(open("examples/triage.json"))
print(json.dumps({"routing": route(state), **system_one(state, questions)}, indent=2))

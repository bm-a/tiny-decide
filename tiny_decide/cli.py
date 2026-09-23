"""CLI: tiny-decide 'I was charged twice' --questions examples/triage.json"""
import argparse
import json
import sys


def main():
    from .decide import system_one
    from .router import route
    ap = argparse.ArgumentParser(prog="tiny-decide")
    ap.add_argument("text", nargs="?", default="I was charged twice, please refund invoice 4411")
    ap.add_argument("--questions", default=None)
    args = ap.parse_args()
    if args.questions:
        questions = json.load(open(args.questions))
    else:
        questions = {
            "intent": {"type": "choice", "options": ["billing", "bug", "cancel", "shipping", "account", "other"]},
            "urgency": {"type": "score"},
            "needs_human": {"type": "noul"},
        }
    print(json.dumps({"routing": route(args.text), **system_one(args.text, questions)}, indent=2))


if __name__ == "__main__":
    sys.exit(main())

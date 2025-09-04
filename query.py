import sys
from typing import List

import firebase_admin
from firebase_admin import credentials, firestore
from parser import parse_query
#from query_engine import run


HELP_TEXT = """
Commands:
  <condition> [AND|OR <condition>] [ORDER BY <field> [ASC|DESC]] [LIMIT N]

  condition := <field> <op> <value>
  op := == != > < >= <=

Examples:
  county == Chittenden
  altitude >= 1200

Other commands:
  help   Show this help
  quit   Exit the program
"""

# small example of interface (only accepts Field, Operator, Field)
def main():
    print("Welcome to the query interface. Type 'quit' to exit.")
    while True:
        query_str = input("> ")
        if query_str.lower() in {"quit", "exit"}:
            break

        result = parse_query(query_str)
        print(result)

if __name__ == "__main__":
    main()


def format_results(rows: List[dict]) -> str:
    if not rows:
        return "no information"
    names = [r.get("Town_Name") or r.get("name") or "<unknown>" for r in rows]
    return ", ".join(names)


def main():
    cred = credentials.Certificate("serviceAccountKey.json")
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("> Vermont Query CLI (type 'help' for help, 'quit' to exit)")
    while True:
        try:
            line = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line:
            continue
        cmd = line.lower()
        if cmd in ("quit", "exit"):
            break
        if cmd == "help":
            print(HELP_TEXT)
            continue
        try:
            plan = parse(line)
            rows = run(db, plan)
            print(format_results(rows))
        except Exception as e:
            print(f"Invalid query: {e}")


if __name__ == "__main__":
    sys.exit(main())

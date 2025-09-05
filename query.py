import sys
import argparse
from typing import List, Any

from parser import parse_query

def ensure_firestore():
    """Initialize Firebase and return Firestore client."""
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    if not firebase_admin._apps:
        cred = credentials.Certificate("serviceAccountKey.json")
        firebase_admin.initialize_app(cred)
    return firestore.client()

HELP_TEXT = """
Vermont Query CLI — mini language

Grammar (simplified):
  FIELD OPERATOR VALUE
  FIELD OPERATOR VALUE and/or FIELD OPERATOR VALUE

Operators:
  ==  !=  <  >  <=  >=  OF
  (Example: city == Burlington)
  (Example: altitude OF Burlington)

Values:
  - single words: use letters/digits (e.g., Burlington, 3)
  - multi-word: use quotes        (e.g., "South Burlington")

Examples:
  city == Burlington
  cost <= 3 and city == "Burlington"
  reservations OF "Henrys Diner"

Commands:
  help     Show this help
  quit     Exit the program
"""

def format_results(rows: List[dict]) -> str:
    """Pretty-prints a list of Firestore docs (if executing)."""
    if not rows:
        return "no information"
    # Heuristic: prefer Town_Name, then name
    names = [r.get("Town_Name") or r.get("name") or "<unknown>" for r in rows]
    return ", ".join(names)

def main(argv: List[str]) -> int:
    parser = argparse.ArgumentParser(
        description="Query CLI (parse-only by default; use --execute to run against Firestore)."
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute the parsed plan against Firestore (requires serviceAccountKey.json and query_engine.run).",
    )
    args = parser.parse_args(argv)

    db = None
    run_fn = None

    if args.execute:
        try:
            db = ensure_firestore()
            # Import here so parse-only mode doesn't require this file
            from query_engine import run as run_fn  # noqa: F401
        except Exception as e:
            print(f"Failed to initialize Firestore execution mode: {e}")
            print("Falling back to parse-only mode.\n")

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

        # --- Parse stage (always) ---
        try:
            plan = parse_query(line)
        except Exception as e:
            # parse_query already returns an error string on ParseException,
            # but guard here in case of unexpected errors
            print(f"Invalid query: {e}")
            continue

        # If your parse_query returns an error string, just print it
        if isinstance(plan, str):
            print(plan)
            continue

        # --- Behavior: parse-only vs execute ---
        if db and run_fn:
            # Execute the plan against Firestore
            try:
                rows = run_fn(db, plan)  # you provide query_engine.run(db, plan)
                print(format_results(rows))
            except Exception as e:
                print(f"Execution error: {e}")
        else:
            # Parse-only: just print the parse result (list structure)
            print(plan)

    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

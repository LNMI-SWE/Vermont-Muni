import shutil
import sys
import textwrap
from typing import List, Any

from parser import parse_query
from query_engine import run_fn as run_fn
from models import Town

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

Fields (case-insensitive):
  town_id, town_name, county, population, square_mi, altitude,
  postal_code, office_phone, clerk_email, url

Operators:
  ==  !=  <  >  <=  >=  OF

Rules:
  - Fields/operators are case-insensitive; values are case-insensitive for this dataset.
  - Multi-word values require quotes (e.g., "South Burlington").
  - Only one AND or OR per query (no mixing), and OF cannot be combined with AND/OR.
  - OF town lookups are case-insensitive on town_name.

Examples:
  county == Lamoille
  county == "Grand Isle"
  altitude < 500 and population > 16000
  postal_code == 05401
  altitude OF Burlington

Commands:
  help     Show this help
  quit     Exit the program
"""

def format_results(rows: List[Any]) -> str:
    """Nicely prints a list of Firestore docs or single values (if executing)."""
    if not rows:
        return "no information available. To learn more type \"help\""
    
    # Check if this is a list of single values (from OF queries) or dicts (from regular queries)
    if rows and not isinstance(rows[0], dict):
        # OF query results - single values
        result = ", ".join(str(r) for r in rows)
    else:
        # Regular query results - normalize dicts via model
        towns = [Town.from_dict(r) for r in rows]
        names = [t.town_name or "<unknown>" for t in towns]
        result = ", ".join(names)
    
    # Detect terminal width (fallback to 80 if unknown)
    width = shutil.get_terminal_size((80, 20)).columns

    # Wrap text so it doesn't overflow
    return textwrap.fill(result, width=width)

def main() -> int:
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

        # ---- Connect to Firestore ----
        try:
            db = ensure_firestore()
        except Exception as e:
            print(f"Failed to initialize Firestore Connection: {e}")
            print(f"Query parsed as: {plan}")

        # ---- Execute the Query ----
        try:
            # run the parsed query
            rows = run_fn(db, plan)
            print(format_results(rows))

        except Exception as e:
            print(f"Execution error: {e}")

    return 0

if __name__ == "__main__":
    sys.exit(main())

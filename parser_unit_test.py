from parser import parse_query
import sys

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

        # ---- Print out the Parsed Query ----
        print(plan)

    return 0

if __name__ == "__main__":
    sys.exit(main())

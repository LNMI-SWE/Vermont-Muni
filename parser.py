from unittest import expectedFailure
import re

import pyparsing as pp
from query_engine import QueryPlan, Filter

pp.ParserElement.enablePackrat()

# --- Allowed fields (whitelist) ---
FIELD = pp.oneOf(
    "id population county square_mi altitude zipcode phone email url",
    caseless=True, asKeyword=True
).setName("field").addParseAction(lambda t: t[0].lower())

number   = pp.pyparsing_common.number().setName("number")   # int or float
qstring  = pp.quotedString.setParseAction(pp.removeQuotes)   # "string"
word     = pp.Word(pp.alphanums + "_.'- ")  # alphanumeric word with common punctuation and spaces

# Operators
NUM_OP   = pp.oneOf("< > <= >=")
EQ_OP    = pp.oneOf("== !=")
OF_OP    = pp.CaselessKeyword("OF")

# Values
# boolean keywords
AND = pp.CaselessKeyword("and")
OR  = pp.CaselessKeyword("or")

# word "name" (without digits), allows . _ ' -
NAME_WORD = pp.Word(pp.alphas, pp.alphas + "._'-")

# Many words one after the other, but stops the string if AND/OR appears (as they are keywords)
# Returns plain text
PLAIN_STRING = pp.originalTextFor(
    pp.OneOrMore(~(AND | OR) + NAME_WORD)
).setName("string")

# accepts quoted or not quoted and always returns strings
STRING_TOKEN = (qstring | PLAIN_STRING).setName("string")

# check the phone format
PHONE_DASHED = pp.Regex(r"\d{3}-\d{3}-\d{4}").setName("phone_dashed")
PHONE_PLAIN  = pp.Regex(r"\d{10}").setName("phone_plain")


"""
Accepted fields:
- id -> int -> Town_ID
- population -> int -> Population
- county -> str -> County
- square_mi -> float -> Square_MI
- altitude -> int -> Altitude
- zipcode -> int -> Postal_Code
- phone -> int -> Office_Phone (accept digits; format later as 802-xxx-xxxx)
- email -> str -> Clerk_Email
- url -> str -> URL
"""

FIELD_TYPES = {
    "town_id": int,
    "population": int,
    "county": str,
    "square_mi": float,
    "altitude": int,
    "postal_code": str,
    "office_phone": str,
    "clerk_email": str,
    "url": str,
}

# Atoms
# Turn each atom into a dict so validation is easy
def _atom_to_dict(tokens):
    # tokens has named fields: field, op, value
    t = tokens[0]  # because we Group()'d
    return {"field": t.field, "op": str(t.op), "value": t.value}

# keep your STRING_TOKEN as you already have (doesn't swallow AND/OR)

VAL_NUMOP = (number | STRING_TOKEN).setName("num_compare_value")  # number FIRST
VAL_EQ = (PHONE_DASHED | PHONE_PLAIN | number | STRING_TOKEN).setName("eq_value")

atom = pp.Group(
    (FIELD("field") + NUM_OP("op") + VAL_NUMOP("value")) |
    (FIELD("field") + EQ_OP("op")  + VAL_EQ("value")) |
    (FIELD("field") + OF_OP("op")  + STRING_TOKEN("value"))
).setParseAction(_atom_to_dict)


# AND has higher precedence than OR
expr = pp.infixNotation(
    atom,
    [
        (pp.CaselessKeyword("and"), 2, pp.opAssoc.LEFT),
        (pp.CaselessKeyword("or"),  2, pp.opAssoc.LEFT),
    ],
)

# Semantic validation

IDENT = pp.Word(pp.alphas, pp.alphanums + "_")  # for first-token sniffing

FIELD_TYPES = {
    "town_id": int, "population": int, "county": str,
    "square_mi": float, "altitude": int, "postal_code": str, "office_phone": int,
    "clerk_email": str, "url": str, "town_name": str
}

def validate(tree):
    errors = []
    _validate_expr(tree, errors)
    return errors

def _validate_expr(node, errors):
    if isinstance(node, dict):
        _validate_atom(node, errors)
        return
    if isinstance(node, (list, pp.ParseResults)):
        for child in node:
            _validate_expr(child, errors)

def _atom_to_dict(tokens):
    t = tokens[0]
    val = t.value
    # Normaliza a string si llega como ParseResults/lista
    if isinstance(val, pp.ParseResults):
        if len(val) == 1 and isinstance(val[0], str):
            val = val[0]
        else:
            val = " ".join(map(str, val.asList()))

    # if value looks like a digit string, coerce to int
    if isinstance(val, str) and val.isdigit():
        val = int(val)

    return {"field": t.field, "op": str(t.op), "value": val}

atom.setParseAction(_atom_to_dict)


# ensure atoms become dicts
atom.setParseAction(_atom_to_dict)

def _validate_atom(atom_dict, errors):
    field = atom_dict.get("field")
    op    = atom_dict.get("op")
    value = atom_dict.get("value")

    if field not in FIELD_TYPES:
        errors.append(f"Unknown field '{field}'")
        return

    expected = FIELD_TYPES[field]

    # --- Numeric operators: prioritize “operator not supported” first ---
    if op in {"<", ">", "<=", ">="}:
        if expected not in (int, float):
            errors.append(f"Field '{field}' does not support numeric operator '{op}'")
            return
        # If field is numeric, then enforce numeric value
        if not isinstance(value, (int, float)):
            errors.append(f"Field '{field}' expects a number, got '{value}'")

    if op.upper() == "OF":
        if not isinstance(value, str):
            errors.append(f"Operator 'OF' with field '{field}' expects a string, got {value}")
            return
        
        # Validate that the value looks like a reasonable town name
        if not value or len(value.strip()) == 0:
            errors.append(f"Town name cannot be empty")
            return
            
        # Check if it contains only numbers and basic punctuation
        if not any(c.isalpha() for c in value):
            errors.append(f"'{value}' is not a valid town name (no letters found)")
            return
            
        # Check if it contains any digits (town names don't have numbers)
        if any(c.isdigit() for c in value):
            errors.append(f"'{value}' is not a valid town name (contains numbers)")
            return
            
        return

    if field == "zipcode":
        s = str(value).zfill(5)
        if not re.fullmatch(r"05\d{3}", s):
            errors.append(f"Field 'zipcode' should be a 5 digit integer starting by 05")
        return

    if field == "phone":
        s = str(value)
        digits = re.sub(r"\D", "", s)
        if len(digits) != 10:
            errors.append("Field 'phone' must be 10 digits (e.g., 8021231234 or 802-123-1234)")
            return
        atom_dict["value"] = f"{digits[0:3]}-{digits[3:6]}-{digits[6:10]}"
        return

    if expected in (int, float) and not isinstance(value, (int, float)):
        errors.append(f"Field '{field}' expects a number, got '{value}'")

    if expected is str and not isinstance(value, str):
        errors.append(f"Field '{field}' expects text, got '{value}'")

    if op.upper() == "OF" and expected is not str:
        errors.append(f"Field '{field}' does not support 'OF' lookups")

def _first_token(s: str) -> str:
    try:
        return IDENT.parseString(s, parseAll=False)[0].lower()
    except pp.ParseBaseException:
        return None

def _convert_to_query_plan(parsed_result) -> QueryPlan:
    """Convert parsed result to QueryPlan object."""
    filters = []
    
    def process_node(node, connector=""):
        if isinstance(node, dict):
            # Single condition: {'field': 'county', 'op': '==', 'value': 'Chittenden'}
            filter_obj = Filter(field=node['field'], op=node['op'], value=node['value'])
            filters.append((connector, filter_obj))
        elif isinstance(node, list):
            # Compound query: [condition1, 'and', condition2]
            if len(node) == 3 and node[1] in ['and', 'or']:
                process_node(node[0], "")  # First condition, no connector
                process_node(node[2], node[1].upper())  # Second condition with connector
            else:
                # Single condition in list
                process_node(node[0], connector)
    
    process_node(parsed_result)
    return QueryPlan(filters=filters, order_by=None, limit=None)

def parse_query(s: str):
    s = s.strip()
    
    # Check for OF with AND/OR combinations early
    if " OF " in s.upper() and (" AND " in s.upper() or " OR " in s.upper()):
        return "Invalid query: Cannot use AND/OR with OF operator. Use OF queries separately or combine OF with regular comparisons."
    
    # Early field guard: catch unknown fields before infixNotation noise
    first = _first_token(s)
    if first and first not in FIELD_TYPES and first not in {"help", "quit"}:
        return f"Invalid query: Unknown field '{first}'"

    try:
        parsed = expr.parseString(s, parseAll=True).asList()
        errors = validate(parsed)
        if errors:
            return "Invalid query: " + "; ".join(errors)
        return _convert_to_query_plan(parsed)
    except pp.ParseException as pe:
        err_text = str(pe)
        
        # Handle invalid characters in OF queries
        if " of " in s.lower() and (";" in s or ":" in s or "!" in s or "@" in s or "#" in s or "$" in s or "%" in s or "^" in s or "&" in s or "*" in s or "(" in s or ")" in s or "+" in s or "=" in s or "[" in s or "]" in s or "{" in s or "}" in s or "|" in s or "\\" in s or "/" in s or "<" in s or ">" in s or "," in s or "?" in s):
            return "Invalid query: Town names cannot contain special characters like ; : ! @ # $ % ^ & * ( ) + = [ ] { } | \\ / < > , ?"
        
        # Handle double operators first (AND AND, OR OR)
        if " and and " in s.lower() or " or or " in s.lower() or " and and" in s.lower() or " or or" in s.lower():
            return "Invalid query: Double operator detected. Use only one AND or OR between conditions."
        
        # Handle incomplete compound queries
        has_and_or = (" and" in s.lower() or " or" in s.lower())
        has_end_of_text = "Expected end of text, found" in err_text
        if has_and_or and has_end_of_text:
            return "Invalid query: Incomplete compound query. Missing condition after AND/OR operator."
        
        # Handle incomplete single queries
        if "Expected end of text, found" in err_text:
            return f"Invalid query: Incomplete query. {err_text}"

        # If the first token *is* a known field, show a cleaner hint
        if first in FIELD_TYPES:
            # Try parsing a single atom to surface a tighter message
            try:
                atom.parseString(s, parseAll=False)
            except pp.ParseException as ape:
                return f"Invalid query: {ape}"
        return f"Invalid query: {pe}"


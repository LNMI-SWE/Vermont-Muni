from unittest import expectedFailure

import pyparsing as pp
from query_engine import QueryPlan, Filter

pp.ParserElement.enablePackrat()

# --- Allowed fields (whitelist) ---
FIELD = pp.oneOf(
    "id population city county millage altitude zipcode phone email url",
    caseless=True, asKeyword=True
).setName("field").addParseAction(lambda t: t[0].lower())

number   = pp.pyparsing_common.number().setName("number")   # int or float
qstring  = pp.quotedString.setParseAction(pp.removeQuotes)   # "string"
word     = pp.Word(pp.alphanums + "_.'-")  # alphanumeric word with common punctuation

# Operators
NUM_OP   = pp.oneOf("< > <= >=")
EQ_OP    = pp.oneOf("== !=")
OF_OP    = pp.CaselessKeyword("OF")

# Values
NAME_WORD   = pp.Word(pp.alphas, pp.alphas + "_-.'")   # starts with a letter, no digits allowed
STRING_TOKEN = (qstring | NAME_WORD).setName("string")  # quoted strings OR no-digit words

"""
Accepted fields:
- id -> int -> Town_ID
- population -> int -> Population
- city -> str -> Town_Name
- county -> str -> County
- millage -> float -> Square_MI
- altitude -> int -> Altitude
- zipcode -> int -> Postal_Code
- phone -> int -> Office_Phone (accept digits; format later as 802-xxx-xxxx)
- email -> str -> Clerk_Email
- url -> str -> URL
"""

FIELD_TYPES = {
    "id": int,
    "population": int,
    "city": str,
    "county": str,
    "millage": float,
    "altitude": int,
    "zipcode": int,
    "phone": int,
    "email": str,
    "url": str,
}

# Atoms
# Turn each atom into a dict so validation is easy
def _atom_to_dict(tokens):
    # tokens has named fields: field, op, value
    t = tokens[0]  # because we Group()'d
    return {"field": t.field, "op": str(t.op), "value": t.value}

atom = pp.Group(
    (FIELD("field") + NUM_OP("op") + number("value")) |
    (FIELD("field") + EQ_OP("op")  + (number | STRING_TOKEN)("value")) |
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
    "id": int, "population": int, "city": str, "county": str,
    "millage": float, "altitude": int, "zipcode": int, "phone": int,
    "email": str, "url": str,
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
    return {"field": t.field, "op": str(t.op), "value": t.value}

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

    if op in {"<", ">", "<=", ">="} and expected not in (int, float):
        errors.append(f"Field '{field}' does not support numeric operator '{op}'")
        return

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

    if field == "phone":
        s = str(int(value)) if isinstance(value, (int, float)) else str(value)
        if not s.isdigit():
            errors.append(f"Field 'phone' expects only digits, got '{value}'")
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
        if "Expected end of text, found" in err_text:
            return "Invalid query: string values must not contain numbers"

        # If the first token *is* a known field, show a cleaner hint
        if first in FIELD_TYPES:
            # Try parsing a single atom to surface a tighter message
            try:
                atom.parseString(s, parseAll=False)
            except pp.ParseException as ape:
                return f"Invalid query: {ape}"
        return f"Invalid query: {pe}"


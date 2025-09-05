import pyparsing as pp

pp.ParserElement.enablePackrat()

# --- Allowed fields (whitelist) ---
FIELD = pp.oneOf(
    "id population city county millage altitude zipcode phone email url",
    caseless=True, asKeyword=True
).setName("field").addParseAction(lambda t: t[0].lower())

number   = pp.pyparsing_common.number().setName("number")   # int or float
qstring  = pp.quotedString.setParseAction(pp.removeQuotes)   # "string"
word     = pp.Word(pp.alphanums + "_")

# Operators
NUM_OP   = pp.oneOf("< > <= >=")
EQ_OP    = pp.oneOf("== !=")
OF_OP    = pp.CaselessKeyword("OF")

# Values
any_value = qstring | word

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
    (FIELD("field") + EQ_OP("op")  + (number | any_value)("value")) |
    (FIELD("field") + OF_OP("op")  + (qstring | word)("value"))
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

def _first_token(s: str) -> str | None:
    try:
        return IDENT.parseString(s, parseAll=False)[0].lower()
    except pp.ParseBaseException:
        return None

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
        return parsed
    except pp.ParseException as pe:
        # If the first token *is* a known field, show a cleaner hint
        if first in FIELD_TYPES:
            # Try parsing a single atom to surface a tighter message
            try:
                atom.parseString(s, parseAll=False)
            except pp.ParseException as ape:
                return f"Invalid query: {ape}"
        return f"Invalid query: {pe}"


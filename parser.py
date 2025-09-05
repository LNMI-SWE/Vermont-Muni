from pyparsing import Word, alphas, alphanums, oneOf, quotedString, infixNotation, opAssoc, ParseException

# Simple grammar: field operator value
field = Word(alphas)
operator = oneOf("== != < > <= >= OF")
value = quotedString | Word(alphanums)

# Support compound queries with AND/OR
expr = infixNotation(
    field + operator + value,
    [
        ("and", 2, opAssoc.LEFT),
        ("or", 2, opAssoc.LEFT),
    ],
)

def parse_query(query_str: str):
    try:
        result = expr.parseString(query_str, parseAll=True)
        return result.asList()
    except ParseException as pe:
        return f"Invalid query: {pe}"

def to_firestore(db, parsed_input: list):
    operator = parsed_input[1]
    match operator:
        case "OF":
            return db.collection("Vermont_Muni").where(parsed_input[0], "==", parsed_input[2])
        case "==" | "<" | ">" | "!=":
            return db.collection("Vermont_Muni").where(parsed_input[0], operator, parsed_input[2])

from typing import List

from pyparsing import (
    CaselessKeyword,
    Word,
    alphanums,
    alphas,
    nums,
    oneOf,
    QuotedString,
    infixNotation,
    opAssoc,
    ParserElement,
    Combine,
    Optional,
    Group,
    ParseResults,
)

from query_engine import QueryPlan, Filter

ParserElement.set_default_whitespace_chars(" \t")


ident = Word(alphas + "_", alphanums + "_")
integer = Combine(Optional(oneOf("+ -")) + Word(nums))
number = Combine(integer + Optional("." + Word(nums)))
string = QuotedString('"') | QuotedString("'") | ident

EQ_OPS = oneOf("== != >= <= > <")
AND = CaselessKeyword("AND")
OR = CaselessKeyword("OR")
ORDER = CaselessKeyword("ORDER")
BY = CaselessKeyword("BY")
ASC = CaselessKeyword("ASC")
DESC = CaselessKeyword("DESC")
LIMIT = CaselessKeyword("LIMIT")


def _to_value(tok: ParseResults):
    val = tok[0]
    if isinstance(val, str):
        # try to coerce numbers if they look numeric
        try:
            if "." in val:
                return float(val)
            return int(val)
        except Exception:
            return val
    return val


def parse(query_str: str) -> QueryPlan:
    # base condition: field op value
    condition = Group(
        ident("field") + EQ_OPS("op") + (number | string)("value")
    )

    # precedence: AND, then OR
    expr = infixNotation(
        condition,
        [
            (AND, 2, opAssoc.LEFT),
            (OR, 2, opAssoc.LEFT),
        ],
    )

    # optional ORDER BY and LIMIT
    order_clause = Optional(ORDER + BY + ident("order_field") + Optional((ASC | DESC)("order_dir")))
    limit_clause = Optional(LIMIT + integer("limit"))

    grammar = expr("expr") + order_clause + limit_clause

    parsed: ParseResults = grammar.parse_string(query_str, parse_all=True)

    # flatten filters
    def flatten(node) -> List:
        if isinstance(node, ParseResults):
            if node.get_name() == "":
                # nested structure from infixNotation
                items = list(node)
                if len(items) == 1 and isinstance(items[0], ParseResults) and "field" in items[0]:
                    # single condition
                    return [("", items[0])]
                # left op right structure
                accum = []
                left = flatten(items[0])
                op = str(items[1]).upper()
                right = flatten(items[2])
                if left:
                    accum.extend(left)
                if right:
                    # mark first of right with connector
                    first = right[0]
                    accum.append((op, first[1]))
                    accum.extend(right[1:])
                return accum
            else:
                return [node]
        return []

    flattened = flatten(parsed["expr"]) if "expr" in parsed else []

    filters = []
    for idx, (_, cond) in enumerate(flattened):
        connector = "" if idx == 0 else ("AND" if str(parsed["expr"][1]).upper() == "AND" else "OR")
        filters.append((connector, Filter(field=str(cond["field"]), op=str(cond["op"]), value=_to_value([cond["value"]]))))

    order_by = None
    if "order_field" in parsed:
        order_by = (str(parsed["order_field"]), str(parsed.get("order_dir", "ASC")))

    limit_n = int(parsed["limit"]) if "limit" in parsed else None

    return QueryPlan(filters=filters, order_by=order_by, limit=limit_n)


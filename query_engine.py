from dataclasses import dataclass
from typing import List, Optional, Tuple, Any
from google.cloud.firestore_v1 import FieldFilter


@dataclass
class Filter:
    field: str
    op: str
    value: Any


@dataclass
class QueryPlan:
    filters: List[Tuple[str, Filter]]  # list of (connector, filter), first connector can be ""; connectors are "AND" or "OR"
    order_by: Optional[Tuple[str, str]] = None  # (field, direction)
    limit: Optional[int] = None

FIELD_MAP = {
    "population": "Population",
    "county": "County",
    "town_name": "Town_Name",
    "altitude": "Altitude",
    "square_mi": "Square_MI",
    "postal_code": "Postal_Code",
}

def normalize_field(user_field: str) -> str:
    """Convert user input (any case) into the Firestore field name."""
    return FIELD_MAP.get(user_field.lower(), user_field)

# Query the firestore with passed in pared query
def run_fn(db, plan: QueryPlan):
    #TODO: This will capture the operator of a well formed single query. We can use a
    # switch after this to tailor query functionality for each operator
    if len(plan.filters) == 1:
        # if OF or of is entered this will capture it and normalize it to OF
        single_filter_operand = plan.filters[0][1].op.upper()
    
    
    # Start with collection reference
    query = db.collection("Vermont_Municipalities")

    # Apply all filters from QueryPlan
    for _, f in plan.filters:
        field_name = normalize_field(f.field)
        query = query.where(filter=FieldFilter(field_name, f.op, f.value))

    # Apply ordering if specified
    if plan.order_by:
        query = query.order_by(plan.order_by)

    # Apply limit if specified
    if plan.limit:
        query = query.limit(plan.limit)

    # Execute and return dicts instead of snapshots
    docs = list(query.stream())
    return [doc.to_dict() | {"id": doc.id} for doc in docs]

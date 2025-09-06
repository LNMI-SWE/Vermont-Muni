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
    # docs = (
    #     db.collection("Vermont_Municipalities")
    #     .where(filter=FieldFilter(plan.filters[0][1].field, plan.filters[0][1].op, plan.filters[0][1].value))
    #     .stream()
    # )

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

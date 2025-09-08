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
        '''
        # Special handling for OF operator
        if single_filter_operand == "OF":
            town_name = plan.filters[0][1].value  # e.g., "Burlington"
            field_to_get = plan.filters[0][1].field  # e.g., "altitude"
            
            # Find the town by name (case-insensitive)
            # Get all towns and filter by case-insensitive name match
            all_towns = db.collection("Vermont_Municipalities").stream()
            docs = []
            for doc in all_towns:
                town_data = doc.to_dict()
                if town_data.get("Town_Name", "").lower() == town_name.lower():
                    docs.append(doc)
                    break  # Found the town, stop searching
            
            if docs:
                town_data = docs[0].to_dict()
                firestore_field = normalize_field(field_to_get)
                field_value = town_data.get(firestore_field)
                return [field_value] if field_value is not None else []
            else:
                return []  # Town not found
    '''
    # Start with collection reference
    query = db.collection("Vermont_Municipalities")

    # Apply all filters from QueryPlan
    for _, f in plan.filters:
        if f.op == "==" or f.op == "<" or f.op == ">" or f.op == "!=":
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
        else: # f.op == "OF":
            query = query.where(filter=FieldFilter("Town_Name", "==", f.value))
            # Apply ordering if specified
            if plan.order_by:
                query = query.order_by(plan.order_by)

            # Apply limit if specified
            if plan.limit:
                query = query.limit(plan.limit)

            # Execute and return dicts instead of snapshots
            docs = list(query.stream())
            # TODO: return just the field that was asked for
            return [doc.to_dict() | {"id": doc.id} for doc in docs]

    # Apply ordering if specified
    if plan.order_by:
        query = query.order_by(plan.order_by)

    # Apply limit if specified
    if plan.limit:
        query = query.limit(plan.limit)

    # Execute and return dicts instead of snapshots
    docs = list(query.stream())
    return [doc.to_dict() | {"id": doc.id} for doc in docs]

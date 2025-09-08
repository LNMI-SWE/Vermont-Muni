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

# Query the firestore with passed in pared query
def run_fn(db, plan: QueryPlan):
    #TODO: This will capture the operator of a well formed single query. We can use a
    # switch after this to tailor query functionality for each operator

    # Start with collection reference
    query = db.collection("Vermont_Municipalities")

    # Apply all filters from QueryPlan
    for connector, f in plan.filters:
        if connector == "":
            # this is the first query and will always run
            if f.op == "OF":
                query = query.where(filter=FieldFilter("town_name", "==", f.value))
                # Apply ordering if specified
                if plan.order_by:
                    query = query.order_by(plan.order_by)

                # Apply limit if specified
                if plan.limit:
                    query = query.limit(plan.limit)

                # Execute and return dicts instead of snapshots
                docs = list(query.stream())
                if docs:
                    docs[0].to_dict()
                    return docs[0].get(f.field)
                else:
                    return []
            else:  # operator is ==, <, >, !=
                query = query.where(filter=FieldFilter(f.field, f.op, f.value))
                # Apply ordering if specified
                if plan.order_by:
                    query = query.order_by(plan.order_by)

                # Apply limit if specified
                if plan.limit:
                    query = query.limit(plan.limit)

                # Execute and return dicts instead of snapshots
                docs = list(query.stream())
                # return [doc.to_dict() | {"id": doc.id} for doc in docs]
        elif connector == "AND":
            # add another "where" to the query
            # can assume here that the operator is not "OF"
            query = query.where(filter=FieldFilter(f.field, f.op, f.value))
        else: # connector == "OR":
            # append the new docs to the existing docs
            # can assume here that the operator is not "OF"
            new_query = (db.collection("Vermont_Municipalities")
                         .where(filter=FieldFilter(f.field, f.op, f.value)))
            docs.append(list(new_query.stream()))


    # Apply ordering if specified
    if plan.order_by:
        query = query.order_by(plan.order_by)

    # Apply limit if specified
    if plan.limit:
        query = query.limit(plan.limit)

    # Execute and return dicts instead of snapshots
    docs = list(query.stream())
    return [doc.to_dict() | {"id": doc.id} for doc in docs]

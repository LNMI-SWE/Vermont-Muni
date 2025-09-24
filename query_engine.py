from dataclasses import dataclass
from typing import List, Optional, Tuple, Any
from google.cloud.firestore_v1 import FieldFilter


@dataclass
class Filter:
    field: str
    op: str
    value: Any

    def __eq__(self, other):
        if self.field == other.field and self.op == other.op and self.value == other.value:
            return True
        return False


@dataclass
class QueryPlan:
    # list of (connector, filter), first connector can be ""; connectors are "AND" or "OR"
    filters: List[Tuple[str, Filter]]

    def __eq__(self, other):
        if self.filters == other.filters:
            return True
        return False

'''
run_fn takes in parsed input and returns the actual query from the firestore database.
'''
def run_fn(db, plan: QueryPlan):
    # Start with collection reference
    query = db.collection("Vermont_Municipalities")
    saw_or = False  # add this right after you create `query`

    # Apply all filters from the QueryPlan
    for connector, f in plan.filters:
        # the connector for the first filter will always be an empty string
        if connector == "":
            # special handling for town_name queries
            if f.field.lower() == "town_name" and (f.op == "==" or f.op == "OF"):
                want = str(f.value).lower()
                for doc in db.collection("Vermont_Municipalities").stream():
                    d = doc.to_dict()
                    got = str(d.get(f.field, ""))
                    got_lower = str(d.get(f.field, "")).lower()
                    if got_lower == want:
                        return [str(got) + "... What did you expect?"]

                return []

            if f.op == "OF":
                # Case-insensitive search for town name
                all_towns = db.collection("Vermont_Municipalities").stream()
                for doc in all_towns:
                    town_data = doc.to_dict()
                    # Get town name from the data
                    town_name = town_data.get("town_name", "")
                    if town_name.lower() == f.value.lower():
                        return [town_data.get(f.field)]
                return []
            else:  # operator is ==, <, >, !=
                query = query.where(filter=FieldFilter(f.field, f.op, f.value))
                # Execute
                docs = list(query.stream())
        elif connector == "AND":
            # add another "where" to the query
            # can assume here that the operator is not "OF"
            query = query.where(filter=FieldFilter(f.field, f.op, f.value))

        else:  # connector == "OR"
            # Seed docs from the current AND-chain once
            if not saw_or:
                docs = list(query.stream())

            # Run the OR branch independently
            new_query = (db.collection("Vermont_Municipalities")
                         .where(filter=FieldFilter(f.field, f.op, f.value)))
            new_docs = list(new_query.stream())

            # Union by document id (avoid duplicates)
            existing_ids = {d.id for d in docs}
            for nd in new_docs:
                if nd.id not in existing_ids:
                    docs.append(nd)

            saw_or = True
    # Execute and return dicts instead of snapshots
    # Only run the chained AND query when there was NO OR
    if not saw_or:
        docs = list(query.stream())

    return [doc.to_dict() | {"id": doc.id} for doc in docs]

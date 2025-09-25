# Vermont-Muni
A Firebase-based admin loader and query CLI for Vermont towns.

## Setup

1. Install Python 3.9+ and pip
2. Install dependencies:
```
pip install -r requirements.txt
```
3. Obtain your Firebase service account key JSON (not committed). Save as `serviceAccountKey.json` in project root (or set `GOOGLE_APPLICATION_CREDENTIALS`).

## Admin loader

Load JSON data into Firestore, replacing existing docs:
```
python admin.py Vermont_Muni.json
```

## Query CLI

To start the query interface:
```
python query.py
```

Start interactive prompt to run queries like:
```
> county == Chittenden
> town_name == "South Burlington"
> altitude >= 1200
> postal_code == 05401
> altitude OF Burlington
```

Queryable fields (case-insensitive): `town_id`, `town_name`, `county`, `population`, `square_mi`,
`altitude`, `postal_code`, `office_phone`, `clerk_email`, `url`. Some fields are optional and may be missing.

Rules:
- Fields/operators are case-insensitive; values area also case-insensitive for this dataset.
- Multi-word values require quotes (e.g., "South Burlington").
- Support a single AND or OR (no mixing), and do not combine `OF` with AND/OR.
- Not all fields support all operators (e.g., `town_name` does not support the `>` operator).
- Depending on the operator the value must be of a certain type: 
      - After `>`, `<`, `>=` or `<=`, the value must be a number.
      - After `OF`, the value must be a string.

Interface between parser and engine:
- `parse_query(query_str: str) -> QueryPlan`
- `run_fn(db, plan: QueryPlan) -> list[dict] | list[Any]`

Model usage:
- Admin loader normalizes inputs with `Town.from_dict(...).to_dict()` before upload.
- Query CLI formats results via `Town.from_dict(...)` for consistent output.

If you need help, use the `help` command, and use the `quit` command to exit the program.
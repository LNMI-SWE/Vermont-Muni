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

Start interactive prompt to run queries like:
```
> county == Chittenden
> town_name == "South Burlington"
> altitude >= 1200
```

The queryable fields are the following: `town_id`, `town_name`, `county`, `population`, `square_mi`, 
`altitude`, `postal_code`, `url`, `office_phone`, and `clerk_email`. Not all documents in the database 
have the `url`, `office_phone`, or `clerk_email` fields.
If you need help, use the `help` command, and use the `quit` command to exit the program. 
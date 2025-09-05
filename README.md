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
python admin.py csvjson.json
```

## Query CLI

Start interactive prompt to run queries like:
```
> county == Chittenden
> altitude >= 1200
> population > 0 ORDER BY population DESC LIMIT 5
> help
> quit
```

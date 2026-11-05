# Student Placement Analysis System

A Flask dashboard for student placement records and indicative readiness scores.

## Run locally

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000 in your browser.

The app creates `students.db` automatically and inserts three example students on the first run. Records persist between restarts. To use another database location, set `PLACEMENT_DB` to its path. For production, set a stable random `SECRET_KEY` environment variable and deploy behind a production WSGI server; never enable Flask debug mode in production.

## Tests

```bash
python -m unittest -v
```

## Features

- Student dashboard: counts, placement rate, average positive package (LPA)
- Add student form with server-side validation and CSRF protection
- SQLite persistence and parameterized SQL queries
- Indicative readiness score based on CGPA and skills (not a trained ML model)

## Notes

The initial records are demonstration data. This is a student prototype, not a production multi-user admissions or placement platform. Authentication, authorization, and stronger deployment controls are needed before handling real student data. A zero package for a placed student is permitted as an unknown value and excluded from average package calculations.

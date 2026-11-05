"""Student Placement Analysis System."""
import math
import os
import secrets
import sqlite3
from pathlib import Path
from flask import Flask, abort, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
SAMPLE_STUDENTS = [
    ('Rahul', 'CSE', 8.2, 75, 80, 70, 1, 6.0),
    ('Priya', 'CSE', 9.1, 88, 92, 85, 1, 8.0),
    ('Arjun', 'ECE', 7.0, 60, 65, 58, 0, 0.0),
]
DEPARTMENTS = {'CSE', 'ECE', 'EEE', 'IT', 'MECH', 'CIVIL', 'Other'}


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=os.environ.get('SECRET_KEY') or secrets.token_hex(32),
        DATABASE=os.environ.get('PLACEMENT_DB', str(BASE_DIR / 'students.db')),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
    )
    if test_config:
        app.config.update(test_config)

    def connect():
        db = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
        return db

    def init_db():
        with connect() as db:
            db.execute('''CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL, department TEXT NOT NULL,
                cgpa REAL NOT NULL, aptitude INTEGER NOT NULL,
                technical INTEGER NOT NULL, communication INTEGER NOT NULL,
                placed INTEGER NOT NULL, package REAL NOT NULL
            )''')
            # Seed only when the database is first created and contains no records.
            if db.execute('SELECT COUNT(*) FROM students').fetchone()[0] == 0:
                db.executemany('''INSERT INTO students
                    (name, department, cgpa, aptitude, technical, communication, placed, package)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', SAMPLE_STUDENTS)

    def parse_number(field, low, high, integer=False):
        raw = request.form.get(field, '').strip()
        try:
            number = int(raw) if integer else float(raw)
        except (ValueError, TypeError):
            raise ValueError(f'{field.capitalize()} must be a valid number.')
        if not math.isfinite(number) or not low <= number <= high:
            raise ValueError(f'{field.capitalize()} must be between {low} and {high}.')
        return number

    @app.route('/', methods=['GET', 'POST'])
    def home():
        if request.method == 'POST':
            if not session.get('csrf_token') or not secrets.compare_digest(request.form.get('csrf_token', ''), session['csrf_token']):
                abort(400, description='Invalid form token. Refresh the page and try again.')
            try:
                name = request.form.get('name', '').strip()
                department = request.form.get('department', '').strip()
                if not name or len(name) > 100:
                    raise ValueError('Name must be between 1 and 100 characters.')
                if department not in DEPARTMENTS:
                    raise ValueError('Please select a valid department.')
                cgpa = parse_number('cgpa', 0, 10)
                aptitude = parse_number('aptitude', 0, 100, integer=True)
                technical = parse_number('technical', 0, 100, integer=True)
                communication = parse_number('communication', 0, 100, integer=True)
                status = request.form.get('placed')
                if status not in ('yes', 'no'):
                    raise ValueError('Please select a valid placement status.')
                placed = status == 'yes'
                package = parse_number('package', 0, 1000) if request.form.get('package', '').strip() else 0.0
                if not placed and package != 0:
                    raise ValueError('Unplaced students must have a zero package.')
                with connect() as db:
                    db.execute('''INSERT INTO students
                        (name, department, cgpa, aptitude, technical, communication, placed, package)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (name, department, cgpa, aptitude, technical, communication, int(placed), package))
            except ValueError as exc:
                abort(400, description=str(exc))
            return redirect(url_for('home'))

        if 'csrf_token' not in session:
            session['csrf_token'] = secrets.token_urlsafe(32)
        with connect() as db:
            students = [dict(row) for row in db.execute('SELECT * FROM students ORDER BY id')]
        total = len(students)
        placed_count = sum(s['placed'] for s in students)
        packages = [s['package'] for s in students if s['placed'] and s['package'] > 0]
        for s in students:
            s['readiness'] = round(s['cgpa'] * 4 + s['aptitude'] * .20 +
                                   s['technical'] * .25 + s['communication'] * .15, 1)
        return render_template('index.html', students=students, total=total,
                               placed_count=placed_count,
                               placement_rate=round(placed_count / total * 100, 1) if total else 0,
                               average_package=round(sum(packages) / len(packages), 2) if packages else 0,
                               csrf_token=session['csrf_token'])

    with app.app_context():
        init_db()
    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_DEBUG') == '1')

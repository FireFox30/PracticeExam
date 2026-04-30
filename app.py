import sqlite3
from app import Flask, g, render_template, request, redirect, url_for

app = Flask(__name__)
DATABASE = 'notes.db'

def get_db():
    """Open a new database connection if one doesn't exist for the current request."""
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row   # access columns by name
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Create tables from schema.sql (run once)."""
    with app.app_context():
        db = get_db()
        with app.open_resource('schema.sql', mode='r') as f:
            db.executescript(f.read())
        db.commit()

# ---------- Routes ----------
@app.route('/')
def index():
    db = get_db()
    notes = db.execute('SELECT * FROM notes ORDER BY created_at DESC').fetchall()
    return render_template('index.html', notes=notes)

@app.route('/add', methods=['POST'])
def add_note():
    content = request.form.get('content', '').strip()
    if content:
        db = get_db()
        db.execute('INSERT INTO notes (content) VALUES (?)', (content,))
        db.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    db = get_db()
    db.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    db.commit()
    return redirect(url_for('index'))

# ---------- One‑time table creation ----------
# Run this only once (or delete notes.db to start fresh).
# In a real app you'd use Flask CLI or migrations, but for simplicity:
if __name__ == '__main__':
    init_db()
    app.run(debug=True)
import psycopg2
import psycopg2.extras
from flask import Flask, g, render_template, request, redirect, url_for

app = Flask(__name__)

DB_CONFIG = {
    'host': '172.31.255.222',      
    'port': 5432,
    'dbname': 'notesdb',
    'user': 'flaskuser',
    'password': 'flaskpass'
}

def get_db():
    """Open a PostgreSQL connection if one doesn't exist for the current request."""
    if 'db' not in g:
        g.db = psycopg2.connect(**DB_CONFIG)
        # This makes rows behave like dictionaries (e.g. row['content'])
        g.db.cursor_factory = psycopg2.extras.RealDictCursor
    return g.db

@app.teardown_appcontext
def close_db(error):
    """Close the database connection at the end of the request."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """Create the 'notes' table if it doesn't exist yet."""
    with app.app_context():
        db = get_db()
        cur = db.cursor()
        cur.execute('''
            CREATE TABLE IF NOT EXISTS notes (
                id SERIAL PRIMARY KEY,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        ''')
        db.commit()


@app.route('/')
def index():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT * FROM notes ORDER BY created_at DESC')
    notes = cur.fetchall()
    return render_template('index.html', notes=notes)

@app.route('/add', methods=['POST'])
def add_note():
    content = request.form.get('content', '').strip()
    if content:
        db = get_db()
        cur = db.cursor()
        cur.execute('INSERT INTO notes (content) VALUES (%s)', (content,))
        db.commit()
    return redirect(url_for('index'))

@app.route('/delete/<int:note_id>', methods=['POST'])
def delete_note(note_id):
    db = get_db()
    cur = db.cursor()
    cur.execute('DELETE FROM notes WHERE id = %s', (note_id,))
    db.commit()
    return redirect(url_for('index'))

@app.route('/edit/<int:note_id>', methods=['POST'])
def edit_note(note_id):
    content = request.form.get('content', '').strip()
    db = get_db()
    cur = db.cursor()
    cur.execute('UPDATE notes SET content = %s WHERE id = %s', (content, note_id))
    db.commit()
    return redirect(url_for('index'))

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '').strip()
    db = get_db()
    cur = db.cursor()
    
    if query:
        # Search using SQL LIKE for partial matches
        cur.execute('SELECT * FROM notes WHERE content ILIKE %s ORDER BY created_at DESC', 
                    (f'%{query}%',))
    else:
        cur.execute('SELECT * FROM notes ORDER BY created_at DESC')
    
    notes = cur.fetchall()
    return render_template('index.html', notes=notes, search_query=query)

if __name__ == '__main__':
    init_db()          
    app.run(debug=True)
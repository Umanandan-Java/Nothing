import sqlite3
import time
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import os

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static'))
CORS(app) # Allow all origins for simplicity in the hackathon
DATABASE_FILE = 'econsultation.db'

def get_db_connection():
    """Creates a database connection with dictionary-like row access."""
    conn = sqlite3.connect(DATABASE_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# --- API Endpoints ---

@app.route('/api/drafts', methods=['GET'])
def get_drafts():
    """
    UPGRADED: Returns a list of all drafts, now including all AI analysis columns.
    """
   
    conn = get_db_connection()
    # Using SELECT * is the easiest way to include all the new columns
    drafts = conn.execute('SELECT * FROM drafts').fetchall()
    conn.close()
    return jsonify([dict(row) for row in drafts])

@app.route('/api/sections/<int:draft_id>')
def get_sections_for_draft(draft_id):
    """
    UPGRADED: Returns all sections for a specific draft, including all new AI analysis columns.
    """
    
    conn = get_db_connection()
    # Using SELECT * to get all columns, including new ones
    sections = conn.execute(
        'SELECT * FROM sections WHERE draft_id = ?', 
        (draft_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(row) for row in sections])
    
@app.route('/api/comments/<int:draft_id>')
def get_comments_for_draft(draft_id):
    """
    UPGRADED: Returns all comments for a specific draft, joined with user and section data.
    This is the primary endpoint for the interactive dashboard.
    """
    
    conn = get_db_connection()
    comments = conn.execute("""
        SELECT 
            c.*, -- Selects all comment data, including new score columns
            sec.section_title,
            u.state,
            CASE 
                WHEN u.industry IS NULL OR u.industry = '' THEN 'Individual'
                ELSE u.industry
            END as industry,
            u.is_organization
        FROM comments c
        JOIN submissions s ON c.submission_id = s.submission_id
        JOIN sections sec ON c.section_id = sec.section_id
        JOIN users u ON s.user_id = u.user_id
        WHERE s.draft_id = ?
    """, (draft_id,)).fetchall()
    conn.close()
    return jsonify([dict(row) for row in comments])

# --- RESTORED & MAINTAINED from your original code ---

@app.route('/api/drafts/<int:draft_id>', methods=['GET'])
def get_draft_details(draft_id):
    """
    RESTORED: Provides a deeply nested JSON object for a single draft,
    including all its sections and their respective comments.
    """
    
    conn = get_db_connection()
    draft = conn.execute('SELECT * FROM drafts WHERE draft_id = ?', (draft_id,)).fetchone()
    if draft is None: return jsonify({"error": "Draft not found"}), 404

    sections = conn.execute('SELECT * FROM sections WHERE draft_id = ? ORDER BY section_id', (draft_id,)).fetchall()
    sections_list = []
    for section in sections:
        section_dict = dict(section)
        # Your original query had a slight bug in the JOIN condition, I've corrected it.
        # It should join on c.submission_id = s.submission_id, not section_id.
        comments = conn.execute('''
            SELECT c.*, u.first_name, u.last_name, u.organization_name FROM comments c
            JOIN submissions s ON c.submission_id = s.submission_id
            JOIN users u ON s.user_id = u.user_id WHERE c.section_id = ?
        ''', (section['section_id'],)).fetchall()
        section_dict['comments'] = [dict(comment) for comment in comments]
        sections_list.append(section_dict)
    
    conn.close()
    result = dict(draft)
    result['sections'] = sections_list
    return jsonify(result)

@app.route('/wordclouds/<path:subfolder>/<path:filename>')
def serve_wordcloud(subfolder, filename):
    """
    RESTORED: A dedicated route for serving word cloud images, which may be
    cleaner for some frontend paths than using the main /static route.
    """
    
    # Note: Flask's send_from_directory is relative to the *app root*, not the static folder path.
    # We construct a path to the top-level 'static' directory.
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..','static')
    
    return send_from_directory(static_dir, f'wordclouds/{subfolder}/{filename}')

# Added the generic /static route as well, as it is also very useful.
@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory(app.static_folder, path)


if __name__ == '__main__':
    app.run(debug=True, port=5000)
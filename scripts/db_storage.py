"""
SQLite persistence layer for Document AI

Stores:
- documents metadata
- extracted fields
- document text (for RAG)
"""

import sqlite3
from datetime import datetime

DB_PATH = "document_ai.db"


# Connection
def get_connection():
    return sqlite3.connect(DB_PATH)


# Initialize database
def init_db():

    conn = get_connection()
    cur = conn.cursor()

    # Documents table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT,
        processed_at TEXT,
        status TEXT
    )
    """)

    # Extracted fields table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS extracted_fields (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        field_name TEXT,
        field_value TEXT,
        confidence REAL,
        source TEXT,
        reviewed INTEGER DEFAULT 0,
        FOREIGN KEY(document_id) REFERENCES documents(id)
    )
    """)

    # Full OCR text storage (used for RAG)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS document_text (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        page_number INTEGER,
        content TEXT,
        FOREIGN KEY(document_id) REFERENCES documents(id)
    )
    """)

    conn.commit()
    conn.close()



# Document management
def create_document(filename):
    """
    Create or retrieve a document row.
    """

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id FROM documents WHERE filename=?", (filename,))
    row = cur.fetchone()

    if row:
        doc_id = row[0]

    else:

        cur.execute(
            "INSERT INTO documents (filename, processed_at, status) VALUES (?, ?, ?)",
            (filename, datetime.utcnow().isoformat(), "processed")
        )

        doc_id = cur.lastrowid

    conn.commit()
    conn.close()

    return doc_id


# Save extracted fields
def save_fields(document_id, fields, confidences, sources):

    conn = get_connection()
    cur = conn.cursor()

    for field, value in fields.items():

        cur.execute("""
            INSERT INTO extracted_fields
            (document_id, field_name, field_value, confidence, source)
            VALUES (?, ?, ?, ?, ?)
        """, (
            document_id,
            field,
            value,
            confidences.get(field, 0.0),
            sources.get(field, "regex")
        ))

    conn.commit()
    conn.close()


# Save OCR text (for RAG)
def save_document_text(document_id, page, text):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO document_text
        (document_id, page_number, content)
        VALUES (?, ?, ?)
    """, (document_id, page, text))

    conn.commit()
    conn.close()



# Review utilities
def mark_field_reviewed(document_id, field_name):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE extracted_fields
        SET reviewed=1
        WHERE document_id=? AND field_name=?
    """, (document_id, field_name))

    conn.commit()
    conn.close()


def load_fields(document_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT field_name, field_value, confidence, source, reviewed
        FROM extracted_fields
        WHERE document_id=?
    """, (document_id,))

    rows = cur.fetchall()

    conn.close()

    return rows

# load document text for debugging.

def load_document_text(document_id):

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT page_number, content
        FROM document_text
        WHERE document_id=?
    """, (document_id,))

    rows = cur.fetchall()

    conn.close()

    return rows
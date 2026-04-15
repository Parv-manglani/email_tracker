import sqlite3
from datetime import datetime


DB_name = "emails.db"

def get_connection() :
    return sqlite3.connect(DB_name)

def init_db() :
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        create table if not exists email_tracking (
            id text PRIMARY KEY,
            email TEXT,
            status text, 
            sent_at text,
            opened_at text,
            open_count integer default 0    
        )
        """)
    
    conn.commit()
    conn.close()


def insert_email(uid, email) :
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        insert into email_tracking(id, email, status, sent_at) 
        values (?, ?, ?, ?)
        """, (uid, email, "SENT", datetime.now()))

    conn.commit()
    conn.close()


def mark_as_opened(uid) :
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        update email_tracking
        set status = "OPENED",   
        opened_at = ?, 
        open_count = open_count + 1
        where id = ?
    """, (datetime.now(), uid))

    conn.commit()
    conn.close()

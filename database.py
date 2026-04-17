import psycopg2
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def get_connection():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is not set. Please configure it in your environment.")
    return psycopg2.connect(database_url)


# 🔹 Table init
def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS email_tracking (
        id TEXT PRIMARY KEY,
        email TEXT,
        status TEXT,
        sent_at TIMESTAMP,
        opened_at TIMESTAMP,
        open_count INTEGER DEFAULT 0,
        ip TEXT,
        user_agent TEXT,
        is_proxy BOOLEAN DEFAULT FALSE
    )
    """)

    conn.commit()
    conn.close()


# 🔹 Insert email record
def insert_email(uid, email):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO email_tracking (id, email, status, sent_at)
        VALUES (%s, %s, %s, %s)
    """, (uid, email, "SENT", datetime.now()))

    conn.commit()
    conn.close()


# 🔥 CORE FUNCTION (SMART TRACKING)
def mark_as_opened(uid, ip, user_agent):
    conn = get_connection()
    cursor = conn.cursor()

    # 🔹 Step 1: get sent_at
    cursor.execute("""
        SELECT sent_at FROM email_tracking
        WHERE id = %s
    """, (uid,))

    result = cursor.fetchone()

    if not result:
        conn.close()
        return

    sent_at = result[0]
    current_time = datetime.now()

    # 🔹 Step 2: time diff calculate
    time_diff = (current_time - sent_at).total_seconds()

    # 🔥 ONLY TIME-BASED FILTER
    is_proxy = time_diff < 3   # < 3 sec = proxy

    print(f"UID: {uid}")
    print(f"Time diff: {time_diff}")
    print(f"IP: {ip}")
    print(f"UA: {user_agent}")
    print(f"Proxy (time-based): {is_proxy}")

    # 🔹 Step 3: update DB
    if is_proxy:
        cursor.execute("""
            UPDATE email_tracking
            SET ip = %s,
                user_agent = %s,
                is_proxy = TRUE
            WHERE id = %s
        """, (ip, user_agent, uid))

    else:
        cursor.execute("""
            UPDATE email_tracking
            SET status = 'OPENED',
                opened_at = %s,
                open_count = open_count + 1,
                ip = %s,
                user_agent = %s,
                is_proxy = FALSE
            WHERE id = %s
        """, (current_time, ip, user_agent, uid))

    conn.commit()
    conn.close()
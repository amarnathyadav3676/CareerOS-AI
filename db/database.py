import sqlite3, hashlib, os

DB_PATH = os.path.join(os.path.dirname(__file__), "careeros.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        college TEXT DEFAULT 'LPU',
        branch TEXT DEFAULT 'CSE',
        year INTEGER DEFAULT 2,
        target_role TEXT DEFAULT 'AI Full Stack Engineer',
        target_salary TEXT DEFAULT '₹15-30 LPA',
        cgpa TEXT DEFAULT '8.81',
        avatar TEXT DEFAULT '',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")

    # Per-user progress: key-value store (flexible for all tracker data)
    c.execute("""CREATE TABLE IF NOT EXISTS user_progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        key TEXT NOT NULL,
        value TEXT NOT NULL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, key),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # Study streak log
    c.execute("""CREATE TABLE IF NOT EXISTS streak_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        date TEXT NOT NULL,
        UNIQUE(user_id, date),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # LeetCode problems solved
    c.execute("""CREATE TABLE IF NOT EXISTS dsa_solved (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        topic_index INTEGER NOT NULL,
        problem_index INTEGER NOT NULL,
        solved_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, topic_index, problem_index),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # Projects
    c.execute("""CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        project_index INTEGER NOT NULL,
        status TEXT DEFAULT 'todo',
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, project_index),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # Certifications
    c.execute("""CREATE TABLE IF NOT EXISTS certifications (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        cert_index INTEGER NOT NULL,
        earned_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, cert_index),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # Skills
    c.execute("""CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        skill_key TEXT NOT NULL,
        skill_index INTEGER NOT NULL,
        done INTEGER DEFAULT 0,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, skill_key, skill_index),
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    # Notes (per user)
    c.execute("""CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        content TEXT DEFAULT '',
        color TEXT DEFAULT '#3B82F6',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")

    conn.commit()
    conn.close()
    print("✅ CareerOS DB initialized")

if __name__ == "__main__":
    init_db()
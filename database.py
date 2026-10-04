import hashlib
import secrets
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "site.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str, salt: str | None = None):
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100_000)
    return salt, digest.hex()


def verify_password(password: str, salt: str, password_hash: str) -> bool:
    _, expected_hash = hash_password(password, salt)
    return secrets.compare_digest(expected_hash, password_hash)


def init_db():
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS contact_submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                project_type TEXT NOT NULL,
                message TEXT NOT NULL,
                user_id INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                password_salt TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'user',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS user_sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                token TEXT UNIQUE NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            """
        )

        columns = [row[1] for row in conn.execute("PRAGMA TABLE_INFO(contact_submissions)").fetchall()]
        if "user_id" not in columns:
            conn.execute("ALTER TABLE contact_submissions ADD COLUMN user_id INTEGER")

        if get_user_by_username(conn, "admin") is None:
            create_user(
                conn=conn,
                username="admin",
                email="admin@novastudio.local",
                password="admin123",
                role="admin",
            )


def create_user(username: str, email: str, password: str, role: str = "user", conn=None):
    if conn is None:
        with get_connection() as conn:
            return create_user(username=username, email=email, password=password, role=role, conn=conn)

    if get_user_by_username(conn, username) is not None:
        raise ValueError("Username already exists")
    if get_user_by_email(conn, email) is not None:
        raise ValueError("Email already exists")

    salt, password_hash = hash_password(password)
    cursor = conn.execute(
        """
        INSERT INTO users (username, email, password_hash, password_salt, role)
        VALUES (?, ?, ?, ?, ?)
        """,
        (username.strip(), email.strip().lower(), password_hash, salt, role),
    )
    return cursor.lastrowid


def get_user_by_username(conn, username: str):
    row = conn.execute(
        "SELECT id, username, email, password_hash, password_salt, role, created_at FROM users WHERE username = ?",
        (username.strip(),),
    ).fetchone()
    return dict(row) if row else None


def get_user_by_email(conn, email: str):
    row = conn.execute(
        "SELECT id, username, email, password_hash, password_salt, role, created_at FROM users WHERE email = ?",
        (email.strip().lower(),),
    ).fetchone()
    return dict(row) if row else None


def get_user_by_id(user_id: int):
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id, username, email, password_hash, password_salt, role, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        return dict(row) if row else None


def authenticate_user(username: str, password: str):
    with get_connection() as conn:
        user = get_user_by_username(conn, username) or get_user_by_email(conn, username)
        if not user:
            return None
        if not verify_password(password, user["password_salt"], user["password_hash"]):
            return None
        return user


def create_session(user_id: int):
    token = secrets.token_urlsafe(32)
    expires_at = (datetime.utcnow() + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO user_sessions (user_id, token, expires_at) VALUES (?, ?, ?)",
            (user_id, token, expires_at),
        )
        return token


def get_session_user(token: str):
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.username, u.email, u.role, u.created_at
            FROM user_sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.token = ? AND s.expires_at > datetime('now')
            """,
            (token,),
        ).fetchone()
        return dict(row) if row else None


def delete_session(token: str):
    with get_connection() as conn:
        conn.execute("DELETE FROM user_sessions WHERE token = ?", (token,))


def save_contact_submission(name: str, email: str, project_type: str, message: str, user_id: int | None = None):
    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO contact_submissions (name, email, project_type, message, user_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, email, project_type, message, user_id),
        )
        return cursor.lastrowid


def get_contact_submissions(limit: int = 20, user_id: int | None = None, include_all: bool = False):
    with get_connection() as conn:
        if include_all:
            rows = conn.execute(
                """
                SELECT id, name, email, project_type, message, user_id, created_at
                FROM contact_submissions
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        elif user_id is not None:
            rows = conn.execute(
                """
                SELECT id, name, email, project_type, message, user_id, created_at
                FROM contact_submissions
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (user_id, limit),
            ).fetchall()
        else:
            rows = []
        return [dict(row) for row in rows]


def get_all_users_with_submissions():
    with get_connection() as conn:
        users = conn.execute(
            "SELECT id, username, email, role, created_at FROM users ORDER BY created_at DESC"
        ).fetchall()

        result = []
        for user in users:
            submissions = conn.execute(
                """
                SELECT id, name, email, project_type, message, user_id, created_at
                FROM contact_submissions
                WHERE user_id = ?
                ORDER BY created_at DESC
                """,
                (user["id"],),
            ).fetchall()

            result.append(
                {
                    "id": user["id"],
                    "username": user["username"],
                    "email": user["email"],
                    "role": user["role"],
                    "created_at": user["created_at"],
                    "submissions": [dict(row) for row in submissions],
                }
            )

        return result

# core/database.py
import sqlite3
import os
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path


def get_db_path(db_name: str) -> str:
    """Return path for a given DB inside the project folder."""
    base = Path(__file__).parent.parent
    return str(base / db_name)


# ─────────────────────────────────────────────
#  ADMIN DATABASE
# ─────────────────────────────────────────────

class AdminDB:
    def __init__(self, path: str = None):
        if path is None:
            path = get_db_path("admin/users.db")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.path = path
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS admin_config (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL,
                    email TEXT,
                    serial_key TEXT UNIQUE NOT NULL,
                    mac_hash TEXT,
                    ip_address TEXT,
                    valid_until TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    last_login TEXT,
                    notes TEXT
                );

                CREATE TABLE IF NOT EXISTS editals_config (
                    edital_id TEXT PRIMARY KEY,
                    tutorial_url TEXT DEFAULT '',
                    updated_at TEXT DEFAULT (datetime('now'))
                );

                CREATE TABLE IF NOT EXISTS app_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)
            # Default admin config
            conn.execute(
                "INSERT OR IGNORE INTO admin_config VALUES ('admin_password', ?)",
                (hashlib.sha256(b"admin123").hexdigest(),)
            )
            conn.execute(
                "INSERT OR IGNORE INTO app_settings VALUES ('app_version', '1.0.0')"
            )
            conn.execute(
                "INSERT OR IGNORE INTO app_settings VALUES ('update_url', '')"
            )
            conn.commit()

    # ── Auth ──────────────────────────────────
    def verify_admin(self, password: str) -> bool:
        hashed = hashlib.sha256(password.encode()).hexdigest()
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM admin_config WHERE key='admin_password'"
            ).fetchone()
            return row and row["value"] == hashed

    def change_admin_password(self, new_password: str):
        hashed = hashlib.sha256(new_password.encode()).hexdigest()
        with self._connect() as conn:
            conn.execute(
                "UPDATE admin_config SET value=? WHERE key='admin_password'", (hashed,)
            )
            conn.commit()

    # ── Users ─────────────────────────────────
    def get_all_users(self):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM users ORDER BY created_at DESC"
            ).fetchall()

    def get_user_by_serial(self, serial: str):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM users WHERE serial_key=?", (serial,)
            ).fetchone()

    def create_user(self, nome: str, email: str, serial: str,
                    days: int = 30, notes: str = "") -> int:
        valid_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        with self._connect() as conn:
            cur = conn.execute(
                """INSERT INTO users (nome, email, serial_key, valid_until, notes)
                   VALUES (?, ?, ?, ?, ?)""",
                (nome, email, serial, valid_until, notes)
            )
            conn.commit()
            return cur.lastrowid

    def update_user(self, user_id: int, nome: str, email: str,
                    valid_until: str, is_active: int, notes: str):
        with self._connect() as conn:
            conn.execute(
                """UPDATE users SET nome=?, email=?, valid_until=?,
                   is_active=?, notes=? WHERE id=?""",
                (nome, email, valid_until, is_active, notes, user_id)
            )
            conn.commit()

    def toggle_user_active(self, user_id: int):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET is_active = CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?",
                (user_id,)
            )
            conn.commit()

    def renew_user(self, user_id: int, days: int = 30):
        valid_until = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET valid_until=?, is_active=1 WHERE id=?",
                (valid_until, user_id)
            )
            conn.commit()

    def delete_user(self, user_id: int):
        with self._connect() as conn:
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()

    def update_user_device(self, serial: str, mac_hash: str, ip: str):
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET mac_hash=?, ip_address=?, last_login=datetime('now') WHERE serial_key=?",
                (mac_hash, ip, serial)
            )
            conn.commit()

    # ── Editais config ────────────────────────
    def get_edital_config(self, edital_id: str):
        with self._connect() as conn:
            return conn.execute(
                "SELECT * FROM editals_config WHERE edital_id=?", (edital_id,)
            ).fetchone()

    def set_tutorial_url(self, edital_id: str, url: str):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO editals_config (edital_id, tutorial_url, updated_at)
                   VALUES (?, ?, datetime('now'))
                   ON CONFLICT(edital_id) DO UPDATE SET tutorial_url=?, updated_at=datetime('now')""",
                (edital_id, url, url)
            )
            conn.commit()

    def get_all_editals_config(self):
        with self._connect() as conn:
            rows = conn.execute("SELECT * FROM editals_config").fetchall()
            return {r["edital_id"]: r["tutorial_url"] for r in rows}

    # ── App settings ──────────────────────────
    def get_setting(self, key: str, default: str = "") -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT value FROM app_settings WHERE key=?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO app_settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value=?",
                (key, value, value)
            )
            conn.commit()

    def get_stats(self):
        with self._connect() as conn:
            total = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active = conn.execute(
                "SELECT COUNT(*) FROM users WHERE is_active=1 AND valid_until >= date('now')"
            ).fetchone()[0]
            expiring = conn.execute(
                """SELECT COUNT(*) FROM users WHERE is_active=1
                   AND valid_until BETWEEN date('now') AND date('now', '+7 days')"""
            ).fetchone()[0]
            expired = conn.execute(
                "SELECT COUNT(*) FROM users WHERE valid_until < date('now')"
            ).fetchone()[0]
            return {
                "total": total,
                "active": active,
                "expiring_soon": expiring,
                "expired": expired,
            }


# ─────────────────────────────────────────────
#  CLIENT DATABASE
# ─────────────────────────────────────────────

class ClientDB:
    def __init__(self, path: str = None):
        if path is None:
            app_data = Path.home() / "AppData" / "Local" / "EditalSystem"
            # Linux/Mac fallback
            if not os.name == "nt":
                app_data = Path.home() / ".edital_system"
            app_data.mkdir(parents=True, exist_ok=True)
            path = str(app_data / "client.db")
        self.path = path
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._connect() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS license (
                    id INTEGER PRIMARY KEY,
                    serial_key TEXT,
                    user_name TEXT,
                    valid_until TEXT,
                    mac_hash TEXT,
                    activated_at TEXT
                );

                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    edital_id TEXT NOT NULL,
                    verified_at TEXT DEFAULT (datetime('now','localtime')),
                    action TEXT DEFAULT 'edital'
                );

                CREATE TABLE IF NOT EXISTS cached_editals (
                    edital_id TEXT PRIMARY KEY,
                    tutorial_url TEXT DEFAULT '',
                    updated_at TEXT
                );
            """)
            conn.commit()

    # ── License ───────────────────────────────
    def save_license(self, serial: str, user_name: str,
                     valid_until: str, mac_hash: str):
        with self._connect() as conn:
            conn.execute("DELETE FROM license")
            conn.execute(
                """INSERT INTO license (serial_key, user_name, valid_until, mac_hash, activated_at)
                   VALUES (?, ?, ?, ?, datetime('now','localtime'))""",
                (serial, user_name, valid_until, mac_hash)
            )
            conn.commit()

    def get_license(self):
        with self._connect() as conn:
            return conn.execute("SELECT * FROM license LIMIT 1").fetchone()

    def clear_license(self):
        with self._connect() as conn:
            conn.execute("DELETE FROM license")
            conn.commit()

    # ── Verifications ─────────────────────────
    def mark_verified(self, edital_id: str, action: str = "edital"):
        with self._connect() as conn:
            conn.execute(
                "INSERT INTO verifications (edital_id, action) VALUES (?, ?)",
                (edital_id, action)
            )
            conn.commit()

    def get_last_verification(self, edital_id: str):
        with self._connect() as conn:
            row = conn.execute(
                """SELECT verified_at FROM verifications
                   WHERE edital_id=? ORDER BY verified_at DESC LIMIT 1""",
                (edital_id,)
            ).fetchone()
            return row["verified_at"] if row else None

    def get_all_verifications(self):
        """Returns dict: edital_id -> last_verified_at"""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT edital_id, MAX(verified_at) as last_verified
                   FROM verifications GROUP BY edital_id"""
            ).fetchall()
            return {r["edital_id"]: r["last_verified"] for r in rows}

    # ── Cached editals config ─────────────────
    def update_edital_cache(self, edital_id: str, tutorial_url: str):
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO cached_editals (edital_id, tutorial_url, updated_at)
                   VALUES (?, ?, datetime('now'))
                   ON CONFLICT(edital_id) DO UPDATE SET tutorial_url=?, updated_at=datetime('now')""",
                (edital_id, tutorial_url, tutorial_url)
            )
            conn.commit()

    def get_tutorial_url(self, edital_id: str) -> str:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT tutorial_url FROM cached_editals WHERE edital_id=?",
                (edital_id,)
            ).fetchone()
            return row["tutorial_url"] if row else ""

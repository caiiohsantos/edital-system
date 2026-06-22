# core/database.py
import sqlite3, os, hashlib
from datetime import datetime, timedelta
from pathlib import Path


def get_db_path(name: str) -> str:
    base = Path(__file__).parent.parent
    return str(base / name)


class AdminDB:
    def __init__(self, path=None):
        path = path or get_db_path("admin/users.db")
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
                CREATE TABLE IF NOT EXISTS admin_config (key TEXT PRIMARY KEY, value TEXT);
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    nome TEXT NOT NULL, email TEXT,
                    serial_key TEXT UNIQUE NOT NULL,
                    mac_hash TEXT, ip_address TEXT,
                    valid_until TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT (datetime('now')),
                    last_login TEXT, notes TEXT
                );
                CREATE TABLE IF NOT EXISTS editals_config (
                    edital_id TEXT PRIMARY KEY, tutorial_url TEXT DEFAULT '',
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT);
            """)
            conn.execute("INSERT OR IGNORE INTO admin_config VALUES ('admin_password', ?)",
                        (hashlib.sha256(b"admin123").hexdigest(),))
            conn.execute("INSERT OR IGNORE INTO app_settings VALUES ('app_version','1.0.0')")
            conn.execute("INSERT OR IGNORE INTO app_settings VALUES ('update_url','')")
            conn.commit()

    def verify_admin(self, pw):
        h = hashlib.sha256(pw.encode()).hexdigest()
        with self._connect() as c:
            r = c.execute("SELECT value FROM admin_config WHERE key='admin_password'").fetchone()
            return r and r["value"] == h

    def change_admin_password(self, new_pw):
        h = hashlib.sha256(new_pw.encode()).hexdigest()
        with self._connect() as c:
            c.execute("UPDATE admin_config SET value=? WHERE key='admin_password'", (h,)); c.commit()

    def get_all_users(self):
        with self._connect() as c:
            return c.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()

    def get_user_by_serial(self, serial):
        with self._connect() as c:
            return c.execute("SELECT * FROM users WHERE serial_key=?", (serial,)).fetchone()

    def create_user(self, nome, email, serial, days=30, notes=""):
        valid = (datetime.now()+timedelta(days=days)).strftime("%Y-%m-%d")
        with self._connect() as c:
            cur = c.execute("INSERT INTO users (nome,email,serial_key,valid_until,notes) VALUES (?,?,?,?,?)",
                           (nome,email,serial,valid,notes))
            c.commit(); return cur.lastrowid

    def update_user(self, uid, nome, email, valid_until, is_active, notes):
        with self._connect() as c:
            c.execute("UPDATE users SET nome=?,email=?,valid_until=?,is_active=?,notes=? WHERE id=?",
                     (nome,email,valid_until,is_active,notes,uid)); c.commit()

    def toggle_user_active(self, uid):
        with self._connect() as c:
            c.execute("UPDATE users SET is_active=CASE WHEN is_active=1 THEN 0 ELSE 1 END WHERE id=?",(uid,)); c.commit()

    def renew_user(self, uid, days=30):
        valid = (datetime.now()+timedelta(days=days)).strftime("%Y-%m-%d")
        with self._connect() as c:
            c.execute("UPDATE users SET valid_until=?,is_active=1 WHERE id=?",(valid,uid)); c.commit()

    def delete_user(self, uid):
        with self._connect() as c:
            c.execute("DELETE FROM users WHERE id=?",(uid,)); c.commit()

    def update_user_device(self, serial, mac_hash, ip):
        with self._connect() as c:
            c.execute("UPDATE users SET mac_hash=?,ip_address=?,last_login=datetime('now') WHERE serial_key=?",
                     (mac_hash,ip,serial)); c.commit()

    def set_tutorial_url(self, edital_id, url):
        with self._connect() as c:
            c.execute("""INSERT INTO editals_config (edital_id,tutorial_url,updated_at)
                        VALUES (?,?,datetime('now'))
                        ON CONFLICT(edital_id) DO UPDATE SET tutorial_url=?,updated_at=datetime('now')""",
                     (edital_id,url,url)); c.commit()

    def get_all_editals_config(self):
        with self._connect() as c:
            rows = c.execute("SELECT * FROM editals_config").fetchall()
            return {r["edital_id"]: r["tutorial_url"] for r in rows}

    def get_setting(self, key, default=""):
        with self._connect() as c:
            r = c.execute("SELECT value FROM app_settings WHERE key=?",(key,)).fetchone()
            return r["value"] if r else default

    def set_setting(self, key, value):
        with self._connect() as c:
            c.execute("INSERT INTO app_settings VALUES (?,?) ON CONFLICT(key) DO UPDATE SET value=?",
                     (key,value,value)); c.commit()

    def get_stats(self):
        with self._connect() as c:
            total = c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            active = c.execute("SELECT COUNT(*) FROM users WHERE is_active=1 AND valid_until>=date('now')").fetchone()[0]
            expiring = c.execute("SELECT COUNT(*) FROM users WHERE is_active=1 AND valid_until BETWEEN date('now') AND date('now','+7 days')").fetchone()[0]
            expired = c.execute("SELECT COUNT(*) FROM users WHERE valid_until<date('now')").fetchone()[0]
            return {"total":total,"active":active,"expiring_soon":expiring,"expired":expired}


class ClientDB:
    def __init__(self, path=None):
        if path is None:
            d = Path.home()/("AppData/Local/EditalSystem" if os.name=="nt" else ".edital_system")
            d.mkdir(parents=True, exist_ok=True)
            path = str(d/"client.db")
        self.path = path
        self._init()

    def _connect(self):
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self):
        with self._connect() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS license (
                    id INTEGER PRIMARY KEY, serial_key TEXT, user_name TEXT,
                    valid_until TEXT, mac_hash TEXT, activated_at TEXT
                );
                CREATE TABLE IF NOT EXISTS verifications (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    edital_id TEXT NOT NULL,
                    verified_at TEXT DEFAULT (datetime('now','localtime')),
                    action TEXT DEFAULT 'edital'
                );
                CREATE TABLE IF NOT EXISTS cached_editals (
                    edital_id TEXT PRIMARY KEY, tutorial_url TEXT DEFAULT '', updated_at TEXT
                );
            """); c.commit()

    def save_license(self, serial, user_name, valid_until, mac_hash):
        with self._connect() as c:
            c.execute("DELETE FROM license")
            c.execute("""INSERT INTO license (serial_key,user_name,valid_until,mac_hash,activated_at)
                        VALUES (?,?,?,?,datetime('now','localtime'))""",
                     (serial,user_name,valid_until,mac_hash)); c.commit()

    def get_license(self):
        with self._connect() as c:
            return c.execute("SELECT * FROM license LIMIT 1").fetchone()

    def clear_license(self):
        with self._connect() as c:
            c.execute("DELETE FROM license"); c.commit()

    def mark_verified(self, edital_id, action="edital"):
        with self._connect() as c:
            c.execute("INSERT INTO verifications (edital_id,action) VALUES (?,?)",(edital_id,action)); c.commit()

    def get_last_verification(self, edital_id):
        with self._connect() as c:
            r = c.execute("SELECT verified_at FROM verifications WHERE edital_id=? ORDER BY verified_at DESC LIMIT 1",
                         (edital_id,)).fetchone()
            return r["verified_at"] if r else None

    def get_all_verifications(self):
        with self._connect() as c:
            rows = c.execute("SELECT edital_id, MAX(verified_at) as last_verified FROM verifications GROUP BY edital_id").fetchall()
            return {r["edital_id"]: r["last_verified"] for r in rows}

    def update_edital_cache(self, edital_id, url):
        with self._connect() as c:
            c.execute("""INSERT INTO cached_editals (edital_id,tutorial_url,updated_at) VALUES (?,?,datetime('now'))
                        ON CONFLICT(edital_id) DO UPDATE SET tutorial_url=?,updated_at=datetime('now')""",
                     (edital_id,url,url)); c.commit()

    def get_tutorial_url(self, edital_id):
        with self._connect() as c:
            r = c.execute("SELECT tutorial_url FROM cached_editals WHERE edital_id=?",(edital_id,)).fetchone()
            return r["tutorial_url"] if r else ""

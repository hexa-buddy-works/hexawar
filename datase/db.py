import os
import threading
from typing import Dict, Optional, Tuple
import psycopg2
from psycopg2.extensions import connection as PGConnection
from psycopg2.extensions import cursor as PGCursor
import sqlite3


class PostgresDB:
    """
    Thread-safe Singleton for psycopg2 connection.

    Usage:
        db = PostgresSingleton("db.properties")
        cur = db.get_cursor()
        cur.execute("SELECT 1")
    """

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, properties_path: str = "../resources/hexawar.properties"):
        # Double-checked locking for singleton instance creation
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(PostgresDB, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, properties_path: str = "../resources/hexawar.properties"):
        if getattr(self, "_initialized", False):
            return  # Avoid reinitialization in Singleton

        self._properties_path = properties_path
        self._conn: Optional[PGConnection] = None
        self._conn_lock = threading.RLock()
        self._initialized = True

    def _build_conn_kwargs(self) -> Dict[str, object]:
        props = self.load_properties(self._properties_path)

        # Mandatory fields
        host = props.get("db.host")
        port = props.get("db.port", "5432")
        dbname = props.get("db.name")
        user = props.get("db.user")
        password = props.get("db.password")

        missing = [k for k, v in {
            "db.host": host, "db.name": dbname, "db.user": user, "db.password": password
        }.items() if not v]

        if missing:
            raise ValueError(f"Missing required properties: {', '.join(missing)}")

        kwargs: Dict[str, object] = {
            "host": host,
            "port": int(port),
            "dbname": dbname,
            "user": user,
            "password": password,
        }

        # Optional extras
        if "db.sslmode" in props:
            kwargs["sslmode"] = props["db.sslmode"]
        if "db.connect_timeout" in props:
            kwargs["connect_timeout"] = int(props["db.connect_timeout"])

        return kwargs

    def _ensure_connection(self) -> PGConnection:
        """
        Ensure a live connection exists; reconnect if needed.
        """
        with self._conn_lock:
            if self._conn is None or self._conn.closed != 0:
                kwargs = self._build_conn_kwargs()
                self._conn = psycopg2.connect(**kwargs)
                # Optional: manage transactions yourself
                # self._conn.autocommit = True
            return self._conn

    def get_cursor(self, dict_cursor: bool = False) -> PGCursor:
        """
        Returns a new cursor from the singleton connection.
        - dict_cursor=True returns RealDictCursor (rows as dict)
        """
        conn = self._ensure_connection()

        if dict_cursor:
            from psycopg2.extras import RealDictCursor
            return conn.cursor(cursor_factory=RealDictCursor)

        return conn.cursor()

    def get_cursor_and_connection(self, dict_cursor: bool = False) -> Tuple[PGCursor, PGConnection]:
        """
        Sometimes you need both cursor and connection (e.g., commit/rollback).
        """
        conn = self._ensure_connection()
        cur = self.get_cursor(dict_cursor=dict_cursor)
        return cur, conn

    def commit(self) -> None:
        conn = self._ensure_connection()
        conn.commit()

    def rollback(self) -> None:
        conn = self._ensure_connection()
        conn.rollback()

    def close(self) -> None:
        """
        Close the singleton connection.
        """
        with self._conn_lock:
            if self._conn is not None and self._conn.closed == 0:
                self._conn.close()
            self._conn = None
    
    def load_properties() -> Dict[str, str]:
        """
        Load key=value pairs from a .properties file.
        Supports comments starting with # or ; and ignores blank lines.
        """
        file_path: str = "../resources/hexapp.properties"
        props: Dict[str, str] = {}

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Properties file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()

        return props



class SqliteDB:
    """
    Thread-safe Singleton for SQLite connection.

    Usage:
        db = SqliteSingleton("db.properties")
        cur = db.get_cursor()
        cur.execute("SELECT 1")
    """

    _instance = None
    _instance_lock = threading.Lock()

    def __new__(cls, properties_path: str = "../resources/hexawar.properties"):
        # Double-checked locking for singleton instance creation
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(SqliteDB, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, properties_path: str = "../resources/hexawar.properties"):
        if getattr(self, "_initialized", False):
            return  # Avoid reinitialization in Singleton

        self._properties_path = properties_path
        self._conn: Optional[sqlite3.Connection] = None
        self._conn_lock = threading.RLock()
        self._initialized = True

    def _build_conn_kwargs(self) -> Tuple[str, Dict[str, object], Dict[str, str]]:
        """
        Returns (db_path, connect_kwargs, props)
        """
        props = self.load_properties(self._properties_path)

        db_path = props.get("db.path")
        if not db_path:
            raise ValueError("Missing required property: db.path")

        # Ensure directory exists if it's a file path (not :memory:)
        if db_path != ":memory:":
            parent_dir = os.path.dirname(os.path.abspath(db_path))
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

        timeout = float(props.get("db.timeout", "5"))
        check_same_thread = self._to_bool(props.get("db.check_same_thread"), default=True)

        # isolation_level:
        # - None => autocommit mode in sqlite3
        # - "" (empty string) is treated as a string; we'll normalize empty to None
        iso = props.get("db.isolation_level", None)
        if iso is not None and iso.strip() == "":
            iso = None

        connect_kwargs: Dict[str, object] = {
            "timeout": timeout,
            "check_same_thread": check_same_thread,
            "isolation_level": iso,  # None -> autocommit
        }

        return db_path, connect_kwargs, props

    def _apply_pragmas(self, conn: sqlite3.Connection, props: Dict[str, str]) -> None:
        """
        Apply optional PRAGMAs like WAL journaling, FK enforcement.
        """
        journal_mode = props.get("db.journal_mode")
        foreign_keys = props.get("db.foreign_keys")

        cur = conn.cursor()
        try:
            if journal_mode:
                cur.execute(f"PRAGMA journal_mode={journal_mode};")
            if foreign_keys is not None:
                cur.execute(f"PRAGMA foreign_keys={'ON' if self._to_bool(foreign_keys) else 'OFF'};")
        finally:
            cur.close()

    def _ensure_connection(self) -> sqlite3.Connection:
        """
        Ensure a live connection exists; reconnect if needed.
        """
        with self._conn_lock:
            if self._conn is None:
                db_path, kwargs, props = self._build_conn_kwargs()
                self._conn = sqlite3.connect(db_path, **kwargs)
                self._apply_pragmas(self._conn, props)
            return self._conn

    def get_cursor(self, row_factory: bool = False) -> sqlite3.Cursor:
        """
        Returns a new cursor from the singleton connection.
        - row_factory=True makes rows behave like dicts (sqlite3.Row)
        """
        conn = self._ensure_connection()
        if row_factory:
            conn.row_factory = sqlite3.Row
        return conn.cursor()

    def get_cursor_and_connection(self, row_factory: bool = False) -> Tuple[sqlite3.Cursor, sqlite3.Connection]:
        """
        Sometimes you need both cursor and connection (e.g., commit/rollback).
        """
        conn = self._ensure_connection()
        cur = self.get_cursor(row_factory=row_factory)
        return cur, conn

    def commit(self) -> None:
        conn = self._ensure_connection()
        conn.commit()

    def rollback(self) -> None:
        conn = self._ensure_connection()
        conn.rollback()

    def close(self) -> None:
        """
        Close the singleton connection.
        """
        with self._conn_lock:
            if self._conn is not None:
                self._conn.close()
            self._conn = None

    def _to_bool(value: Optional[str], default: bool = False) -> bool:
        if value is None:
            return default
        v = value.strip().lower()
        return v in ("1", "true", "yes", "y", "on")
    
    def load_properties() -> Dict[str, str]:
        """
        Load key=value pairs from a .properties file.
        Supports comments starting with # or ; and ignores blank lines.
        """
        props: Dict[str, str] = {}
        file_path = "../resources/hexawar.properties"
        if not os.path.exists(file_path):
            
            raise FileNotFoundError(f"Properties file not found: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()

        return props
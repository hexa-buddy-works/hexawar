import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import sqlite3
import threading

from hexlogger import HLogger as HLogr
from psycopg2.extensions import connection as PGConnection
from psycopg2.extensions import cursor as PGCursor
from typing import Dict, Optional, Tuple


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
    _p_loadr: PropertyLoader = None
    def __new__(cls, properties_path: str = "resources/hexawar.properties"):
        # Double-checked locking for singleton instance creation
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = super(SqliteDB, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self, properties_path: str = "resources/hexawar.properties"):
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
        self._p_loadr = PropertyLoader(self._properties_path)
        props = PropertyLoader("resources/hexawar.properties").load_properties()

        db_path = props.get("db.path")
        if not db_path:
            raise ValueError("Missing required property: db.path")

        # Ensure directory exists if it's a file path (not :memory:)
        if db_path != ":memory:":
            parent_dir = os.path.dirname(os.path.abspath(db_path))
            if parent_dir and not os.path.exists(parent_dir):
                os.makedirs(parent_dir, exist_ok=True)

        timeout = float(props.get("db.timeout", "5"))
        check_same_thread = self._p_loadr._to_bool(props.get("db.check_same_thread"), default=True)

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
                cur.execute(f"PRAGMA foreign_keys={'ON' if self._p_loadr._to_bool(foreign_keys) else 'OFF'};")
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

    
    

class PropertyLoader:

    def __init__(self, properties_path):
        self._properties_path = properties_path
    

    def load_properties(self) -> Dict[str, str]:
        """
        Load key=value pairs from a .properties file.
        Supports comments starting with # or ; and ignores blank lines.
        """
        props: Dict[str, str] = {}
        
        if not os.path.exists(self._properties_path):
            
            raise FileNotFoundError(f"Properties file not found: {self._properties_path}")

        with open(self._properties_path, "r", encoding="utf-8") as f:
            for raw_line in f:
                line = raw_line.strip()
                if not line or line.startswith("#") or line.startswith(";"):
                    continue
                if "=" not in line:
                    continue
                key, value = line.split("=", 1)
                props[key.strip()] = value.strip()

        return props

    def _to_bool(self,value: Optional[str], default: bool = False) -> bool:
        if value is None:
            return default
        v = value.strip().lower()
        return v in ("1", "true", "yes", "y", "on")
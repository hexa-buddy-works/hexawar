import os
import sys

from db import SqliteDB
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


sqlit_db = SqliteDB()

cur = sqlit_db.get_cursor(row_factory=True)
#cur.execute("SELECT datetime('now') AS server_time;")
cur.execute("select * from sec_war_findings;")
print(dict(cur.fetchone()))

cur.close()
sqlit_db.close()

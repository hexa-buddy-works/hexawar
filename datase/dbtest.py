
from db import PostgresDB, SqliteDB

# db = PostgresDB()

# cur = db.get_cursor(dict_cursor=True)
# cur.execute("SELECT now() AS server_time;")
# print(cur.fetchone())

# cur.close()
# db.close()


sqlit_db = SqliteDB()

cur = sqlit_db.get_cursor(row_factory=True)
cur.execute("SELECT datetime('now') AS server_time;")
print(dict(cur.fetchone()))

cur.close()
sqlit_db.close()

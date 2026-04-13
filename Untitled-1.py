
import sqlite3
conn = sqlite3.connect("database.db")
print(conn.execute("SELECT * FROM users").fetchall())


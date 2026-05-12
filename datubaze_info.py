
import sqlite3

conn = sqlite3.connect("database.db")
c = conn.cursor()

print("=== USERS ===")
for row in c.execute("SELECT * FROM users"):
    print(row)

print("\n=== PLANTS ===")
for row in c.execute("SELECT * FROM plants"):
    print(row)

conn.close()



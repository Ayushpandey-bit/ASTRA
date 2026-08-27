import sqlite3

class Memory:
    def __init__(self):
        self.conn = sqlite3.connect("astra_memory.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            role TEXT,
            message TEXT
        )
        """)

        self.conn.commit()

    def save(self, role, message):
        self.cursor.execute(
            "INSERT INTO memory(role, message) VALUES(?, ?)",
            (role, message)
        )
        self.conn.commit()

    def get_recent(self, limit=10):
        self.cursor.execute(
            "SELECT role, message FROM memory ORDER BY id DESC LIMIT ?",
            (limit,)
        )

        rows = self.cursor.fetchall()
        rows.reverse()
        return rows
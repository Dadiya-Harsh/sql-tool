from sql_agent_tool.database.database_base import DatabaseBase


class SQLiteDatabase(DatabaseBase):
    def __init__(self, db_path: str):
        import sqlite3
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()

    def execute_query(self, query: str):
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close(self):
        self.connection.close()
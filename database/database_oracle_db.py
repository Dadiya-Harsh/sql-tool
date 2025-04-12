from sql_agent_tool.database.database_base import DatabaseBase


class OracleDatabase(DatabaseBase):
    def __init__(self, host, port, username, password, database):
        super().__init__(host, port, username, password, database)
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
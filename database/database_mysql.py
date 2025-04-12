from sql_agent_tool.database.database_base import DatabaseBase


class MySQLDatabase(DatabaseBase):
    def __init__(self, host, user, password, database):
        super().__init__(host, user, password, database)
        self.host = host
        self.user = user
        self.password = password
        self.database = database
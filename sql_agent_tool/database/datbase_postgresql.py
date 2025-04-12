from sqlalchemy import Engine
from sql_agent_tool.database.database_base import DatabaseBase


class PostgreSQLDatabase(DatabaseBase):
    """PostgreSQL database implementation."""

    def create_engine(self) -> Engine:
        """Create a SQLAlchemy engine for PostgreSQL."""
        from sqlalchemy import create_engine
        connection_string = f"postgresql+psycopg2://{self.config.username}:{self.config.password}@{self.config.host}:{self.config.port}/{self.config.database}"
        return create_engine(connection_string, connect_args={"sslmode": "require" if self.config.require_ssl else "prefer"})
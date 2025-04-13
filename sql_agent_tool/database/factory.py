# sql_agent_tool/database/factory.py
from typing import Dict, Type
from sql_agent_tool.models import DatabaseConfig
from sql_agent_tool.database.database_base import DatabaseBase
from sql_agent_tool.database.database_postgresql import PostgreSQLDatabase
from sql_agent_tool.database.database_mssql import MSSQLDatabase
from sql_agent_tool.database.database_mysql import MySQLDatabase
from sql_agent_tool.database.database_oracle_db import OracleDatabase
from sql_agent_tool.database.database_sqllite import SQLiteDatabase


class DatabaseFactory:
    """Factory class for creating database implementations based on driver name."""
    
    # Registry of supported database implementations
    _registry: Dict[str, Type[DatabaseBase]] = {
        'postgresql': PostgreSQLDatabase,
        'mssql': MSSQLDatabase,
        'mysql': MySQLDatabase,
        'oracle': OracleDatabase,
        'sqlite': SQLiteDatabase,
    }
    
    @classmethod
    def get_database(cls, config: DatabaseConfig) -> DatabaseBase:
        """
        Get the appropriate database implementation based on driver name.
        
        Args:
            config (DatabaseConfig): Database configuration object
            
        Returns:
            DatabaseBase: An instance of the appropriate database implementation
            
        Raises:
            ValueError: If the driver name is not supported
        """
        db_class = cls._registry.get(config.drivername.lower())
        if not db_class:
            supported = ', '.join(cls._registry.keys())
            raise ValueError(f"Unsupported database driver: {config.drivername}. "
                            f"Supported drivers are: {supported}")
        
        return db_class(config)
    
    @classmethod
    def register_database(cls, driver_name: str, db_class: Type[DatabaseBase]) -> None:
        """
        Register a new database implementation.
        
        Args:
            driver_name (str): The driver name to register
            db_class (Type[DatabaseBase]): The database implementation class
        """
        cls._registry[driver_name.lower()] = db_class
class SQLAgentError(Exception):
    """Base exception class for all SQLAgentTool-related errors."""
    def __init__(self, message: str = "An error occurred in SQLAgentTool"):
        self.message = message
        super().__init__(self.message)


class SQLValidationError(SQLAgentError):
    """Raised when SQL query validation fails."""
    def __init__(self, query: str, reason: str):
        """
        Args:
            query: The invalid SQL query that caused the error.
            reason: Specific reason why validation failed.
        """
        self.query = query
        self.reason = reason
        message = f"SQL validation failed for query: '{query}'. Reason: {reason}"
        super().__init__(message)


class ParameterExtractionError(SQLAgentError):
    """Raised when parameter extraction from SQL or natural language fails."""
    def __init__(self, sql: str, request: str, error_detail: str):
        """
        Args:
            sql: The SQL query with parameters that failed extraction.
            request: The natural language request being processed.
            error_detail: Specific detail about why extraction failed.
        """
        self.sql = sql
        self.request = request
        self.error_detail = error_detail
        message = (
            f"Parameter extraction failed for request: '{request}' "
            f"and SQL: '{sql}'. Error: {error_detail}"
        )
        super().__init__(message)


class SchemaReflectionError(SQLAgentError):
    """Raised when database schema reflection fails."""
    def __init__(self, database: str, error_detail: str):
        """
        Args:
            database: The database name where reflection failed.
            error_detail: Specific error from the database engine.
        """
        self.database = database
        self.error_detail = error_detail
        message = f"Schema reflection failed for database '{database}'. Error: {error_detail}"
        super().__init__(message)


class QueryExecutionError(SQLAgentError):
    """Raised when SQL query execution fails."""
    def __init__(self, query: str, error_detail: str):
        """
        Args:
            query: The SQL query that failed to execute.
            error_detail: Specific error from the database engine.
        """
        self.query = query
        self.error_detail = error_detail
        message = f"Query execution failed for: '{query}'. Error: {error_detail}"
        super().__init__(message)


class LLMGenerationError(SQLAgentError):
    """Raised when LLM fails to generate valid SQL or parameters."""
    def __init__(self, prompt: str, error_detail: str):
        """
        Args:
            prompt: The prompt sent to the LLM.
            error_detail: Specific error from the LLM response or processing.
        """
        self.prompt = prompt
        self.error_detail = error_detail
        message = f"LLM generation failed for prompt: '{prompt}'. Error: {error_detail}"
        super().__init__(message)

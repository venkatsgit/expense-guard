from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
import urllib


class AzureConnectionManager:
    _engines = {}

    def __init__(self, **kwargs):
        self.config_key = self._build_key(kwargs)
        if self.config_key not in AzureConnectionManager._engines:
            AzureConnectionManager._engines[self.config_key] = self._create_engine(
                kwargs)

    def _build_key(self, kwargs) -> str:
        return f"{kwargs.get('database')}"

    def _create_engine(self, db_config) -> Engine:
        required_keys = ['user_name', 'password', 'host', 'database']
        missing_keys = [k for k in required_keys if k not in db_config]
        if missing_keys:
            raise ValueError(
                f"Missing required DB config keys: {missing_keys}")

        conn_str = (
            f"DRIVER={{ODBC Driver 18 for SQL Server}};"
            f"SERVER={db_config['host']},{db_config.get('port', 1433)};"
            f"DATABASE={db_config['database']};"
            f"UID={db_config['user_name']};"
            f"PWD={db_config['password']};"
            f"Encrypt=yes;"
            f"TrustServerCertificate=yes;"
        )
        connection_url = f"mssql+pyodbc:///?odbc_connect={urllib.parse.quote_plus(conn_str)}"

        return create_engine(
            connection_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )

    def get_engine(self) -> Engine:
        return AzureConnectionManager._engines[self.config_key]

    @classmethod
    def execute_query(cls, config_key: str, query: str):
        """
        Run a SQL query for a given config key.
        Connection is automatically managed.
        """
        engine = cls._engines.get(config_key)
        if not engine:
            raise ValueError(f"No engine found for config_key: {config_key}")

        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
            return [dict(row._mapping) for row in rows]

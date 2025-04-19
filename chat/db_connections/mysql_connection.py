from sqlalchemy import create_engine, text
from typing import Dict
import time

class MySQLConnectionManager:
    _engines: Dict[str, any] = {}

    def __init__(self, **kwargs):
        self.config_key = self._build_key(kwargs)
        if self.config_key not in MySQLConnectionManager._engines:
            MySQLConnectionManager._initialize_engine(kwargs)

    @staticmethod
    def _build_key(config: dict) -> str:
        return f"{config.get('database')}"

    @classmethod
    def _initialize_engine(cls, config: dict):
        config_key = cls._build_key(config)
        if config_key in cls._engines:
            return
        
        required_keys = ['user_name', 'password', 'host', 'database']
        missing_keys = [k for k in required_keys if k not in config]
        if missing_keys:
            raise ValueError(
                f"Missing required DB config keys: {missing_keys}")

        connection_url = (
            f"mysql+mysqlconnector://{config['user_name']}:{config['password']}"
            f"@{config['host']}:{config.get('port', 3306)}/{config['database']}"
        )

        engine = create_engine(
            connection_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=1800,
        )

        # Optional: warm up pool
        with engine.connect() as conn:
            pass

        cls._engines[config_key] = engine

    @classmethod
    def execute_query(cls, config_key: str, query: str):
        """
        Execute a SELECT query using a pooled connection.
        """
        engine = cls._engines.get(config_key)
        if not engine:
            raise ValueError(f"No engine found for config_key: {config_key}")

        if not query.strip().lower().startswith("select"):
            raise ValueError("Only SELECT queries are allowed.")

        with engine.connect() as conn:
            result = conn.execute(text(query))
            rows = result.fetchall()
        return [dict(row._mapping) for row in rows]

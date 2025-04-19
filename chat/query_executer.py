from db_connections.azure_wh_connection import AzureConnectionManager
from db_connections.mysql_connection import MySQLConnectionManager


class QueryExecuter:

    def __init__(self, db_type: str = "mysql", query: str = "", **kwargs):
        self.db_type = db_type.lower()
        self.query = query
        self.kwargs = kwargs

    def execute(self):
        if self.db_type == "mysql":
            return self._execute_mysql()
        elif self.db_type == "azure_wh":
            return self._execute_azure_wh()
        else:
            raise NotImplementedError(
                f"DB type '{self.db_type}' is not supported.")

    def _execute_mysql(self):

        try:
            mysql = MySQLConnectionManager(**self.kwargs)
            return mysql.execute_query(config_key=self.kwargs.get('database'), query=self.query)
        except Exception as e:
            print(f"MySQL Error: {e}")
            return None

    def _execute_azure_wh(self):

        try:
            azure = AzureConnectionManager(**self.kwargs)
            return azure.execute_query(config_key=self.kwargs.get('database'), query=self.query)
        except Exception as e:
            print(f"MySQL Error: {e}")
            return None

import os
from logging import getLogger
from typing import Dict, List, Optional

import cx_Oracle
import pandas
from pandas.io import sql as psql

from tests.lib.base_processing import BaseProcessing

logger = getLogger(__name__)


class OracleProcessing(BaseProcessing):
    _column_types_and_names_matching = {
        "id_int": "INTEGER GENERATED BY DEFAULT AS IDENTITY",
        "text_string": "VARCHAR2(50) NOT NULL",
        "hwm_int": "INTEGER",
        "hwm_date": "DATE",
        "hwm_datetime": "TIMESTAMP",
        "float_value": "FLOAT",
    }

    def __enter__(self):
        self.connection = self.get_conn()
        return self

    def __exit__(self, _exc_type, _exc_value, _traceback):
        self.connection.close()
        return False

    @property
    def sid(self) -> str:
        return os.getenv("ONETL_ORA_CONN_SID")

    @property
    def service_name(self) -> str:
        return os.getenv("ONETL_ORA_CONN_SERVICE_NAME")

    @property
    def user(self) -> str:
        return os.getenv("ONETL_ORA_CONN_USER")

    @property
    def password(self) -> str:
        return os.getenv("ONETL_ORA_CONN_PASSWORD")

    @property
    def host(self) -> str:
        return os.getenv("ONETL_ORA_CONN_HOST")

    @property
    def port(self) -> int:
        return int(os.getenv("ONETL_ORA_CONN_PORT"))

    @property
    def schema(self) -> str:
        return os.getenv("ONETL_ORA_CONN_SCHEMA", "onetl")

    @property
    def url(self) -> str:
        dsn = cx_Oracle.makedsn(self.host, self.port, sid=self.sid, service_name=self.service_name)
        return f"oracle://{self.user}:{self.password}@{dsn}"

    def get_conn(self) -> cx_Oracle.Connection:
        try:
            cx_Oracle.init_oracle_client(lib_dir=os.getenv("ONETL_ORA_CLIENT_PATH"))
        except Exception:
            logger.debug("cx_Oracle client is already initialized.", exc_info=True)
        dsn = cx_Oracle.makedsn(self.host, self.port, sid=self.sid, service_name=self.service_name)
        return cx_Oracle.connect(user=self.user, password=self.password, dsn=dsn)

    def create_schema_ddl(
        self,
        schema: str,
    ) -> str:
        return f"CREATE SCHEMA AUTHORIZATION {schema}"

    def create_schema(
        self,
        schema: str,
    ) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(self.create_schema_ddl(schema))
            self.connection.commit()

    def create_table(
        self,
        table: str,
        fields: Dict[str, str],
        schema: str,
    ) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(self.create_table_ddl(table, fields, schema))
            self.connection.commit()

    def drop_database_ddl(
        self,
        schema: str,
    ) -> str:
        return f"DROP DATABASE {schema}"

    def drop_database(
        self,
        schema: str,
    ) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(self.drop_database_ddl(schema))
            self.connection.commit()

    def drop_table_ddl(
        self,
        table: str,
        schema: str,
    ) -> str:
        return f"DROP TABLE {schema}.{table} PURGE"

    def drop_table(
        self,
        table: str,
        schema: str,
    ) -> None:
        with self.connection.cursor() as cursor:
            cursor.execute(self.drop_table_ddl(table, schema))
            self.connection.commit()

    def insert_data(
        self,
        schema: str,
        table: str,
        values: "pandas.core.frame.DataFrame",  # noqa: F821
    ) -> None:
        # <con> parameter is SQLAlchemy connectable or str
        # A database URI could be provided as as str.
        psql.to_sql(
            frame=values,
            name=table,
            con=self.url,
            index=False,
            schema=schema,
            if_exists="append",
        )

    def get_expected_dataframe(
        self,
        schema: str,
        table: str,
        order_by: Optional[List[str]] = None,
    ) -> "pandas.core.frame.DataFrame":  # noqa: F821
        return pandas.read_sql_query(self.get_expected_dataframe_ddl(schema, table, order_by), con=self.connection)

    def fix_pandas_df(
        self,
        df: "pandas.core.frame.DataFrame",  # noqa: F821
    ) -> "pandas.core.frame.DataFrame":  # noqa: F821
        # Oracle returns column names in UPPERCASE, convert them back to lowercase
        rename_columns = {x: x.lower() for x in df}
        df = df.rename(columns=rename_columns, inplace=False)

        for column in df:  # noqa: WPS528
            column_names = column.split("_")

            # Type conversion is required since Spark stores both Integer and Float as Numeric
            if "int" in column_names:
                df[column] = df[column].astype("int64")
            elif "float" in column_names:
                df[column] = df[column].astype("float64")
            elif "datetime" in column_names:
                # I'm not sure why, but something does not support milliseconds
                # It's either Spark 2.3 (https://stackoverflow.com/a/57929964/16977118) or pandas.io.sql
                # So cut them off
                df[column] = df[column].astype("datetime64[ns]").dt.floor("S")
            elif "date" in column_names:
                # Oracle's Date type is actually Datetime, so we need to truncate dates
                df[column] = df[column].astype("datetime64[ns]").dt.date

        return df

from __future__ import annotations

from datetime import date, datetime
from typing import ClassVar, Optional

from onetl.connection.db_connection.jdbc_connection import JDBCConnection


class MySQL(JDBCConnection):
    """Class for MySQL JDBC connection.

    Based on Maven package ``mysql:mysql-connector-java:8.0.30``
    (`official MySQL JDBC driver <https://dev.mysql.com/downloads/connector/j/8.0.html>`_)

    .. note::

        Supported MySQL server versions: >= 5.6

    Parameters
    ----------
    host : str
        Host of MySQL database. For example: ``mysql0012.domain.com`` or ``192.168.1.11``

    port : int, default: ``3306``
        Port of MySQL database

    user : str
        User, which have access to the database and table. For example: ``some_user``

    password : str
        Password for database connection

    database : str
        Database in RDBMS, NOT schema.

        See `this page <https://www.educba.com/postgresql-database-vs-schema/>`_ for more details

    spark : :obj:`pyspark.sql.SparkSession`
        Spark session that required for jdbc connection to database.

        You can use ``mtspark`` for spark session initialization

    extra : dict, default: ``None``
        Specifies one or more extra parameters by which clients can connect to the instance.

        For example: ``{"useSSL": "false"}``

        See `MySQL JDBC driver properties documentation
        <https://dev.mysql.com/doc/connector-j/8.0/en/connector-j-reference-configuration-properties.html>`_
        for more details

    Examples
    --------

    MySQL connection initialization

    .. code::

        from onetl.connection import MySQL
        from mtspark import get_spark

        extra = {"useSSL": "false"}

        spark = get_spark({
            "appName": "spark-app-name",
            "spark.jars.packages": [MySQL.package],
        })

        mysql = MySQL(
            host="database.host.or.ip",
            user="user",
            password="*****",
            extra=extra,
            spark=spark,
        )

    """

    class Extra(JDBCConnection.Extra):
        useUnicode: str = "yes"  # noqa: N815
        characterEncoding: str = "UTF-8"  # noqa: N815

    port: int = 3306
    database: Optional[str] = None
    extra: Extra = Extra()

    driver: ClassVar[str] = "com.mysql.jdbc.Driver"
    package: ClassVar[str] = "mysql:mysql-connector-java:8.0.30"

    @property
    def jdbc_url(self):
        prop = self.extra.dict(by_alias=True)
        parameters = "&".join(f"{k}={v}" for k, v in sorted(prop.items()))

        if self.database:
            return f"jdbc:mysql://{self.host}:{self.port}/{self.database}?{parameters}"

        return f"jdbc:mysql://{self.host}:{self.port}?{parameters}"

    class ReadOptions(JDBCConnection.ReadOptions):
        @classmethod
        def partition_column_hash(cls, partition_column: str, num_partitions: int) -> str:
            return f"MOD(CONV(CONV(RIGHT(MD5({partition_column}), 16),16, 2), 2, 10), {num_partitions})"

        @classmethod
        def partition_column_mod(cls, partition_column: str, num_partitions: int) -> str:
            return f"MOD({partition_column}, {num_partitions})"

    def _get_datetime_value_sql(self, value: datetime) -> str:
        result = value.strftime("%Y-%m-%d %H:%M:%S.%f")
        return f"STR_TO_DATE('{result}', '%Y-%m-%d %H:%i:%s.%f')"  # noqa: WPS323

    def _get_date_value_sql(self, value: date) -> str:
        result = value.strftime("%Y-%m-%d")
        return f"STR_TO_DATE('{result}', '%Y-%m-%d')"  # noqa: WPS323

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, ClassVar

from onetl.connection.db_connection.jdbc_connection import JDBCConnection


@dataclass(frozen=True)
class Teradata(JDBCConnection):
    """Class for Teradata jdbc connection.

    Parameters
    ----------
    host : str
        Host of teradata database. For example: ``0411td-rnd.pv.mts.ru``

    port : int, default: ``1025``
        Port of teradata database

    user : str
        User, which have access to the database and table. For example: ``TECH_ETL``

    password : str
        Password for database connection

    database : str
        Database in rdbms. To provide schema, use DBReader class

    spark : :obj:`pyspark.sql.SparkSession`
        Spark session that required for jdbc connection to database.

        You can use ``mtspark`` for spark session initialization

    extra : dict, default: ``None``
        Specifies one or more extra parameters which should be appended to a connection string.

        For example: ``{"MODE": "TERA", "MAYBENULL": "ON", "CHARSET": "UTF8", "LOGMECH":"LDAP"}``

        .. note::

            By default, ``STRICT_NAMES=OFF`` and ``FLATTEN=ON`` options are added to extra.

            It is possible to pass different values for these options,
            e.g. ``extra={"FLATTEN": "OFF"}``

    Examples
    --------

    Teradata jdbc connection initialization

    .. code::

        from onetl.connection import Teradata
        from mtspark import get_spark

        extra = {
            "LOGMECH": "TERA",
            "MAYBENULL": "ON",
            "CHARSET": "UTF8",
            "LOGMECH":"LDAP",
        }

        spark = get_spark({
            "appName": "spark-app-name",
            "spark.jars.packages": [Teradata.package],
        })

        teradata = Teradata(
            host="0411td-rnd.pv.mts.ru",
            user="BD_TECH_ETL",
            password="*****",
            extra=extra,
            spark=spark,
        )

    """

    driver: ClassVar[str] = "com.teradata.jdbc.TeraDriver"
    # TODO:(@mivasil6) think about workaround for case with several jar packages
    package: ClassVar[str] = "com.teradata.jdbc:terajdbc4:17.10.00.25"
    port: int = 1025

    _check_query: ClassVar[str] = "SELECT 1 AS check_result"
    _default_extra: ClassVar[dict[str, Any]] = {
        "STRICT_NAMES": "OFF",
        "FLATTEN": "ON",
    }

    @property
    def jdbc_url(self) -> str:
        prop = self._default_extra.copy()
        prop.update(self.extra)

        if self.database:
            prop["DATABASE"] = self.database

        prop["DBS_PORT"] = self.port

        conn = ",".join(f"{k}={v}" for k, v in prop.items())
        return f"jdbc:teradata://{self.host}/{conn}"

    def _get_datetime_value_sql(self, value: datetime) -> str:
        result = value.isoformat()
        return f"CAST('{result}' AS TIMESTAMP)"

    def _get_date_value_sql(self, value: date) -> str:
        result = value.isoformat()
        return f"CAST('{result}' AS DATE)"

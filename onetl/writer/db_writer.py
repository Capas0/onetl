from __future__ import annotations

from dataclasses import dataclass
from logging import getLogger

from etl_entities import Table
from onetl.connection.db_connection import DBConnection
from onetl.connection.connection_helpers import decorated_log


log = getLogger(__name__)
# TODO:(@mivasil6) implement logging


@dataclass
class DBWriter:
    """Class specifies database and table where you can write your dataframe.

    Parameters
    ----------
    connection : onetl.connection.db_connection.DBConnection
        Class which contain DB connection properties. See in DBConnection section.
    table : str
        Table from which we read. You need to specify the full path to the table, including the schema.
        Like ``schema.name``

    options : dict, DBConnection.Options, optional, default: ``None``
        Spark JDBC or Hive write options.

        For example:
        ``{"mode": "overwrite", "compression": "snappy"}``
        or
        ``Hive.Options(mode="overwrite", compression="snappy")``

        Hive and JDBC options:
            * ``mode`` : str, optional, default: ``append``
                        The way of handling errors when the table is already exists.

                        Possible values:
                            * ``overwrite``
                                Remove old table data and write new one
                            * ``append``
                                Append data to a table
                            * ``ignore``
                                Don't write anything
                            * ``error``
                                Raise exception
        Hive options:
            * ``format`` : str, optional, default: ``orc``
                Format of written data. Can be ``json``, ``parquet``, ``orc``, ``csv``, ``text``, ``avro``

            * ``insertInto``: bool, optional, default: ``False``
                If you need to insert data into an existing table then set option as True.
                Used pyspark method `insertInto <https://t.ly/0RRH>`_ under the hood.

            * ``partitionBy``: str, List[str], optional, default: ``None``
                Column names which will be used for the output partitioning.

                If set, the output is laid out on the file system similar
                to Hive's partitioning scheme.

            * ``bucketBy``: Tuple[int, str] or Tuple[int, List[str]], optional, default: ``None``
                Divide output to specific number of buckets over a column/columns.

                If set, the output is laid out on the file system *similar* to Hive's bucketing scheme,
                but with a **different bucket hash function** which is not compatible with Hive's bucketing.

            * ``sortBy``: str or List[str], optional, default: ``None``
                Sorts the output in each bucket by the given columns.

            * other options
                Options that are written to the ``option`` method are specified without specifying the
                ``option`` method

                For example:

                    .. code::

                        DBWriter(
                            connection=hive,
                            table="onetl.some_table",
                            options=Hive.Options(compression="snappy"),
                        )

        JDBC options:
            * ``numPartitions``
            * ``queryTimeout``
            * ``batchsize``
            * ``isolationLevel``
            * ``truncate``
            * ``cascadeTruncate``
            * ``createTableOptions``
            * ``createTableColumnTypes``

        You can find a description of the options at the link below:

        https://spark.apache.org/docs/2.4.0/sql-data-sources-jdbc.html


    Examples
    --------
    Simple Writer creation:

    .. code::

        from onetl.writer import DBWriter
        from onetl.connection.db_connection import Postgres
        from mtspark import get_spark

        spark = get_spark({
            "appName": "spark-app-name",
            "spark.jars.packages": Postgres.package,
        })

        postgres = Postgres(
            host="test-db-vip.msk.mts.ru",
            user="your_user",
            password="***",
            database="target_db",
            spark=spark,
        )

        writer = DBWriter(
            connection=postgres,
            table="fiddle.dummy",
        )

    Writer creation with options:

    .. code::

        from onetl.writer import DBWriter
        from onetl.connection.db_connection import Postgres
        from mtspark import get_spark

        spark = get_spark({
            "appName": "spark-app-name",
            "spark.jars.packages": Postgres.package,
        })

        postgres = Postgres(
            host="test-db-vip.msk.mts.ru",
            user="your_user",
            password="***",
            database="target_db",
            spark=spark,
        )

        options = {"truncate": "true", "batchsize": 1000}
        # or (it is the same):
        options = Postgres.Options(truncate=True, batchsize=1000}

        writer = DBWriter(
            connection=postgres,
            table="fiddle.dummy",
            options=options,
        )

    Writer to Hive with options:

    .. code::

        from onetl.connection.db_connection import Hive
        from onetl.reader import DBWriter
        from mtspark import get_spark

        spark = get_spark({"appName": "spark-app-name"})

        hive = Hive(spark=spark)

        options = {"compression": "snappy", "partitionBy": "id"}
        # or (it is the same):
        options = Hive.Options(compression="snappy", partitionBy="id")

        writer = DBWriter(
            connection=hive,
            table="default.test",
            options=options,
        )
    """

    connection: DBConnection
    table: Table
    options: DBConnection.Options

    def __init__(
        self,
        connection: DBConnection,
        table: str,
        options: DBConnection.Options | dict | None = None,
    ):
        self.connection = connection
        self.table = self._handle_table(table)
        self.options = self._handle_options(options)

    def run(self, df):
        """
        Method for writing your df to specified table.

        Parameters
        ----------
        df : pyspark.sql.dataframe.DataFrame
            Spark dataframe

        Examples
        --------

        Write df to table:

        .. code::

            writer.run(df)

        """
        decorated_log(msg="DBWriter starts")

        log.info(f"|Spark| -> |{self.connection.__class__.__name__}| Writing DataFrame to {self.table}")

        self.connection.save_df(
            df=df,
            table=str(self.table),
            options=self.options,
        )

        decorated_log(msg="DBWriter ends", char="-")

    def _handle_table(self, table: str) -> Table:
        return Table(name=table, instance=self.connection.instance_url)

    def _handle_options(self, options: DBConnection.Options | dict | None) -> DBConnection.Options:
        if options:
            return self.connection.to_options(options)

        return self.connection.Options()

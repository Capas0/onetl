#  Copyright 2022 MTS (Mobile Telesystems)
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

from __future__ import annotations

import logging
import textwrap
from enum import Enum
from typing import TYPE_CHECKING, Any, ClassVar
from urllib import parse as parser

from etl_entities.instance import Host
from frozendict import frozendict
from pydantic import SecretStr

if TYPE_CHECKING:
    from pyspark.sql.types import StructType
    from pyspark.sql import DataFrame

from onetl.connection.db_connection.db_connection import DBConnection
from onetl.impl import GenericOptions

log = logging.getLogger(__name__)

_upper_level_operators = frozenset(  # noqa: WPS527
    [
        "$addFields",
        "$bucket",
        "$bucketAuto",
        "$changeStream",
        "$collStats",
        "$count",
        "$currentOp",
        "$densify",
        "$documents",
        "$facet",
        "$fill",
        "$geoNear",
        "$graphLookup",
        "$group",
        "$indexStats",
        "$limit",
        "$listLocalSessions",
        "$listSessions",
        "$lookup",
        "$merge",
        "$out",
        "$planCacheStats",
        "$project",
        "$redact",
        "$replaceRoot",
        "$replaceWith",
        "$sample",
        "$search",
        "$searchMeta",
        "$set",
        "$setWindowFields",
        "$shardedDataDistribution",
        "$skip",
        "$sort",
        "$sortByCount",
        "$unionWith",
        "$unset",
        "$unwind",
    ],
)


class MongoDBWriteMode(str, Enum):  # noqa: WPS600
    APPEND = "append"
    OVERWRITE = "overwrite"

    def __str__(self) -> str:
        return str(self.value)


PROHIBITED_OPTIONS = frozenset(
    (
        "uri",
        "database",
        "collection",
        "pipeline",
        "hint",
    ),
)

KNOWN_READ_OPTIONS = frozenset(
    (
        "localThreshold",
        "readPreference.name",
        "readPreference.tagSets",
        "readConcern.level",
        "sampleSize",
        "samplePoolSize",
        "partitioner",
        "partitionerOptions",
        "registerSQLHelperFunctions",
        "sql.inferschema.mapTypes.enabled",
        "sql.inferschema.mapTypes.minimumKeys",
        "sql.pipeline.includeNullFilters",
        "sql.pipeline.includeFiltersAndProjections",
        "pipeline",
        "hint",
        "collation",
        "allowDiskUse",
        "batchSize",
    ),
)

KNOWN_WRITE_OPTIONS = frozenset(
    (
        "extendedBsonTypes",
        "localThreshold",
        "replaceDocument",
        "maxBatchSize",
        "writeConcern.w",
        "writeConcern.journal",
        "writeConcern.wTimeoutMS",
        "shardKey",
        "forceInsert",
        "ordered",
    ),
)


class MongoDB(DBConnection):
    """MongoDB connection.

    Based on package ``org.mongodb.spark:mongo-spark-connector``
    (`MongoDB connector for Spark <https://www.mongodb.com/docs/spark-connector/master/python-api/>`_)

    .. warning::

        To use Greenplum connector you should have PySpark installed (or injected to ``sys.path``)
        BEFORE creating the connector instance.

        You can install PySpark as follows:

        .. code:: bash

            pip install onetl[spark]  # latest PySpark version

            # or
            pip install onetl pyspark=3.3.1  # pass specific PySpark version

        See :ref:`spark-install` instruction for more details.

    Parameters
    ----------
    host : str
        Host of MongoDB. For example: ``test.mongodb.com`` or ``193.168.1.17``.

    port : int, default: ``27017``.
        Port of MongoDB

    user : str
        User, which have proper access to the database. For example: ``some_user``.

    password : str
        Password for database connection.

    database : str
        Database in MongoDB.

    spark : :obj:`pyspark.sql.SparkSession`
        Spark session.

    Examples
    --------

    MongoDB connection initialization.

    .. code:: python

        from onetl.connection import MongoDB
        from pyspark.sql import SparkSession

        spark = (
            SparkSession.builder.appName("spark-app-name")
            .config("spark.jars.packages", MongoDB.package_spark_2_4)
            .getOrCreate()
        )

        mongo = MongoDB(
            host="master.host.or.ip",
            user="user",
            password="*****",
            database="target_database",
            spark=spark,
        )
    """

    database: str
    host: Host
    user: str
    password: SecretStr
    port: int = 27017
    package_spark_2_4: ClassVar[str] = "org.mongodb.spark:mongo-spark-connector_2.11:2.4.4"  # noqa: WPS114
    package_spark_2_3: ClassVar[str] = "org.mongodb.spark:mongo-spark-connector_2.11:2.3.6"  # noqa: WPS114
    package_spark_3_2: ClassVar[str] = "org.mongodb.spark:mongo-spark-connector_2.12:3.0.2"  # noqa: WPS114
    package_spark_3_3: ClassVar[str] = "org.mongodb.spark:mongo-spark-connector_2.12:3.0.2"  # noqa: WPS114

    class ReadOptions(GenericOptions):
        """MongoDB connector for Spark reading options.

        .. note ::

            You can pass any value
            `supported by connector <https://www.mongodb.com/docs/spark-connector/master/configuration/
            #:~:text=See%20Cache%20Configuration.-,Input%20Configuration,-You%20can%20configure>`_,
            even if it is not mentioned in this documentation.

            The set of supported options depends on connector version.

        .. warning::

            Options ``uri``, ``database``, ``collection`` are populated from connection attributes,
            and cannot be set in ``ReadOptions`` class.

        Examples
        --------

        Read options initialization

        .. code:: python

            MongoDB.ReadOptions(
                pipeline="{'$match': {'number':{'$gte': 3}}}",
            )
        """

        class Config:
            prohibited_options = PROHIBITED_OPTIONS
            known_options = KNOWN_READ_OPTIONS
            extra = "allow"

    class WriteOptions(GenericOptions):
        """MongoDB connector for writing reading options.

        .. note ::

            You can pass any value
            `supported by connector <https://www.mongodb.com/docs/spark-connector/master/configuration/
            #:~:text=input.database%3Dbar-,Output%20Configuration,-The%20following%20options>`_,
            even if it is not mentioned in this documentation.

            The set of supported options depends on connector version.

        .. warning::

            Options ``uri``, ``database``, ``collection`` are populated from connection attributes,
            and cannot be set in ``WriteOptions`` class.

        Examples
        --------

        Write options initialization

        .. code:: python

            options = MongoDB.WriteOptions(
                mode="append",
                sampleSize=500,
                localThreshold=20,
            )
        """

        mode: MongoDBWriteMode = MongoDBWriteMode.APPEND
        """Mode of writing data into target table.

        Possible values:
            * ``append`` (default)
                Appends data into existing table.

                Behavior in details:

                * Table does not exist
                    Table is created using other options from current class
                    (``shardkey`` and others).

                * Table exists
                    Data is appended to a table. Table has the same DDL as before writing data

            * ``overwrite``
                Overwrites data in the entire table (**table is dropped and then created, or truncated**).

                Behavior in details:

                * Table does not exist
                    Table is created using other options from current class
                    (``shardkey`` and others).

                * Table exists
                    Table content is replaced with dataframe content.

                    After writing completed, target table could either have the same DDL as
                    before writing data, or can be recreated.

        .. note::

            ``error`` and ``ignore`` modes are not supported.
        """

        class Config:
            prohibited_options = PROHIBITED_OPTIONS
            known_options = KNOWN_WRITE_OPTIONS
            extra = "allow"

    @property
    def instance_url(self) -> str:
        return f"{self.__class__.__name__.lower()}://{self.host}:{self.port}/{self.database}"

    def check(self):
        log.info(f"|{self.__class__.__name__}| Checking connection availability...")
        self._log_parameters()

        try:
            jvm = self.spark._sc._gateway.jvm  # noqa: WPS437
            client = jvm.com.mongodb.client.MongoClients.create(self._url)
        except Exception as e:
            spark_version = "_".join(self.spark.version.split(".")[:1])

            raise RuntimeError(
                textwrap.dedent(
                    f"""
                    Cannot import Java package 'com.mongodb.client'.

                    It looks like you've created Spark session without this option:
                        SparkSession.builder.config("spark.jars.packages", MongoDB.package_spark_{spark_version})

                    Please stop Spark session, restart the interpreter,
                    and create SparkSession again with proper options.
                    """,
                ).strip(),
            ) from e

        try:
            list(client.listDatabaseNames().iterator())
            log.info(f"|{self.__class__.__name__}| Connection is available.")
        except Exception as e:
            log.exception(f"|{self.__class__.__name__}| Connection is unavailable")
            raise RuntimeError("Connection is unavailable") from e

        return self

    def get_schema(self, table: str, columns: list[str] | None = None) -> StructType:  # noqa: WPS463
        pass  # noqa: WPS420

    def get_min_max_bounds(  # type:ignore  # noqa: WPS463
        self,
        table: str,
        column: str,
        expression: str | None = None,
        hint: dict | None = None,
        where: dict | None = None,
    ) -> tuple[Any, Any]:
        return ""  # type: ignore

    class Dialect:
        """
        The class contains methods for generating queries transmitted to the database. requests are formed from
        parameters passed to DBReader.
        """

        @classmethod
        def check_where_parameter(cls, where: str | dict) -> bool:
            """
            Checks the parameter passed to DBReader. Passed value cannot be a string.
            """
            if isinstance(where, str):
                raise ValueError(
                    "|MongoDB| Parameter 'where' cannot be a string, 'dict' must be passed.",
                )
            for key, _ in where.items():
                cls._validate_top_level_keys_in_where_parameter(key)
            return True

        @classmethod
        def check_hint_parameter(cls, hint: str | dict) -> bool:
            """
            Checks the parameter passed to DBReader. Passed value cannot be a string.
            """
            if isinstance(hint, str):
                raise ValueError("|MongoDB| Parameter 'hint' cannot be a string, 'dict' must be passed.")
            return True

        @classmethod
        def convert_filter_parameter_to_pipeline(
            cls,
            parameter: list | frozendict | dict,
        ) -> str:  # noqa: WPS212, WPS231, WPS430
            """
            Converts the given dictionary, list or primitive to a string. for each element of the collection,
            the method calls itself and internally processes each element depending on its type.
            """
            if isinstance(parameter, (frozendict, dict)):
                return cls._build_string_pipeline_from_dictionary(parameter)

            if isinstance(parameter, list):
                return cls._build_string_pipeline_from_list(parameter)

            return cls._build_string_pipeline_from_simple_types(parameter)

        @classmethod
        def generate_where_request(cls, where: frozendict) -> str:  # noqa: WPS212, WPS231
            """
            The passed frozendict is converted to a MongoDb-readable format, the original result is passed to the
            pipeline.

            """
            blank_pipeline = "{{'$match':{custom_condition}}}"
            return blank_pipeline.format(custom_condition=cls.convert_filter_parameter_to_pipeline(where))

        @classmethod
        def _build_string_pipeline_from_dictionary(cls, parameter: dict):
            """
            Converts the passed map to a string. Map elements can be collections. Loops through all elements of the map
            and converts each to a string depending on the type of each element.
            """
            list_of_operations = []
            for key, value in parameter.items():
                value = (
                    cls.convert_filter_parameter_to_pipeline(key)
                    + ":"
                    + cls.convert_filter_parameter_to_pipeline(value)
                )
                list_of_operations.append(value)
            return "{" + ",".join(list_of_operations) + "}"

        @classmethod
        def _validate_top_level_keys_in_where_parameter(cls, key: str):
            """
            Checks the 'where' parameter for illegal operators, such as ``$match``, ``$merge`` or ``$changeStream``.

            'where' clause can contain only filtering operators, like ``{"col1" {"$eq": 1}}`` or ``{"$and": [...]}``.
            """
            if key.startswith("$"):
                if key == "$match":
                    raise ValueError(
                        "|MongoDB| $match operator not allowed at the top level of the 'where' parameter dictionary."
                        "This error most likely occurred due to the fact that you used the MongoDB format for the "
                        "pipeline {'$match': {'column': ...}}. In the onETL paradigm, you do not need to specify the "
                        "$match keyword, but write the filtering condition right away {'column': ...}",
                    )
                if key in _upper_level_operators:  # noqa: WPS220
                    raise ValueError(  # noqa: WPS220
                        f"|MongoDB| An invalid parameter {key!r} was specified in the 'where' "
                        "field.\nYou cannot use aggregations or 'groupBy' clauses in 'where'.",
                    )

        @classmethod
        def _build_string_pipeline_from_list(cls, param: list) -> str:
            """
            The passed list is converted to a string. The elements of the list can be dictionaries. Iterates through all
            the elements of the list and processes each element by converting it to a string.
            """
            list_of_operations = []
            for elem in param:
                list_value = cls.convert_filter_parameter_to_pipeline(elem)
                list_of_operations.append(list_value)
            return "[" + ",".join(list_of_operations) + "]"

        @classmethod
        def _build_string_pipeline_from_simple_types(cls, param: str | int | bool | float) -> str:
            """
            Wraps the passed parameters in parentheses. Doesn't work with collections.
            """
            if isinstance(param, str):
                return "'" + param + "'"

            if isinstance(param, bool):
                return str(param).lower()

            if param is None:
                return "null"

            if isinstance(param, int):
                return str(param)

            raise ValueError(f"|MongoDB| Wrong value type : {type(param)}")

    def read_table(
        self,
        table: str,
        columns: list[str] | None = None,
        hint: dict | None = None,
        where: dict | None = None,
        options: ReadOptions | dict | None = None,
    ) -> DataFrame:
        read_options = self.ReadOptions.parse(options).dict(by_alias=True, exclude_none=True)

        if where:
            read_options["pipeline"] = self.Dialect.generate_where_request(where)

        if hint:
            read_options["hint"] = self.Dialect.convert_filter_parameter_to_pipeline(hint)  # noqa: WPS437

        read_options["spark.mongodb.input.uri"] = self._url
        read_options["spark.mongodb.input.collection"] = table

        df = self.spark.read.format("mongo").options(**read_options).load()

        if columns:
            return df.select(*columns)

        return df

    def save_df(
        self,
        df: DataFrame,
        table: str,
        options: WriteOptions | dict | None = None,
    ) -> None:
        write_options = self.WriteOptions.parse(options)
        mode = write_options.mode
        write_options = write_options.dict(by_alias=True, exclude_none=True, exclude={"mode"})
        write_options["spark.mongodb.output.uri"] = self._url
        write_options["spark.mongodb.output.collection"] = table
        df.write.format("mongo").mode(mode).options(**write_options).save()

    @property
    def _url(self) -> str:
        password = parser.quote(self.password.get_secret_value())
        return f"mongodb://{self.user}:{password}@{self.host}:{self.port}/{self.database}"

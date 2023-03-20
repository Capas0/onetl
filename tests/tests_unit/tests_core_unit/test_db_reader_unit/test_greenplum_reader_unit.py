import pytest
from pyspark.sql.types import (
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from onetl.connection import Greenplum
from onetl.core import DBReader


def test_greenplum_reader_snapshot_error_pass_df_schema(spark_mock):
    df_schema = StructType(
        [
            StructField("_id", IntegerType()),
            StructField("text_string", StringType()),
            StructField("hwm_int", IntegerType()),
            StructField("hwm_datetime", TimestampType()),
            StructField("float_value", DoubleType()),
        ],
    )

    greenplum = Greenplum(host="some_host", user="user", database="database", password="passwd", spark=spark_mock)

    with pytest.raises(ValueError, match="'df_schema' parameter is not supported by Greenplum"):
        DBReader(
            connection=greenplum,
            table="schema.table",
            df_schema=df_schema,
        )


@pytest.mark.parametrize("table", ["table", "table.table.table"])
def test_reader_wrong_table(spark_mock, table):
    greenplum = Greenplum(host="some_host", user="user", database="database", password="passwd", spark=spark_mock)
    with pytest.raises(ValueError, match="Table name should be passed in `schema.name` format"):
        DBReader(
            connection=greenplum,
            table=table,  # Missing schema. Required format: table="shema.table"
        )

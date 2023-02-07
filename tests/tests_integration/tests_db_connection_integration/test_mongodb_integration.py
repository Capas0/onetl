import logging

import pytest

from onetl.connection import MongoDB


def test_mongodb_connection_check(spark, processing, caplog):
    mongo = MongoDB(
        host=processing.host,
        port=processing.port,
        user=processing.user,
        password=processing.password,
        database=processing.database,
        spark=spark,
    )

    with caplog.at_level(logging.INFO):
        assert mongo.check() == mongo

    assert "type = MongoDB" in caplog.text
    assert f"host = '{processing.host}'" in caplog.text
    assert f"port = {processing.port}" in caplog.text
    assert f"user = '{processing.user}'" in caplog.text
    assert f"database = '{processing.database}'" in caplog.text

    if processing.password:
        assert processing.password not in caplog.text

    assert "package = " not in caplog.text
    assert "spark = " not in caplog.text

    assert "Connection is available" in caplog.text


def test_mongodb_connection_check_fail(spark):
    mongo = MongoDB(host="host", database="db", user="some_user", password="pwd", spark=spark)

    with pytest.raises(RuntimeError, match="Connection is unavailable"):
        mongo.check()


def test_mongodb_connection_read(spark, processing, load_table_data):
    mongo = MongoDB(
        host=processing.host,
        port=processing.port,
        user=processing.user,
        password=processing.password,
        database=processing.database,
        spark=spark,
    )

    df = mongo.read_table(table=load_table_data.table)

    processing.assert_equal_df(
        schema=load_table_data.schema,
        table=load_table_data.table,
        df=df,
    )


def test_mongodb_connection_write(spark, prepare_schema_table, processing):
    df = processing.create_spark_df(spark=spark)

    mongo = MongoDB(
        host=processing.host,
        port=processing.port,
        user=processing.user,
        password=processing.password,
        database=processing.database,
        spark=spark,
    )

    mongo.save_df(df, table=prepare_schema_table.table)

    processing.assert_equal_df(
        schema=prepare_schema_table.schema,
        table=prepare_schema_table.table,
        df=df,
    )


def test_mongodb_snapshot_with_where(spark, processing, load_table_data):
    mongo = MongoDB(
        host=processing.host,
        port=processing.port,
        user=processing.user,
        password=processing.password,
        database=processing.database,
        spark=spark,
    )

    table_df = mongo.read_table(table=load_table_data.table)

    table_df1 = mongo.read_table(table=load_table_data.table, where={"_id": {"$lt": 1000}}, hint={"_id": 1})

    assert table_df1.count() == table_df.count()

    table_df2 = mongo.read_table(
        table=load_table_data.table,
        where={"$or": [{"_id": {"$lt": 1000}}, {"_id": {"$eq": 1000}}]},
        hint={"_id": 1},
    )

    assert table_df2.count() == table_df.count()

    processing.assert_equal_df(
        schema=load_table_data.schema,
        table=load_table_data.table,
        df=table_df1,
    )

    one_df = mongo.read_table(table=load_table_data.table, where={"_id": {"$eq": 50}}, hint={"_id": 1})

    assert one_df.count() == 1

    empty_df = mongo.read_table(table=load_table_data.table, where={"_id": {"$gt": 1000}}, hint={"_id": 1})

    assert not empty_df.count()

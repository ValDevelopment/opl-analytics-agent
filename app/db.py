import os

import mysql.connector
from dotenv import load_dotenv

import sqlglot
from sqlglot import exp


load_dotenv()


def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
    )


def get_schema():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_KEY
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = %s
        ORDER BY TABLE_NAME, ORDINAL_POSITION;
    """, (os.getenv("DB_NAME"),))

    columns = cursor.fetchall()

    cursor.close()
    connection.close()

    schema = {}

    for column in columns:
        table_name = column["TABLE_NAME"]

        if table_name not in schema:
            schema[table_name] = []

        schema[table_name].append({
            "name": column["COLUMN_NAME"],
            "type": column["DATA_TYPE"],
            "nullable": column["IS_NULLABLE"] == "YES",
            "key": column["COLUMN_KEY"],
        })

    return schema


def get_foreign_keys():
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            TABLE_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
        WHERE TABLE_SCHEMA = %s
          AND REFERENCED_TABLE_NAME IS NOT NULL;
    """, (os.getenv("DB_NAME"),))

    foreign_keys = cursor.fetchall()

    cursor.close()
    connection.close()

    return foreign_keys


def execute_query(sql):
    sql = sql.strip()

    validate_query(sql)

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        return results

    finally:
        cursor.close()
        connection.close()


def validate_query(sql):
    try:
        statements = sqlglot.parse(sql, read="mysql")
    except sqlglot.errors.ParseError as e:
        raise ValueError(f"Invalid SQL: {e}")

    if len(statements) != 1:
        raise ValueError("Only one SQL statement is allowed.")

    statement = statements[0]

    if not isinstance(statement, exp.Query):
        raise ValueError("Only read-only queries are allowed.")

    forbidden = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
    )

    for expression_type in forbidden:
        if statement.find(expression_type):
            raise ValueError("Query contains a prohibited operation.")

    return True
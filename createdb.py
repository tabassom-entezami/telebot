import csv
import os
import sqlite3

#############
# database  #
#############

columns_product = ["id", "product_name", "product_name_fa", "part_number", "brand", "price_usd",
                   "is_available", "region", "product_type", "car_model", "car_brand", "inventory", "lR"]
columns_answer = ["id", "sender", "from_group", "user_message", "answer", "datetime", "lR"]


def check_existence(db):
    conn_check = sqlite3.connect(db)
    cursor_check = conn_check.cursor()
    cursor_check.execute("PRAGMA table_info(products)")
    columns_exists = cursor_check.fetchall()

    return conn_check, cursor_check, columns_exists


# database connection
def create_or_connect_product_db(filename='products.db', expected_columns=[]):
    if os.path.isfile(filename):

        # check existence of db
        conn_check, cursor_check, columns_exists = check_existence(filename)

        existing_columns = [col[1] for col in columns_exists]
        if existing_columns != expected_columns:
            cursor_check.execute(
                '''CREATE TABLE IF NOT EXISTS products_new
                                              (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                               product_name TEXT,
                                               product_name_fa TEXT,
                                               part_number TEXT,
                                               brand TEXT,
                                               region TEXT,
                                               product_type TEXT,
                                               car_brand TEXT,
                                               car_model TEXT,
                                               price_usd BIGINT,
                                               inventory BIGINT,
                                               is_available BOOLEAN,
                                               lR TEXT)'''
            )
            cursor_check.execute("DROP TABLE IF EXISTS products")
            cursor_check.execute("ALTER TABLE products_new RENAME TO products")
        print(f"Connected to existing database: {filename}")
    else:
        conn_check = sqlite3.connect(filename)
        cursor_check = conn_check.cursor()
        cursor_check.execute(
            '''CREATE TABLE IF NOT EXISTS products
                                      (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                       product_name TEXT,
                                       product_name_fa TEXT,
                                       part_number TEXT,
                                       brand TEXT,
                                       region TEXT,
                                       product_type TEXT,
                                       car_brand TEXT,
                                       car_model TEXT,
                                       price_usd BIGINT,
                                       inventory BIGINT,
                                       is_available BOOLEAN,
                                       lR TEXT)''')
        conn_check.commit()
        print(f"Created new database: {filename}")
    return conn_check


def create_or_connect_answer_db(filename='answerlog.db', expected_columns=[]):
    conn_check, cursor_check, columns_exists = check_existence(filename)

    existing_columns = [col[1] for col in columns_exists]
    if existing_columns != expected_columns:
        cursor_check.execute(
            '''CREATE TABLE IF NOT EXISTS log_new
                                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                           sender TEXT,
                                           from_group TEXT,
                                           user_message TEXT,
                                           answer TEXT,
                                           datetime TIMESTAMP)'''
        )
        cursor_check.execute("DROP TABLE IF EXISTS answerlog")
        cursor_check.execute("ALTER TABLE log_new RENAME TO answerlog")
        print(f"Connected to existing database: {filename}")

    else:
        conn_check = sqlite3.connect(filename)
        cursor_check = conn_check.cursor()
        cursor_check.execute(
            '''CREATE TABLE IF NOT EXISTS log_new
                                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                           sender TEXT,
                                           from_group TEXT,
                                           user_message TEXT,
                                           answer TEXT,
                                           datetime TIMESTAMP,
                                           lR TEXT)''')
        conn_check.commit()
        print(f"Created new database: {filename}")
    return conn_check


PRODUCT_CONN = create_or_connect_product_db('product.db', columns_product)
LOG_CONN = create_or_connect_answer_db('answerlog.db', columns_answer)

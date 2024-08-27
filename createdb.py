import csv
import os
import sqlite3

#############
# database  #
#############

columns_product = {"id", "product_name", "product_name_fa", "part_number", "brand", "price_usd",
                   "is_available", "region", "product_type", "car_model", "car_brand", "inventory", "LR"}
columns_answer = {"id", "sender", "from_group", "part_number", "user_message", "answer", "datetime", "LR"}


def check_existence(db, table):
    conn_check = sqlite3.connect(db)
    cursor_check = conn_check.cursor()
    res = cursor_check.execute(f"PRAGMA table_info({table})")
    columns_exists = res.fetchall()

    return conn_check, cursor_check, columns_exists


# database connection
def create_or_connect_product_db(filename='db.sqlite3', expected_columns=[]):
    if os.path.isfile(filename):

        # check existence of db
        conn_check, cursor_check, columns_exists = check_existence(filename, 'products')
        existing_columns = {col[1] for col in columns_exists}
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
				               LR BOOLEAN)'''
            )
            cursor_check.execute("DROP TABLE IF EXISTS products")
            cursor_check.execute("ALTER TABLE products_new RENAME TO products")
        print(f"Connected to existing database: {filename} to create product")
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
                                       LR BOOLEAN)''')
        conn_check.commit()
        print(f"Created new database: {filename} to connect product")
    return conn_check


def create_or_connect_answer_db(filename='db.sqlite3', expected_columns=[]):
    conn_check, cursor_check, columns_exists = check_existence(filename, 'answerlog')

    existing_columns = {col[1] for col in columns_exists}
    if existing_columns != expected_columns:
        cursor_check.execute(
            '''CREATE TABLE IF NOT EXISTS answerlog_new
                                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                           sender TEXT,
                                           from_group TEXT,
                                           part_number TEXT,
                                           user_message TEXT,
                                           answer TEXT,
                                           datetime TIMESTAMP,
                                           LR BOOLEAN)'''
        )
        cursor_check.execute("DROP TABLE IF EXISTS answerlog")
        cursor_check.execute("ALTER TABLE answerlog_new RENAME TO answerlog")
        print(f"Connected to existing database: {filename} to create answer log")

    else:
        conn_check = sqlite3.connect(filename)
        cursor_check = conn_check.cursor()
        cursor_check.execute(
            '''CREATE TABLE IF NOT EXISTS log_new
                                          (id INTEGER PRIMARY KEY AUTOINCREMENT,
                                           sender TEXT,
                                           from_group TEXT,
                                           part_number TEXT,
                                           user_message TEXT,
                                           answer TEXT,
                                           datetime TIMESTAMP,
				           LR BOOLEAN)''')
        conn_check.commit()
        print(f"Created new database: {filename} to connect answerlog")
    return conn_check


PRODUCT_CONN = create_or_connect_product_db('db.sqlite3', columns_product)
LOG_CONN = create_or_connect_answer_db('db.sqlite3', columns_answer)

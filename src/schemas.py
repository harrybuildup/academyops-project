import sqlite3
from database import create_connection

def create_table(conn):
    """ create a table from the create_table_sql statement
    :param conn: Connection object
    :return:
    """
    try:
        sql_create_table = """ CREATE TABLE IF NOT EXISTS leads (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    name TEXT NOT NULL,
                                    phone TEXT NOT NULL UNIQUE,
                                    source TEXT,
                                    stage TEXT NOT NULL,
                                    notes TEXT,
                                    created_at TEXT NOT NULL,
                                    updated_at TEXT NOT NULL
                                ); """
        c = conn.cursor()
        c.execute(sql_create_table)
        print("Table 'leads' created successfully.")
    except sqlite3.Error as e:
        print(e)


def initialize_database(db_file):
    """ create a database connection and initialize the leads table
    :param db_file: database file
    :return: Connection object
    """
    conn = create_connection(db_file)
    if conn is not None:
        create_table(conn)
    else:
        print("Error! cannot create the database connection.")
    return conn


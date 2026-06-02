import sqlite3

def create_connection(db_file):
    """ create a database connection to the SQLite database specified by db_file
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(f"Connected to database: {db_file}")
    except sqlite3.Error as e:
        print(e)

    return conn



def close_connection(conn):
    """ close the database connection
    :param conn: Connection object
    """
    if conn:
        conn.close()
        print("Database connection closed.")


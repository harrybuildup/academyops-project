from src.database.connections import create_connection, close_connection
from src.database.schemas import create_table

def initialize_database(db_file):
    conn = create_connection(db_file)
    if conn is not None:
        create_table(conn)
        close_connection(conn)
    else:
        print("Error! Cannot create the database connection.")

if __name__ == "__main__":
    initialize_database("data/academyops.db")

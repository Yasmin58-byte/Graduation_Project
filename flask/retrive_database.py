import pyodbc

def create_database(server, database_name):
    # Append "_CLEANED" to the database name
    cleaned_database_name = database_name + "_CLEANED"

    # Connection string for the server
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};Trusted_Connection=yes'

    # Establish connection to the server
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    try:
        # Rollback any open transactions
        conn.rollback()

        # Create destination database if it does not exist
        cursor.execute(f'IF DB_ID(\'{cleaned_database_name}\') IS NULL CREATE DATABASE {cleaned_database_name}')

        # Commit the transaction
        conn.commit()

    finally:
        # Close connections
        cursor.close()
        conn.close()

def transfer_data(source_server, source_database, dest_server, dest_database):
    # Create destination database
    create_database(dest_server, source_database)  # Pass source_database for creating the cleaned database name

    # Connection string for the source database
    source_conn_str = f'DRIVER={{SQL Server}};SERVER={source_server};DATABASE={source_database};Trusted_Connection=yes'

    # Connection string for the destination database
    dest_conn_str = f'DRIVER={{SQL Server}};SERVER={dest_server};DATABASE={source_database}_CLEANED;Trusted_Connection=yes'  # Adjust the destination database name

    # Establish connection to the source and destination databases
    source_conn = pyodbc.connect(source_conn_str)
    dest_conn = pyodbc.connect(dest_conn_str)

    try:
        # Get a list of tables in the source database
        source_cursor = source_conn.cursor()
        source_cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' AND TABLE_SCHEMA='dbo'")
        tables = [table[0] for table in source_cursor.fetchall()]

        # Transfer data for each table
        for table in tables:
            # Get table schema from the source database
            source_schema_query = f"SELECT TOP 0 * FROM {table}"
            source_cursor.execute(source_schema_query)
            source_schema = [col_desc[0] for col_desc in source_cursor.description]

            # Create table in the destination database if it doesn't exist
            dest_cursor = dest_conn.cursor()
            dest_cursor.execute(f"IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = '{table}' AND type = 'U') BEGIN CREATE TABLE {table} ({', '.join([f'{col} VARCHAR(MAX)' for col in source_schema])}) END")

            # Insert data into the destination table
            dest_cursor.execute(f'INSERT INTO {table} SELECT * FROM {source_database}.dbo.{table}')

        # Commit changes to the destination database
        dest_conn.commit()

    finally:
        # Close connections
        source_conn.close()
        dest_conn.close()


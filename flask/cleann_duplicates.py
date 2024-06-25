import pyodbc

def remove_duplicates_sql_server(server, database):
    # Connect to the SQL Server database using integrated security
    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    # Get a list of all tables in the database
    tables_query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE';"
    cursor.execute(tables_query)
    tables = [row.TABLE_NAME for row in cursor.fetchall()]

    # Iterate through each table and remove duplicates based on all columns
    for table in tables:
        cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table}';")
        columns = [row.COLUMN_NAME for row in cursor.fetchall()]

        # Generate a dynamic SQL query to remove duplicates based on all columns
        columns_str = ', '.join(columns)
        remove_duplicates_query = f'''
            WITH CTE AS (
                SELECT *,
                       ROW_NUMBER() OVER (PARTITION BY {columns_str} ORDER BY (SELECT 1)) as RowNumber
                FROM {table}
            )
            DELETE FROM CTE WHERE RowNumber > 1;
        '''
        cursor.execute(remove_duplicates_query)
        conn.commit()

    # Close the connection
    conn.close()


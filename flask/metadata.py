import pyodbc

def fetch_and_store_metadata(db_connection_str, metadatabase_connection_str):
    db_connection = None
    metadatabase_connection = None

    try:
        db_connection = pyodbc.connect(db_connection_str)
        db_cursor = db_connection.cursor()

        db_cursor.execute("SELECT DB_NAME() AS DatabaseName")
        database_name = db_cursor.fetchone().DatabaseName

        db_cursor.execute("""
            SELECT 
                STUFF((
                    SELECT ',' + COLUMN_NAME
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA + '.' + TABLE_NAME = t.TABLE_SCHEMA + '.' + t.TABLE_NAME
                    FOR XML PATH('')), 1, 1, '') AS ColumnsNames,
                STUFF((
                    SELECT ',' + CAST(COUNT(*) AS NVARCHAR(50))
                    FROM INFORMATION_SCHEMA.COLUMNS
                    WHERE TABLE_SCHEMA + '.' + TABLE_NAME = t.TABLE_SCHEMA + '.' + t.TABLE_NAME
                    GROUP BY TABLE_NAME
                    FOR XML PATH('')), 1, 1, '') AS ColumnsCount,
                STUFF((
                    SELECT ',' + CAST(SUM(rows) AS NVARCHAR(50))
                    FROM (
                        SELECT p.rows
                        FROM sys.objects o
                        JOIN sys.partitions p ON o.object_id = p.object_id
                        WHERE o.type = 'U' AND o.name = t.TABLE_NAME
                    ) rows
                    FOR XML PATH('')), 1, 1, '') AS RowsCount,
                t.TABLE_NAME
            FROM INFORMATION_SCHEMA.COLUMNS t
            GROUP BY t.TABLE_SCHEMA, t.TABLE_NAME
        """)

        results = db_cursor.fetchall()

        metadatabase_connection = pyodbc.connect(metadatabase_connection_str)
        metadatabase_cursor = metadatabase_connection.cursor()

        columns_names_combined = ', '.join([row.ColumnsNames for row in results])
        columns_count_combined = ', '.join([f"{row.TABLE_NAME}:{row.ColumnsCount}" for row in results])
        rows_count_combined = ', '.join([f"{row.TABLE_NAME}:{row.RowsCount}" for row in results])

        metadatabase_cursor.execute("""
            INSERT INTO METADATA (DatabaseName, ColumnsNames, NumberOfColumns, NumberOfRows)
            VALUES (?, ?, ?, ?)
        """, (database_name, columns_names_combined, columns_count_combined, rows_count_combined))

        metadatabase_connection.commit()
        print("Metadata stored successfully!")
        return True
 
    except pyodbc.Error as e:
        print(f"Error connecting to the database: {str(e)}")

    finally:
        if db_connection:
            db_connection.close()
        if metadatabase_connection:
            metadatabase_connection.close()
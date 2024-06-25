import pyodbc
import pandas as pd

def handle_nulls_in_database(server, database, replacement_method, delete_nulls=False):
    connection_string = f'DRIVER=ODBC Driver 17 for SQL Server;SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    try:
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Query to get all table names in the database
        tables_query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
        tables_df = pd.read_sql(tables_query, conn)

        for index, row in tables_df.iterrows():
            table_name = row['TABLE_NAME']
            print(f"Processing table: {table_name}")

            # Query to get all column names, data types, and identity information in the current table
            columns_query = f"""
                SELECT COLUMN_NAME, DATA_TYPE, COLUMNPROPERTY(OBJECT_ID(TABLE_NAME), COLUMN_NAME, 'IsIdentity') AS IS_IDENTITY
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = '{table_name}'
            """
            columns_df = pd.read_sql(columns_query, conn)

            # Filter out identity columns
            columns_df = columns_df[(~columns_df['COLUMN_NAME'].str.lower().isin(['id'])) & (columns_df['IS_IDENTITY'] != 1)]

            # Generate SQL UPDATE or DELETE query for each column in the table
            update_queries = []
            for _, col_row in columns_df.iterrows():
                column_name = col_row['COLUMN_NAME']
                data_type = col_row['DATA_TYPE']

                # Determine replacement method based on data type
                if data_type.startswith('varchar') or data_type.startswith('char') or data_type.startswith('nvarchar'):
                    replace_method = 'mode'
                else:
                    replace_method = replacement_method

                # Generate the appropriate SQL update or delete query
                if delete_nulls:
                    delete_query = f"""
                        DELETE FROM {table_name}
                        WHERE {column_name} IS NULL;
                    """
                    update_queries.append(delete_query)
                else:
                    if replace_method == 'mean':
                        update_query = f"""
                            UPDATE {table_name}
                            SET {column_name} = COALESCE({column_name}, (
                                SELECT AVG(CAST({column_name} AS FLOAT))
                                FROM {table_name}
                                WHERE {column_name} IS NOT NULL
                            ));
                        """
                    elif replace_method == 'mode':
                        update_query = f"""
                            UPDATE {table_name}
                            SET {column_name} = COALESCE({column_name}, (
                                SELECT TOP 1 {column_name}
                                FROM {table_name}
                                WHERE {column_name} IS NOT NULL
                                GROUP BY {column_name}
                                ORDER BY COUNT(*) DESC
                            ));
                        """
                    elif replace_method == 'backward_fill':
                        update_query = f"""
                            WITH BackwardFilled AS (
                                SELECT *,
                                    LAG({column_name}) OVER (ORDER BY (SELECT NULL)) AS filled_value
                                FROM {table_name}
                            )
                            UPDATE BackwardFilled
                            SET {column_name} = filled_value
                            WHERE {column_name} IS NULL;
                        """
                    elif replace_method == 'forward_fill':
                        update_query = f"""
                            WITH ForwardFilled AS (
                                SELECT *,
                                    LEAD({column_name}) OVER (ORDER BY (SELECT NULL)) AS filled_value
                                FROM {table_name}
                            )
                            UPDATE ForwardFilled
                            SET {column_name} = filled_value
                            WHERE {column_name} IS NULL;
                        """
                    update_queries.append(update_query)


            # Execute update or delete queries
            for query in update_queries:
                cursor.execute(query)
            conn.commit()
            print(f"Null values handled successfully for table: {table_name}")

        print("Null value handling completed successfully for all tables.")

    except pyodbc.Error as e:
        print(f"Error connecting to the database: {e}")



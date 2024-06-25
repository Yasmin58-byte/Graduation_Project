import pyodbc
import decimal

def handle_outliers_in_database(server, database, replacement_method_outliers, remove_outliers=False, z_threshold=3):
    try:
        # Establish connection
        connection_string = f'DRIVER=ODBC Driver 17 for SQL Server;SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        conn = pyodbc.connect(connection_string)
        cursor = conn.cursor()

        # Get all numerical columns
        numerical_columns_query = """
            SELECT t.name AS table_name, c.name AS column_name, c.is_identity
            FROM sys.tables t
            INNER JOIN sys.columns c ON t.object_id = c.object_id
            INNER JOIN sys.types ty ON c.user_type_id = ty.user_type_id
            WHERE ty.name IN ('int', 'bigint', 'smallint', 'tinyint', 'float', 'real', 'decimal', 'numeric')
        """
        cursor.execute(numerical_columns_query)
        columns = cursor.fetchall()

        for table, column, is_identity in columns:
            print(f"Processing table: {table}, column: {column}")

            # Skip handling identity columns or columns likely to be identifiers
            if is_identity or 'id' in column.lower() or column.lower().endswith('_id') or 'id_' in column.lower():
                print(f"Skipping column '{column}' in table '{table}'")
                continue

            # Calculate mean and standard deviation
            stats_query = f"""
                SELECT AVG([{column}]), STDEV([{column}])
                FROM {table}
            """
            cursor.execute(stats_query)
            mean, std_dev = cursor.fetchone()

            if mean is not None and std_dev is not None:
                # Convert mean and std_dev to decimal.Decimal for precise arithmetic
                mean = decimal.Decimal(mean)
                std_dev = decimal.Decimal(std_dev)

                # Identify outliers using Z-score
                lower_bound = mean - z_threshold * std_dev
                upper_bound = mean + z_threshold * std_dev

                outliers_query = f"""
                    SELECT [{column}]
                    FROM {table}
                    WHERE [{column}] < {lower_bound} OR [{column}] > {upper_bound}
                """
                cursor.execute(outliers_query)
                outliers = cursor.fetchall()

                if outliers:
                    if remove_outliers:
                        # Remove outliers
                        delete_query = f"""
                            DELETE FROM {table}
                            WHERE [{column}] < {lower_bound} OR [{column}] > {upper_bound}
                        """
                        cursor.execute(delete_query)
                        conn.commit()
                        print(f"Outliers removed successfully for table: {table}, column: {column}")

                    else:
                        if replacement_method_outliers == 'median':
                            # Calculate median using NTILE
                            median_query = f"""
                                SELECT AVG([{column}]) AS median
                                FROM (
                                    SELECT [{column}], NTILE(2) OVER (ORDER BY [{column}]) AS tile
                                    FROM {table}
                                ) AS tiles
                                WHERE tile = 2
                            """
                            cursor.execute(median_query)
                            median = cursor.fetchone().median

                            # Replace outliers with median
                            replace_query = f"""
                                UPDATE {table}
                                SET [{column}] = {median}
                                WHERE [{column}] < {lower_bound} OR [{column}] > {upper_bound}
                            """
                        elif replacement_method_outliers == 'mean':
                            # Replace outliers with mean
                            replace_query = f"""
                                UPDATE {table}
                                SET [{column}] = {mean}
                                WHERE [{column}] < {lower_bound} OR [{column}] > {upper_bound}
                            """

                        cursor.execute(replace_query)
                        conn.commit()
                        print(f"Outliers handled successfully for table: {table}, column: {column}")

                else:
                    print(f"No outliers found in table: {table}, column: {column}")

            else:
                print(f"No statistics found for table: {table}, column: {column}")

        print("Outlier handling completed successfully.")

    except pyodbc.Error as e:
        print(f"Error connecting to the database: {e}")
 
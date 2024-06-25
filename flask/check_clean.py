import pyodbc
import numpy as np

def check_data_cleanliness(server, database):
    # Establish connection to the SQL Server database (using Windows authentication)
    conn_str = f'DRIVER=ODBC Driver 17 for SQL Server;SERVER={server};DATABASE={database};Trusted_Connection=yes;'
    conn = pyodbc.connect(conn_str)
    
    # Retrieve a list of all tables in the database
    cursor = conn.cursor()
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'")
    tables = [table[0] for table in cursor.fetchall()]
    
    # Initialize a flag to track data cleanliness
    is_data_clean = True
    
    # Check each table for null values, duplicate rows, and outliers
    for table in tables:
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        column_names = [column[0] for column in cursor.description]
        
        # Check for null values in each row
        for row in rows:
            null_columns = [column_names[i] for i, value in enumerate(row) if value is None]
            if null_columns:
                is_data_clean = False
        
        # Check for duplicate rows
        seen = set()
        duplicates = []
        for row in rows:
            row_values = tuple(row)
            if row_values in seen:
                duplicates.append(row_values)
            else:
                seen.add(row_values)
        
           # Check for outliers in numerical columns using IQR method
        for column in column_names:
            if not is_id_column(column):  # Skip checking outliers for ID columns
                cursor.execute(f"SELECT {column} FROM {table} WHERE {column} IS NOT NULL")
                values = [row[0] for row in cursor.fetchall() if row[0] is not None]
                if values and isinstance(values[0], (int, float)):
                    q1 = np.percentile(values, 25)
                    q3 = np.percentile(values, 75)
                    iqr = q3 - q1
                    lower_bound = q1 - 1.5 * iqr
                    upper_bound = q3 + 1.5 * iqr
                    outliers = [value for value in values if value < lower_bound or value > upper_bound]
                    if outliers:
                        print(f'Table "{table}", column "{column}" has {len(outliers)} outliers.')
                        is_data_clean = False
    
    # Close connection
    conn.close()
    
    # Return the result based on data cleanliness
    return is_data_clean

def is_id_column(column):
    # Logic to determine if the column is an ID column based on typical naming conventions
    if 'id' in column.lower() or column.lower().endswith('_id') or 'id_' in column.lower():
        return True
    else:
        return False
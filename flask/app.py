from flask import Flask, render_template, request, flash, redirect, url_for,jsonify,session,send_from_directory,send_file
import pyodbc 
import pandas as pd
import os
import shutil
import zipfile
import tempfile


# Create a Flask application instance named app.
app = Flask(__name__)
# Generate a random 24-byte secret key for session security
app.secret_key = os.urandom(24)  

# Database connection configuration for SQL Server
server = 'DESKTOP-TTF2QDM\SQLEXPRESS'
database = 'GENERATE_REPORTS'

# Create a connection string
connection = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;')

# Create a cursor
cursor = connection.cursor()

# Commit the changes
connection.commit()


@app.route('/')
def index():
    return render_template('home.html')


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
      cursor = connection.cursor()
      # Get user input from the signup form
      username = request.form['username']
      password = request.form['password']
      confirm_password=request.form['confirm_password']
      email = request.form['email']
      session['username'] = username

     #check if password match
      if password != confirm_password:
            flash('password and confirm password do not match', 'danger')
    #check len password
      if len(password) < 8:
            flash('Password must be at least 8 characters long', 'danger')
            cursor.close()
            return render_template('register.html')

      # Check if the email already exists in the database
      cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
      existing_user = cursor.fetchone()

      if existing_user:
            flash('Email address already exists', 'danger')
            cursor.close()
            return render_template('register.html')
      
       # Check if name already exists in the database
      cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
      existing_username = cursor.fetchone()

      if existing_username:
            flash('username address already exists', 'danger')
            cursor.close()
            return render_template('register.html')

     #Insert the new user into the database
      try:
         cursor.execute("INSERT INTO users (username, password, email) VALUES (?, ?, ?)",(username, password, email))     
         connection.commit()
         cursor.close()
         

        # Redirect to the signin page after successful registration
         return render_template('home2.html',username=username)
      except Exception as e:
       # Handle database errors 
        print(f"Error: {e}")
        connection.rollback()
        return f'Error occurred while signing up: {e}. Please try again.'
    # Render the registration form for GET requests
    return render_template('register.html')



@app.route('/sigin', methods=['GET', 'POST'])
def login():
       if request.method == 'POST':
        # Get user input from the login form
        email = request.form['email']
        password =request.form['password']
        try:
            # Check user credentials in the database
            cursor = connection.cursor()
            cursor.execute("SELECT username FROM users WHERE email = ? AND password = ?", (email, password))
            user = cursor.fetchone()
            cursor.close()
            if user:   
              username = user[0]
              # Redirect to the success page after successful login   
              return redirect(url_for('projects', username=username))
                
            else:
                # Provide an error message for invalid credentials
                 flash('Invalid email or password. Please try again.','danger')
                 return render_template('sigin.html')
 
        except Exception as e:
            # Handle database errors
            print(f"Error: {e}")
            return f'Error occurred while logging in: {e}. Please try again.'
       # Render the login form for GET requests
       return render_template('sigin.html')

from datetime import datetime, timedelta
from flask_mail import Mail, Message
import secrets

# Configuration for Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USE_SSL'] = True
app.config['MAIL_USERNAME'] = 'graduation.project70@gmail.com'
app.config['MAIL_PASSWORD'] = 'dvhi tseg wons oedh'
app.config['MAIL_DEFAULT_SENDER'] = 'graduation.project70@gmail.com'  

mail = Mail(app)


@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password_request():
    if request.method == 'POST':
        email = request.form['email']

        # Check if the email exists in the  database
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            # Generate a unique token and set its expiration time
            reset_token = secrets.token_urlsafe(32)
            reset_token_expiration = datetime.now() + timedelta(hours=1)

            # Update the user's record in the database with the reset token and expiration time
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET reset_token = ?, reset_token_expiration = ? WHERE email = ?",
                            (reset_token, reset_token_expiration, email))
            connection.commit()
            cursor.close()

            # Send an email to the user with the reset link
            reset_link = f"http://localhost:5000/reset_password/{reset_token}"
            message_body = f"Click the following link to reset your password: {reset_link}"

            msg = Message('Password Reset Request', recipients=[email])
            msg.body = message_body

            mail.send(msg)

            flash('Password reset link sent to your email. Please check your inbox.', 'success')
            return render_template('reset_password_request.html')

        else:
            flash('Email address not found. Please check and try again.', 'danger')

    return render_template('reset_password_request.html')


@app.route('/reset_password/<reset_token>', methods=['GET', 'POST'])
def reset_password(reset_token):
    if request.method == 'POST':
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']


        # Implement the logic to verify the reset token and allow users to set a new password
        # This will involve checking if the token is valid and not expired, and updating the user's password in the database
        if new_password == confirm_password:
            cursor = connection.cursor()
            cursor.execute("SELECT * FROM users WHERE reset_token = ? AND reset_token_expiration > ?", 
                           (reset_token, datetime.now()))
            user = cursor.fetchone()

            if user:
                # Update the user's password in the database
                cursor.execute("UPDATE users SET password = ?, reset_token = NULL, reset_token_expiration = NULL WHERE reset_token = ?",
                                (new_password, reset_token))

                connection.commit()
                cursor.close()

                flash('Password reset successful. You can now sign in with your new password.', 'success')
                return render_template('sigin.html')
            else:
                flash('Invalid or expired reset token. Please try again.', 'danger')
        else:
            flash('Passwords do not match. Please try again.', 'danger')

    return render_template('reset_password.html')





@app.route('/home2/<username>', methods=['GET'])
def projects(username):
    try:

        cursor.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()

        if not user:
            return "User not found"
        
        user_id = user[0]
        session['user_id'] = user_id
        
        cursor.execute("SELECT project_id FROM projects WHERE user_id = ?", (user_id,))
        project=cursor.fetchone()
        if project:
            project_id = project[0]
            session['project_id'] = project_id
        else:
            project_id = None
            session['project_id'] = None


        count_query = """
            SELECT COUNT(*) 
            FROM projects 
            WHERE user_id = ?
        """
        cursor.execute(count_query, (user_id,))
        project_count = cursor.fetchone()[0] or 0

        report_query = """
            SELECT COUNT(*) 
            FROM Report 
            WHERE user_id = ?
        """
        cursor.execute(report_query, (user_id,))
        report_count = cursor.fetchone()[0] or 0

        query = """
            SELECT projects.project_name, projects.creation_date,Report.report_name,Report.report_domain
             FROM projects
             left JOIN Report
             ON projects.project_id = Report.project_id
             where projects.project_id=? ;

        """
        cursor.execute(query, (project_id,))
        project_data = cursor.fetchall()

        domain_queries = {
            "business_count": "SELECT COUNT(*) FROM Report WHERE user_id = ? AND report_domain = 'Business'",
            "health_count": "SELECT COUNT(*) FROM Report WHERE user_id = ? AND report_domain = 'Health'",
            "education_count": "SELECT COUNT(*) FROM Report WHERE user_id = ? AND report_domain = 'Education'",
            "sport_count": "SELECT COUNT(*) FROM Report WHERE user_id = ? AND report_domain = 'Sports'",
            "economic_count": "SELECT COUNT(*) FROM Report WHERE user_id = ? AND report_domain = 'Economics'",
        }

        domain_counts = {}
        for key, query in domain_queries.items():
            cursor.execute(query, (user_id,))
            count = cursor.fetchone()
            domain_counts[key] = count[0] if count else 0
            cursor.commit()

        return render_template(
            'home2.html',
            project_count=project_count,projects=project_data,
            username=username,report_count=report_count,
            business_count=domain_counts["business_count"],
            health_count=domain_counts["health_count"],
            education_count=domain_counts["education_count"],
            sport_count=domain_counts["sport_count"],
            economic_count=domain_counts["economic_count"]
        )
    except Exception as e:
        print(f"Error: {e}")
        return f'Error occurred while fetching projects: {e}. Please try again.'



@app.route('/create_project', methods=['POST'])
def create_project():
    try:
        user_id = session.get('user_id')
        
        # Get the count of existing projects for the user
        cursor.execute("SELECT COUNT(*) FROM projects WHERE user_id = ?", (user_id,))
        project_count = cursor.fetchone()[0]
        
        # Generate a project name based on the count
        project_name = f"Project {project_count + 1}"  # Example: Project 1, Project 2, ...
        
        # Insert a new project into the projects table
        insert_query = """
            INSERT INTO projects (user_id, project_name)
            VALUES (?, ?)
        """
        cursor.execute(insert_query, (user_id, project_name))

        
        connection.commit()
        return redirect(url_for('check_connection'))
    except Exception as e:
        print(f"Error: {e}")
        return f'Error occurred while creating project: {e}. Please try again.'



@app.route('/connection', methods=['POST','GET'])
def check_connection():
    if request.method == 'POST':
        server = request.form['serverName']
        database = request.form['dbName']
        connection_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes'

        try:
            conn = pyodbc.connect(connection_str)
            conn.close()
            connection.commit()
            session['server'] = server
            session['database'] = database
            return jsonify({'status': 'success'})
        except pyodbc.Error as e:
            return jsonify({'status': 'failure'})

    return render_template('upload.html')

@app.route('/check_cleanliness', methods=['GET'])
def check_cleanliness():
    from check_clean import check_data_cleanliness
    server = session.get('server')
    database = session.get('database')
    if server and database:
        is_data_clean = check_data_cleanliness(server, database)
        if is_data_clean:
            from retrive_database import transfer_data
            transfer_data(server, database, 'DESKTOP-TTF2QDM\\SQLEXPRESS', 'destination_database')
            return redirect("/Metadataa")  

        else:
            return render_template('choice.html')
    else:
        return 'Connection not established properly.'

@app.route('/clean_method', methods=['POST','GET'])
def clean_method():
     from cleann_duplicates import remove_duplicates_sql_server
     from clean_null import handle_nulls_in_database
     from handle_outliers import handle_outliers_in_database
     from retrive_database import transfer_data

     if request.method == 'POST':
       server = session.get('server')
       database = session.get('database')
       button_clicked = request.form['button']
       if button_clicked == 'manual':
         return render_template('data_processing.html')
       elif button_clicked == 'automatic':
            replacement_method_outliers='mean'
            replacement_method='mean'
            remove_duplicates_sql_server(server, database)
            handle_nulls_in_database(server, database, replacement_method, delete_nulls=False)
            handle_outliers_in_database(server, database, replacement_method_outliers, remove_outliers=False,threshold=3)
            transfer_data(server, database, 'DESKTOP-TTF2QDM\\SQLEXPRESS', 'destination_database')
            return redirect("/Metadataa")

     return render_template('choice.html')



@app.route('/clean', methods=['POST', 'GET'])
def clean():
    from clean_null import handle_nulls_in_database
    from cleann_duplicates import remove_duplicates_sql_server
    from handle_outliers import handle_outliers_in_database
    from retrive_database import transfer_data
    
    if request.method == 'POST':
        # Get server and database from session
        server = session.get('server')
        database = session.get('database')
        
        # Check if server and database information exists in session
        if not server or not database:
            return 'Server and/or database information missing.'
        
        # Get selected replacement method for nulls from form
        replacement_method_nulls = request.form.get('replacement_method')
        delete_nulls_option = False
        if replacement_method_nulls == 'delete_nulls':
            delete_nulls_option = True
            
        # Get selected replacement method for outliers from form
        replacement_method_outliers = request.form.get('replacement_method_outliers')
        remove_outliers_option = False
        if replacement_method_outliers == 'remove_outliers':
            remove_outliers_option = True
            
        try:
            # Call functions based on selected options
            handle_nulls_in_database(server, database, replacement_method_nulls, delete_nulls_option)
            remove_duplicates_sql_server(server, database)
            handle_outliers_in_database(server, database, replacement_method_outliers, remove_outliers_option, z_threshold=3)
            transfer_data(server, database, 'DESKTOP-TTF2QDM\\SQLEXPRESS', 'destination_database')
            return redirect("/Metadataa")  # Redirect to '/metadataa' upon successful cleaning
        
        except Exception as e:
            flash(f"An error occurred while cleaning data: {str(e)}", "danger")
    
    return render_template('data_processing.html')





@app.route('/Metadataa', methods=['GET'])
def metadata():
   
            server = session.get('server')
            database = session.get('database')
            # Connect to our SQL Server database
            metadatabase_connection_str = r'DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-TTF2QDM\SQLEXPRESS;DATABASE=GENERATE_REPORTS;Trusted_Connection=yes'

            # Connect to user's database
            db_connection_str = (
                f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;')

            # Import the function from metadata.py
            from metadata import fetch_and_store_metadata
             # Call the imported function
            success = fetch_and_store_metadata(db_connection_str, metadatabase_connection_str)
            if success:
              # check table that you  want to know complete or not
                table_name = 'METADATA'

        # Get the column names from the SQL Server table
                cursor = connection.cursor()
                cursor.execute(f"SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = '{table_name}'")
                columns = [row.COLUMN_NAME for row in cursor.fetchall()]

        # Construct the SQL query to check for NULL values in any column
                query = f"SELECT * FROM {table_name} WHERE {' OR '.join(['[' + column + '] IS NULL' if column != 'Domain' else '[' + column + '] IS NOT NULL' for column in columns])}"

                result = pd.read_sql(query, connection)
       # Check if any rows are returned
                if not result.empty:
                     return render_template('not_complete.html')
                else:
                     return render_template('domain.html')
            else:
                flash("Failed to fetch and store metadata. Please check your connection details and try again.","danger")
      
    
@app.route('/complete_meta', methods=['GET','POST'])
def complete_meta():
    if request.method == 'POST':
        try:
            cursor = connection.cursor()
            # Get user input from the  form
            DESCRIPTION = request.form['DESCRIPTION']
            KEYWORDS = request.form['KEYWORDS']
            DatabaseName = request.form['DatabaseName']  

            # Check if the provided DatabaseName exists in the database
            cursor.execute("SELECT COUNT(*) FROM METADATA WHERE DatabaseName= ?", (DatabaseName,))
            result = cursor.fetchone()
            
            if result[0] == 1:
                # Update data in the existing row with the provided DatabaseName
                cursor.execute("UPDATE METADATA SET DESCRIPTION = ?, KEYWORDS = ? WHERE DatabaseName = ?", (DESCRIPTION, KEYWORDS, DatabaseName))
                
                # Commit the transaction
                connection.commit()
                session['DatabaseName'] = DatabaseName
                print("DatabaseName stored in session:", session['DatabaseName'])  # Check if DatabaseName is stored

                # Redirect to a page indicating successful update
                return redirect(url_for('predict'))  # Redirect to predict route after updating
            else:
                # Close the cursor and connection
                cursor.close()
                connection.close()
                
                return "Error: The provided DatabaseName does not exist in the database."
        
        except Exception as e:
            # Handle exceptions
            print("An error occurred:", e)
            return "An error occurred while completing metadata."
    return render_template('not_complete.html')



@app.route('/predict', methods=['GET'])
def predict():
    try:
        from transformers import BertTokenizer, BertForSequenceClassification
        from sklearn.preprocessing import LabelEncoder
        import torch
        import joblib

        # Load the saved model and tokenizer
        model = BertForSequenceClassification.from_pretrained("bert_model")
        tokenizer = BertTokenizer.from_pretrained("bert_model")

        # Load label encoder
        label_encoder = LabelEncoder()
        # Load the saved LabelEncoder object
        label_encoder = joblib.load('label_encoder.pkl')

        

        # Fetch database name from session
        DatabaseName = session.get('DatabaseName')
        print("Retrieved DatabaseName from session:", DatabaseName)  # Debugging statement

        if not DatabaseName:
            return "Error: DatabaseName not found in session."

        # Connect to the database
        cursor = connection.cursor()

        # Specify the columns you want to retrieve
        columns_to_select = ['DESCRIPTION', 'KEYWORDS', 'ColumnsNames', 'DatabaseName']

        # Construct the SQL query to select specific columns
        columns_str = ', '.join(columns_to_select)
        query = f"SELECT {columns_str} FROM METADATA WHERE DatabaseName = ?"

        # Execute the query with parameter substitution to avoid SQL injection
        cursor.execute(query, (DatabaseName,))
        
        # Fetch the results into a DataFrame
        data = cursor.fetchall()
        
        if not data:
            return "Can't take input. No data available."

        # Initialize text variable
        text_data = ""

        # Iterate through each row in the fetched data
        for row in data:
            # Join the row values into a comma-separated string
            row_str = ", ".join(str(value) for value in row)
            # Concatenate the row string with a newline character
            text_data += row_str + "\n"

        if not text_data:
            return "No text data"

        # Tokenize input text
        inputs = tokenizer(text_data, padding=True, truncation=True, max_length=128, return_tensors="pt")
        print("Tokenized inputs:", inputs)

        # Forward pass through the model
        with torch.no_grad():
            outputs = model(**inputs)

        print("Model outputs:", outputs)

        # Get predicted labels
        predicted_label_ids = torch.argmax(outputs.logits, dim=1).cpu().numpy()
        print("Predicted label IDs:", predicted_label_ids)

        # Inverse transform predicted labels
        predicted_domains = label_encoder.inverse_transform(predicted_label_ids)

        # Convert predicted domains to list before storing in session
        predicted_domains_list = predicted_domains.tolist()

        # Update the database with predicted domains
        update_query = "UPDATE METADATA SET Domain = ? WHERE DatabaseName = ?"
        for domain in predicted_domains:
            cursor.execute(update_query, (domain, DatabaseName))
        
        # Commit the changes to the database
        connection.commit()

        # Store predicted domains in session
        session['predicted_domains'] = predicted_domains_list

        # Render template with predicted domains and inputs
        return render_template('domain.html', predicted_domains=predicted_domains_list)

    except Exception as e:
        # Return the specific error message
        return str(e)




@app.route('/download')
def download():
         predicted_domains = session.get('predicted_domains')
         predicted_domain = predicted_domains[0].capitalize()
         if predicted_domain =='Business':
             return render_template('Bussiness.html',predicted_domains=predicted_domain)
         elif predicted_domain =='Health':
             return render_template('Health.html',predicted_domains=predicted_domain)
         elif predicted_domain =='Education':
             return render_template('Education.html',predicted_domains=predicted_domain)
         elif predicted_domain =='Economics':
             return render_template('Economic.html',predicted_domains=predicted_domain)
         elif predicted_domain =='Sports':
             return render_template('Sport.html',predicted_domains=predicted_domain)
         

@app.route('/download_template', methods=['POST'])
def download_template():
   
    TEMPLATES_DIR = 'G:/GRADUATION_PROJECT/templets/'  
    template_name = request.form.get('template_name', '')

    if not template_name:
        return "Please select a template."

    template_path = os.path.join(TEMPLATES_DIR, template_name)

    if not os.path.exists(template_path):
        return "Template not found."
    
    report_name = request.form.get('report_name')
    report_description = request.form.get('report_description')
    predicted_domains = session.get('predicted_domains')
    predicted_domain = predicted_domains[0].capitalize()
    user_id=session.get('user_id')
    project_id=session.get('project_id')
    print(report_name,report_description,predicted_domain,user_id,project_id)
    cursor.execute("INSERT INTO Report (report_name, report_description, report_domain,user_id,project_id) VALUES (?, ?, ?,?,?)",(report_name, report_description, predicted_domain,user_id,project_id))   
    connection.commit()


    return send_from_directory(TEMPLATES_DIR, template_name, as_attachment=True)
   
   
   
def get_table_names(conn):
    query = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE = 'BASE TABLE'"
    cursor = conn.cursor()
    cursor.execute(query)
    tables = cursor.fetchall()
    return [table[0] for table in tables]


@app.route('/download_all', methods=['GET'])
def download_all_csv():
    server_name = 'DESKTOP-TTF2QDM\SQLEXPRESS'
    database_name = session.get('database') 
    database_name += "_CLEANED"

    conn = pyodbc.connect(f'DRIVER={{SQL Server}};SERVER={server_name};DATABASE={database_name};Trusted_Connection=yes;')

    table_names = get_table_names(conn)
    
    # Create a temporary directory to store CSV files
    temp_dir = tempfile.mkdtemp()
    for table in table_names:
        query = f"SELECT * FROM {table}"
        df = pd.read_sql(query, conn)
        # Prepare data with column names separated by '|'
        data_with_columns = ['|'.join(df.columns)] + [ '|'.join(map(str, row)) for row in df.values ]
        
        csv_path = os.path.join(temp_dir, f"{table}.csv")
        with open(csv_path, 'w') as f:
            f.write('\n'.join(data_with_columns))
    
    # Create a zip file containing all CSV files
    zip_filename = f"{database_name}_data.zip"  # Name for the zip file
    zip_path = os.path.join(tempfile.gettempdir(), zip_filename)
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        for root, _, files in os.walk(temp_dir):
            for file in files:
                zipf.write(os.path.join(root, file), arcname=file)

    # Clean up temporary directory
    shutil.rmtree(temp_dir)
    conn.close()
    return send_file(zip_path, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)








    


from flask import Flask, render_template, request, flash, redirect, url_for
import pyodbc 
import pandas as pd
import os

# Create a Flask application instance named app.
app = Flask(__name__)
# Generate a random 24-byte secret key for session security
app.secret_key = os.urandom(24)  

# Database connection configuration for SQL Server
server = 'DESKTOP-11VDQN8\SQLEXPRESS'
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

        # Check if the email exists in the Oracle database
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
        count_query = """
            SELECT COUNT(*) 
            FROM projects 
            JOIN users ON projects.user_id = users.user_id 
            WHERE users.username = ?
        """
        cursor.execute(count_query, (username,))
        project_count = cursor.fetchone()[0]
        # Fetch all projects from the database
        query = "SELECT project_name, description, creation_date FROM projects JOIN users ON projects.user_id = users.user_id WHERE users.username = ?"
        
        # Execute the query with the provided input_username
        cursor.execute(query, (username,))
        project_data = cursor.fetchall()

        # Print fetched data for debugging
        print("Fetched data:", repr(project_data).encode('unicode_escape').decode('utf-8'))

        # Pass the project data to the template
        return render_template('home2.html', project_count=project_count,projects=project_data,username=username)
    except Exception as e:
        # Handle database errors
        print(f"Error: {e}")
        return f'Error occurred while fetching projects: {e}. Please try again.'





@app.route('/Metadataa', methods=['GET', 'POST'])
def metadata():
    if request.method == 'POST':
            # Get user input from the form
            server = request.form['serverName']
            database = request.form['dbName']

            # Import the function from metadata.py
            from metadata import fetch_and_store_metadata

            # Connect to our SQL Server database
            metadatabase_connection_str = r'DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-11VDQN8\SQLEXPRESS;DATABASE=GENERATE_REPORTS;Trusted_Connection=yes'

            # Connect to user's database
            db_connection_str = (
                f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;')

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
                query = f"SELECT * FROM {table_name} WHERE {' OR '.join(['[' + column + '] IS NULL' for column in columns])}"
                result = pd.read_sql(query, connection)
       # Check if any rows are returned
                if not result.empty:
                     return render_template('not_complete.html')
                else:
                     return render_template('success.html')
            else:
                flash("Failed to fetch and store metadata. Please check your connection details and try again.","danger")
      
    # Handle GET requests if needed
    return render_template('database_details.html')



if __name__ == '__main__':
    app.run(debug=True)
 


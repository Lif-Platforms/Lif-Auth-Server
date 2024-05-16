import secrets
import yaml
import uuid
import mysql.connector
from mysql.connector.constants import ClientFlag

# Global database connection
conn = None

# Load config.yml
# Run by the main file after the config checks have been completed
def load_config():
    global configurations

    with open("config.yml", "r") as config:
        contents = config.read()
        configurations = yaml.safe_load(contents)

# Function to establish a database connection
def connect_to_database():
    # Handle connecting to the database
    def connect():
        global conn

        # Define configurations
        mysql_configs = {
            "host": configurations['mysql-host'],
            "port": configurations['mysql-port'],
            "user": configurations['mysql-user'],
            "password": configurations['mysql-password'],
            "database": configurations['mysql-database'], 
        }

        # Check if SSL is enabled
        if configurations['mysql-ssl']:
            # Add ssl configurations to connection
            mysql_configs['client_flags'] = [ClientFlag.SSL]
            mysql_configs['ssl_ca'] = configurations['mysql-cert-path']

        conn = mysql.connector.connect(**mysql_configs)
    
    # Check if there is a MySQL connection
    if conn is None:
        connect()
    else:
        # Check if existing connection is still alive
        if not conn.is_connected():
            connect()

# Class for auth related functions
class auth:
    # Function for verifying user credentials
    def verify_credentials(username, password):

        if password is None:
            return "BAD_CREDENTIALS"
        
        else:
            connect_to_database()
            cursor = conn.cursor()

            # Validate login credentials
            cursor.execute("SELECT * FROM accounts WHERE username = %s AND password = %s", (username, password,))
            account = cursor.fetchone()

            # Checks if the account was found
            if account:
                # Check if user is suspended
                cursor.execute("SELECT role FROM accounts WHERE username = %s", (username,))
                role = cursor.fetchone()

                if role[0] == "SUSPENDED":
                    return "ACCOUNT_SUSPENDED"
                
                else:
                    return "OK"
            else:
                return "BAD_CREDENTIALS"
            
    def check_token(username: str, token: str):
        connect_to_database()
        cursor = conn.cursor()

        # Gets all accounts from the MySQL database
        cursor.execute("SELECT * FROM accounts")
        items = cursor.fetchall()

        found_token = False

        for user in items:
            database_user = user[1]
            database_token = user[4]

            if database_user == username and database_token == token:
                found_token = True

        return found_token
    
    def check_username(username):
        connect_to_database()
        cursor = conn.cursor()

        # Gets all accounts from the MySQL database
        cursor.execute("SELECT * FROM accounts WHERE username = %s", (username,))
        item = cursor.fetchone()

        found_username = False

        # Set 'found_username' to 'True' if username was found
        if item:
            found_username = True

        cursor.close()

        # Returns the status
        return found_username
    
    def check_email(email):
        connect_to_database()
        cursor = conn.cursor()

        found_email = False

        # Get email from MySQL database
        cursor.execute("SELECT * FROM accounts WHERE email = %s", (email,))
        item = cursor.fetchone()

        # Set 'found_email' to 'True' if email was found
        if item:
            found_email = True

        cursor.close()

        # Returns the status
        return found_email
    
    def create_account(username, email, password, password_salt):
        connect_to_database()

        # Define database cursor
        cursor = conn.cursor()

        # Generate user token
        token = str(secrets.token_hex(16 // 2))

        # Generate user id
        user_id = str(uuid.uuid4()) 

        cursor.execute("INSERT INTO accounts (username, password, email, token, salt, bio, pronouns, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (username, password, email, token, password_salt, None, None, user_id))

        conn.commit()
        cursor.close()

    def check_user_exists(account: str, mode: str):
        connect_to_database()

        # Define database cursor
        cursor = conn.cursor()

        # Check mode
        if mode == "ACCOUNT_ID":
            cursor.execute("SELECT * FROM accounts WHERE user_id = %s", (account,))
            account = cursor.fetchone()

            # Check if user exists
            if account:
                return True
            else:
                return False
            
        elif mode == "USERNAME":
            cursor.execute("SELECT * FROM accounts WHERE username = %s", (id,))
            account = cursor.fetchone()

            # Check if user exists
            if account:
                return True
            else:
                return False
            
    def check_account_permission(account_id: str, node: str):
        connect_to_database()

        # Define database cursor
        cursor = conn.cursor()

        # Get permissions
        cursor.execute("SELECT * FROM permissions WHERE account_id = %s AND node = %s", (account_id, node,))
        perms = cursor.fetchall()

        # Check if user had required perm
        if perms:
            return True
        else:
            return False

            
# Class for info get related functions
class info:
    # Get user salt
    def get_password_salt(username):
        connect_to_database()
        cursor = conn.cursor()

        # Gets the salt for the given username from the MySQL database
        cursor.execute("SELECT salt FROM accounts WHERE username = %s", (username,))
        result = cursor.fetchone()

        if result is not None:
            return result[0]  # Return the salt value if found
        else:
            return False  # Return False if no matching username is found

    def retrieve_user_token(username):
        connect_to_database()
        cursor = conn.cursor()

        # Gets all accounts from the MySQL database
        cursor.execute("SELECT * FROM accounts")
        items = cursor.fetchall()

        found_token = False

        # Gets the token from the MySQL database
        for item in items:
            database_username = item[1]
            database_token = item[4]

            if username == database_username:
                found_token = database_token

        cursor.close()

        # Returns the token
        return found_token
    
    def get_bio(username):
        connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE username = %s", (username,))
        data = cursor.fetchone()

        if data:
            return data[6]
        else:
            return "INVALID_USER"
    
    def get_pronouns(username):
        connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE username = %s", (username,))
        data = cursor.fetchone()

        return data[7]
    
    def get_user_email(username: str):
        connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE username = %s", (username,))
        data = cursor.fetchone()

        return data[3]
    
    def get_bulk_emails(accounts: list, search_mode: str):
        connect_to_database()
        cursor = conn.cursor()

        # Check search mode
        if search_mode == "userID":
            search_column = "user_id"

        else:
            search_column = "username"

        # Prepare the SELECT query
        query = f"SELECT * FROM accounts WHERE {search_column} IN (%s)"
        placeholders = ', '.join(['%s'] * len(accounts))
        query = query % placeholders

        # Execute the query
        cursor.execute(query, accounts)

        # Fetch all rows
        rows = cursor.fetchall()

        return rows
    
    def get_username(account_id: str):
        connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE user_id = %s", (account_id,))
        data = cursor.fetchone()

        return data[1]
    
    def get_user_id(username: str):
        connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM accounts WHERE username = %s", (username,))
        data = cursor.fetchone()

        return data[0]

# Class for update related functions
class update:
    # Update user bio
    def update_user_bio(username, data):
        connect_to_database()
        cursor = conn.cursor()

        # Grab user info from database
        cursor.execute("UPDATE accounts SET bio = %s WHERE username = %s", (data, username))
        conn.commit()

        return "Ok"

    def update_user_pronouns(username, data):
        connect_to_database()
        cursor = conn.cursor()

        # Update pronouns in database
        cursor.execute("UPDATE accounts SET pronouns = %s WHERE username = %s", (data, username))
        conn.commit()

        return "Ok"

    def update_user_salt(username: str, salt: str):
        connect_to_database()
        cursor = conn.cursor()

        # Update salt in database
        cursor.execute("UPDATE accounts SET salt = %s WHERE username = %s", (salt, username))
        conn.commit()

    def update_password(username: str, password: str):
        connect_to_database()
        cursor = conn.cursor()

        # Update password in database
        cursor.execute("UPDATE accounts SET password = %s WHERE username = %s", (password, username))
        conn.commit()

    def set_role(account_id, role):
        connect_to_database()
        cursor = conn.cursor()

        # Set role of user
        cursor.execute("UPDATE accounts SET role = %s WHERE user_id = %s", (role, account_id,))
        conn.commit()

    def update_email(account_id: str, email: str):
        connect_to_database()
        cursor = conn.cursor()

        # Update user email
        cursor.execute("UPDATE accounts SET email = %s WHERE user_id = %s", (email, account_id,))
        conn.commit()

    def add_permission_node(account_id: str, node: str):
        connect_to_database()
        cursor = conn.cursor()

        # Add user permissions
        cursor.execute("INSERT INTO permissions (account_id, node) VALUES (%s, %s)", (account_id, node,))
        conn.commit()

    def remove_permission_node(account_id: str, node: str):
        connect_to_database()
        cursor = conn.cursor()

        # Remove user permissions
        cursor.execute("DELETE FROM permissions WHERE account_id = %s AND node = %s", (account_id, node,))
        conn.commit()

def get_username_from_email(email):
    connect_to_database()
    cursor = conn.cursor()

    # Get username from email
    cursor.execute("SELECT username FROM accounts WHERE email = %s", (email,))
    data = cursor.fetchone()

    return data[0]

import secrets
import yaml
import uuid
import mysql.connector
from mysql.connector.constants import ClientFlag

# Load config.yml
# Run by the main file after the config checks have been completed
def load_config():
    global configurations

    with open("config.yml", "r") as config:
        contents = config.read()
        configurations = yaml.safe_load(contents)

# Function to establish a database connection
def connect_to_database():
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

    return conn
    
# Class for auth related functions
class auth:
    """
    ## Authentication Class
    This class handles authentication for user accounts.
    """
    # Function for verifying user credentials
    def verify_credentials(username, password):
        """
        ## Verify Credentials
        Handles the verification of user login credentials.
        
        ### Parameters
        - username (str): Username of the account.
        - password (str): Password of the account.
        
        ### Returns
        STRING: Literal 'OK', 'BAD_CREDENTIALS', 'ACCOUNT_SUSPENDED'.
        """
        if password is None:
            return "BAD_CREDENTIALS"
        
        else:
            conn = connect_to_database()
            cursor = conn.cursor()

            # Validate login credentials
            cursor.execute("SELECT username, password, role FROM accounts WHERE username = %s AND password = %s", (username, password,))
            account = cursor.fetchone()
            conn.close()

            # Checks if the account was found
            if account:
                # Check if account is suspended
                if account[2] == "SUSPENDED":
                    return "ACCOUNT_SUSPENDED"   
                else:
                    return "OK"
            else:
                return "BAD_CREDENTIALS"
            
    def check_token(username: str, token: str):
        """
        ## Check Token
        Handles the verification of user tokens.
        
        ### Parameters
        - username (str): Username of the account.
        - token (str): Token of the account.
        
        ### Returns
        STRING: Literal 'Ok', 'INVALID_TOKEN', 'SUSPENDED'.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Get account from database
        cursor.execute("SELECT username, token, role FROM accounts WHERE username = %s AND token = %s", (username, token,))
        account = cursor.fetchone()
        conn.close()

        # Check token
        if account:
            # Check role
            if account[2] != "SUSPENDED":
                return "Ok"
            else:
                return "SUSPENDED"
        else:
            return "INVALID_TOKEN"

    
    def check_username(username):
        """
        ## Check Username
        Checks if a username exists.
        
        ### Parameters
        - username (str): Username to check.
       
        ### Returns
        BOOLEAN: True (Username Found), False (Username NOT Found).
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Gets all accounts from the MySQL database
        cursor.execute("SELECT * FROM accounts WHERE username = %s", (username,))
        item = cursor.fetchone()
        conn.close()

        # Check if username was found
        if item:
            return True
        else:
            return False
    
    def check_email(email):
        """
        ## Check Email
        Checks if an email exists.
        
        ### Parameters
        - email (str): Email to check.
        
        ### Returns
        BOOLEAN: True (Email Found), False, (Email NOT Found).
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Get email from MySQL database
        cursor.execute("SELECT * FROM accounts WHERE email = %s", (email,))
        item = cursor.fetchone()
        conn.close()

        # Check if email was found
        if item:
            return True
        else:
            return False
    
    def create_account(username, email, password, password_salt):
        """
        ## Create Acount
        Handles the creation of user accounts.
        
        ### Parameters
        - username (str): Username of the account.
        - email (str): Email of the account.
        - password (str): Password of the account.
        - password_salt (str): Salt for the password.
        
        ### Returns
        None
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Generate user token
        token = str(secrets.token_hex(16 // 2))

        # Generate user id
        user_id = str(uuid.uuid4()) 

        cursor.execute("INSERT INTO accounts (username, password, email, token, salt, bio, pronouns, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                    (username, password, email, token, password_salt, None, None, user_id))

        conn.commit()
        conn.close()

    def check_user_exists(account: str, mode: str):
        """
        ## Check User Exists
        Checks if an account already exists in the database.
        
        ### Parameters
        - account (str): Username or id of the account.
        - mode (str): Specify if the account parameter is an 'ACCOUNT_ID' or 'USERNAME'.
        
        ### Returns
        BOOLEAN: True (User Found), False (User NOT Found)'.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Check mode
        if mode == "ACCOUNT_ID":
            cursor.execute("SELECT * FROM accounts WHERE user_id = %s", (account,))
            account = cursor.fetchone()
            conn.close()

            # Check if user exists
            if account:
                return True
            else:
                return False
            
        elif mode == "USERNAME":
            cursor.execute("SELECT * FROM accounts WHERE username = %s", (id,))
            account = cursor.fetchone()
            conn.close()

            # Check if user exists
            if account:
                return True
            else:
                return False
            
    def check_account_permission(account_id: str, node: str):
        """
        ## Check Account Permission
        Checks the acount permissions for an account.
        
        ### Parameters
        - account_id (str): UserId of the account.
        - node (str): Permission node to check if user has.
        
        ### Returns
        BOOLEAN: True (User HAS Permission), False (User DOESN'T Have Permission).
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Get permissions
        cursor.execute("SELECT * FROM permissions WHERE account_id = %s AND node = %s", (account_id, node,))
        perms = cursor.fetchall()
        conn.close()

        # Check if user had required perm
        if perms:
            return True
        else:
            return False

            
# Class for info get related functions
class info:
    """
    ## Info Class
    Handles the retrieval of info for Lif Accounts.
    """
    # Get user salt
    def get_password_salt(username):
        """
        ## Get Password Salt
        Gets the salt for a password for an account.
        
        ### Parameters
        - username (str): Username of the account.
        
        ### Returns
        STRING: Password salt OR BOOLEAN: False (User Not Found).
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Gets the salt for the given username from the MySQL database
        cursor.execute("SELECT salt FROM accounts WHERE username = %s", (username,))
        result = cursor.fetchone()
        conn.close()

        if result is not None:
            return result[0]  # Return the salt value if found
        else:
            return False  # Return False if no matching username is found

    def retrieve_user_token(username):
        """
        ## Retrieve User Token
        Gets the token for an account.
        
        ### Parameters
        - username (str): Username of the account.
        
        ### Returns
        STRING: User token OR BOOLEAN: False (User Not Found).
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Get token from database
        cursor.execute("SELECT token FROM accounts WHERE username = %s", (username,))
        token = cursor.fetchone()

        # Check if token was found
        if token:
            return token[0]
        else:
            return False
    
    def get_bio(username):
        """
        ## Get Bio
        Gets the bio for a user account.
        
        ### Parameters
        - username (str): Username of the account.
        
        ### Returns
        STRING: User bio, Literal 'INVALID_USER'.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT bio FROM accounts WHERE username = %s", (username,))
        data = cursor.fetchone()
        conn.close()

        if data:
            return data[0]
        else:
            return "INVALID_USER"
    
    def get_pronouns(username):
        """
        ## Get Pronouns
        Gets the pronouns for a user account.
        
        ### Parameters
        - username (str): Username of the account.
        
        ### Returns
        STRING: User pronouns.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT pronouns FROM accounts WHERE username = %s", (username,))
        data = cursor.fetchone()
        conn.close()

        return data[0]
    
    def get_user_email(username: str):
        """
        ## Get User Email
        Gets the email for a user account.
        
        ### Parameters
        - username (str): Username of the account.
        
        ### Returns
        STRING: User email.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT email FROM accounts WHERE username = %s", (username,))
        data = cursor.fetchone()
        conn.close()

        return data[0]
    
    def get_bulk_emails(accounts: list, search_mode: str):
        """
        ## Get Bulk Emails
        Allows services to supply a list of accounts and get their emails.
        
        ### Parameters
        - accounts (list): List of accounts.
        - search_mode (str): Specify if the accounts parameter is a list of 'userID' or 'username'.
        
        ### Returns
        LIST: List of account emails.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Check search mode
        if search_mode == "userID":
            search_column = "user_id"
        else:
            search_column = "username"

        # Create placeholders for the list of values
        placeholders = ', '.join(['%s'] * len(accounts))

        # Generate the SQL query dynamically with parameter placeholders
        query = f"SELECT * FROM accounts WHERE {search_column} IN ({placeholders})"

        # Execute the query with the list of values
        cursor.execute(query, accounts)

        # Fetch the results
        found_accounts = cursor.fetchall()
        conn.close()

        return found_accounts

    def get_username(account_id: str):
        """
        ## Get Username
        Gets the username from  an account id.
        
        ### Parameters
        - account_id (str): The userId for the account.
        
        ### Returns
        STRING: Username.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT username FROM accounts WHERE user_id = %s", (account_id,))
        data = cursor.fetchone()
        conn.close()

        return data[0]
    
    def get_user_id(username: str):
        """
        ## Get User Id
        Gets the account id from the username.
        
        ### Parameters
        - username (str): Username of the account.
       
        ### Returns
        STRING: User Id.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM accounts WHERE username = %s", (username,))
        data = cursor.fetchone()
        conn.close()

        return data[0]
    
    def check_if_user_exists(user: str):
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM accounts WHERE username = %s", (user,))
        data = cursor.fetchone()

        if data:
            return True
        else:
            return False
        
    def get_role(username: str):
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT role FROM accounts WHERE username = %s", (username,))
        role = cursor.fetchone()

        return role[0]
    
    def get_account_id(username: str):
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT user_id FROM accounts WHERE username = %s", (username,))
        role = cursor.fetchone()

        return role[0]

# Class for update related functions
class update:
    """
    ## Update Class
    Handles updating information on Lif Accounts.
    """
    # Update user bio
    def update_user_bio(username, data):
        """
        ## Update User Bio
        Handles updating the user bio.
        
        ### Parameters
        - username (str): Username of the account.
        - data (str): The new bio.
        
        ### Returns
        STRING: Literal 'Ok'.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Grab user info from database
        cursor.execute("UPDATE accounts SET bio = %s WHERE username = %s", (data, username))
        conn.commit()
        conn.close()

        return "Ok"

    def update_user_pronouns(username, data):
        """
        ## Update User Pronouns
        Updates user pronouns for an account.
        
        ### Parameters
        - username (str): Username of the account.
        
        ### Returns
        STRING: Literal 'Ok'.
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Update pronouns in database
        cursor.execute("UPDATE accounts SET pronouns = %s WHERE username = %s", (data, username))
        conn.commit()
        conn.close()

        return "Ok"

    def update_user_salt(username: str, salt: str):
        """
        ## Update User Salt
        Updates the salt for the password of a user account.
        
        ### Parameters
        - username (str): Username of the account.
        - salt (str): New password salt.
        
        ### Returns
        None
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Update salt in database
        cursor.execute("UPDATE accounts SET salt = %s WHERE username = %s", (salt, username))
        conn.commit()
        conn.close()

    def update_password(username: str, password: str):
        """
        ## Update Password
        Updates the password of a user account.
        
        ### Parameters
        - username (str): Username of the account.
        - password (str): New password for the account.
        
        ### Returns
        None
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Update password in database
        cursor.execute("UPDATE accounts SET password = %s WHERE username = %s", (password, username))
        conn.commit()
        conn.close()

    def set_role(account_id, role):
        """
        ## Set Role
        Updates the role of a Lif Account.
        
        ### Parameters
        - account_id (str): UserId of the account.
        - role (str): Role that the account will be set to.
        
        ### Returns
        None
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Set role of user
        cursor.execute("UPDATE accounts SET role = %s WHERE user_id = %s", (role, account_id,))
        conn.commit()
        conn.close()

    def update_email(account_id: str, email: str):
        """
        ## Update Email
        Updates the email on a Lif Account.
        
        ### Parameters
        - account_id (str): UserId of the account.
        - email (str): New email the account.
        
        ### Returns
        None
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Update user email
        cursor.execute("UPDATE accounts SET email = %s WHERE user_id = %s", (email, account_id,))
        conn.commit()
        conn.close()

    def add_permission_node(account_id: str, node: str):
        """
        ## Add Permission Node
        Adds a permission node to a user.
        
        ### Parameters
        - account_id (str): UserId of the account.
        - node (str): Permission node to add to the account.
        
        ### Returns
        None
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Add user permissions
        cursor.execute("INSERT INTO permissions (account_id, node) VALUES (%s, %s)", (account_id, node,))
        conn.commit()
        conn.close()

    def remove_permission_node(account_id: str, node: str):
        """
        ## Remove Permission Node
        Removes a permission node from an account.
        
        ### Parameters
        - account_id (str): UserId of the account.
        - node (str): Permission node to remove from the account.
        
        ### Returns
        None
        """
        conn = connect_to_database()
        cursor = conn.cursor()

        # Remove user permissions
        cursor.execute("DELETE FROM permissions WHERE account_id = %s AND node = %s", (account_id, node,))
        conn.commit()
        conn.close()

class reports:
    def submit_report(user: str, service: str, reason: str, content: str):
        conn = connect_to_database()
        cursor = conn.cursor()

        # Add report to database
        cursor.execute("INSERT INTO reports (user, service, reason, content, resolved) VALUES (%s, %s, %s, %s, %s)", (user, service, reason, content, False,))
        conn.commit()

    def get_reports(filter: str, limit: int = 100):
        conn = connect_to_database()
        cursor = conn.cursor()

        # Check filter and execute correct SQL query
        if filter == "unresolved":
            cursor.execute("SELECT * FROM reports WHERE resolved = %s LIMIT %s", (False, limit))
        elif filter == "resolved":
            cursor.execute("SELECT * FROM reports WHERE resolved = %s LIMIT %s", (True, limit))
        else:
            cursor.execute("SELECT * FROM reports LIMIT %s", (limit,))

        reports = cursor.fetchall()

        return reports
    
    def get_report(report_id: int):
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reports WHERE id = %s", (report_id,))
        report = cursor.fetchone()

        return report
    
    def resolve_report(report_id: int):
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("UPDATE reports SET resolved = %s WHERE id = %s", (True, report_id))
        conn.commit()

class reports:
    def submit_report(user: str, service: str, reason: str, content: str):
        conn = connect_to_database()
        cursor = conn.cursor()

        # Add report to database
        cursor.execute("INSERT INTO reports (user, service, reason, content, resolved) VALUES (%s, %s, %s, %s, %s)", (user, service, reason, content, False,))
        conn.commit()

    def get_reports(filter: str, limit: int = 100):
        conn = connect_to_database()
        cursor = conn.cursor()

        # Check filter and execute correct SQL query
        if filter == "unresolved":
            cursor.execute("SELECT * FROM reports WHERE resolved = %s LIMIT %s", (False, limit))
        elif filter == "resolved":
            cursor.execute("SELECT * FROM reports WHERE resolved = %s LIMIT %s", (True, limit))
        else:
            cursor.execute("SELECT * FROM reports LIMIT %s", (limit,))

        reports = cursor.fetchall()

        return reports
    
    def get_report(report_id: int):
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM reports WHERE id = %s", (report_id,))
        report = cursor.fetchone()

        return report
    
    def resolve_report(report_id: int):
        conn = connect_to_database()
        cursor = conn.cursor()

        cursor.execute("UPDATE reports SET resolved = %s WHERE id = %s", (True, report_id))
        conn.commit()

def get_username_from_email(email):
    """
    ## Get Username From Email
    Gets the username from an email address.
    
    ### Parameters
    - email (str): Email of the account.
    
    ### Returns
    STRING: Email of the account.
    """
    conn = connect_to_database()
    cursor = conn.cursor()

    # Get username from email
    cursor.execute("SELECT username FROM accounts WHERE email = %s", (email,))
    data = cursor.fetchone()
    conn.close()

    return data[0]

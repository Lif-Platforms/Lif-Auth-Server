from app.database import connections
import app.database.exceptions as db_exceptions
from typing import Literal
import secrets
import uuid
import hashlib
from typing import Optional, Tuple, cast

def verify_credentials(username: str, password: str) -> bool:
    """
    Handles the verification of user login credentials.

    Parameters:
        username (str): Username of the account.
        password (str): Password of the account.
    
    Returns:
        out (bool): True
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Get password salt for user
    cursor.execute("SELECT salt FROM accounts WHERE username = %s", (username,))
    salt = cast(Optional[Tuple[str]], cursor.fetchone())

    if not salt:
        raise db_exceptions.InvalidCredentials()
    
    # Hash the password
    saltedPassword: str = password + salt[0]
    passwordHash: str = hashlib.sha256(saltedPassword.encode()).hexdigest()

    # Validate login credentials
    cursor.execute("SELECT username, password, role FROM accounts WHERE username = %s AND password = %s",
                   (username, passwordHash,))
    account = cursor.fetchone()
    conn.close()

    # Checks if the account was found
    if account:
        # Check if account is suspended
        if account[2] == "SUSPENDED":
            raise db_exceptions.AccountSuspended()
        else:
            return True
    else:
        raise db_exceptions.InvalidCredentials()
            
def check_token(username: str, token: str) -> bool:
    """
    Handles the verification of user tokens.
    
    Parameters:
        username (str): Username of the account.
        token (str): Token of the account.
    
    Returns:
        out (bool): If the token is valid.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Get account from database
    cursor.execute("SELECT username, token, role FROM accounts WHERE username = %s AND token = %s", (username, token,))
    account = cursor.fetchone()
    conn.close()

    # Check token
    if account:
        # Check role
        if account[2] != "SUSPENDED":
            return True
        else:
            raise db_exceptions.AccountSuspended()
    else:
        raise db_exceptions.InvalidToken()


def check_username(username: str) -> bool:
    """
    Checks if a username exists.
    
    Parameters:
        username (str): Username to check.
    
    Returns:
        out (bool): If the username is in use.
    """
    conn = connections.get_connection()
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

def check_email(email: str) -> bool:
    """
    Checks if an email exists.
    
    Parameters:
        email (str): Email to check.
    
    Returns:
        out (bool): If the email is in use.
    """
    conn = connections.get_connection()
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

def create_account(
    username: str,
    email: str,
    password: str,
    pronouns: Optional[str] = "Prefer not to say"
) -> str:
    """
    Handles the creation of user accounts.
    
    Parameters:
        username (str): Username of the account.
        email (str): Email of the account.
        password (str): Password of the account.
        password_salt (str): Salt for the password.

    Returns:
        token (str): The token for the acount.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Generate user token
    token = str(secrets.token_hex(16 // 2))

    # Generate user id
    user_id = str(uuid.uuid4()) 

    # Generate a new password salt and hash the new password
    salt = secrets.token_bytes(16).hex()
    saltedPassword = password+salt
    passwordHash = hashlib.sha256(saltedPassword.encode()).hexdigest()

    # Check to ensure the username and email are not already in use
    cursor.execute(
        "SELECT username, email FROM accounts WHERE username = %s OR email = %s",
        (username, email)
    )
    result = cursor.fetchone()

    if result:
        raise db_exceptions.Conflict()

    cursor.execute("""
        INSERT INTO accounts (username, password, email, token, salt, bio, pronouns, user_id) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
        (username, passwordHash, email, token, salt, None, pronouns, user_id)
    )

    conn.commit()
    conn.close()

    return token

def check_user_exists(account: str, mode: Literal["ACCOUNT_ID", "USERNAME"]) -> bool:
    """
    Checks if an account already exists in the database.
    
    Parameters:
        account (str): Username or id of the account.
        mode (str): Specify if the account parameter is an 'ACCOUNT_ID' or 'USERNAME'.
    
    Returns:
        out (bool): If th user was found.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    searchColumn = "user_id" if mode == "ACCOUNT_ID" else "username"
    query = f"SELECT * FROM accounts WHERE {searchColumn} = %s;"

    cursor.execute(query, (account,))
    user = cursor.fetchone()
    conn.close()

    if user:
        return True
    else:
        return False
        
def check_account_permission(account_id: str, node: str) -> bool:
    """
    Checks the acount permissions for an account.
    
    Parameters:
        account_id (str): UserId of the account.
        node (str): Permission node to check if user has.
    
    Returns:
        out (bool): If the user has permission.
    """
    conn = connections.get_connection()
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
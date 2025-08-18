from app.database import connections
from typing import Tuple, Optional, cast, Literal, Dict, List
from app.database import exceptions as db_exceptions
from app.models import database as db_models
from mysql.connector.cursor import MySQLCursorDict

def get_password_salt(username: str) -> Optional[str]:
    """
    Gets the salt for a password for an account.
    
    Parameters:
        username (str): Username of the account.
    
    Returns:
        out (str, None): Password salt.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Gets the salt for the given username from the MySQL database
    cursor.execute("SELECT salt FROM accounts WHERE username = %s", (username,))
    raw = cursor.fetchone()
    result = cast(Optional[Tuple[str]], raw)
    conn.close()

    return result[0] if result else None

def retrieve_user_token(username: str) -> Optional[str]:
    """
    Gets the token for an account.
    
    Parameters:
        username (str): Username of the account.
    
    Returns:
        out (str): The token for the account.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Get token from database
    cursor.execute("SELECT token FROM accounts WHERE username = %s", (username,))
    raw = cursor.fetchone()
    token = cast(Optional[Tuple[str]], raw)

    return token[0] if token else None

def get_bio(username: str) -> Optional[str]:
    """
    Gets the bio for a user account.
    
    Parameters:
        username (str): Username of the account.
    
    Returns:
        out (str): Bio of the user.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT bio FROM accounts WHERE username = %s", (username,))
    raw = cursor.fetchone()
    conn.close()

    if not raw:
        raise db_exceptions.UserNotFound()
    
    bio = cast(Optional[Tuple[str]], raw)
    
    return bio[0] if bio else None

def get_pronouns(username) -> Optional[str]:
    """
    Gets the pronouns for a user account.
    
    Parameters:
        username (str): Username of the account.
    
    Returns:
        out (str): Pronouns for the account.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT pronouns FROM accounts WHERE username = %s", (username,))
    raw = cursor.fetchone()
    conn.close()

    if not raw:
        raise db_exceptions.UserNotFound()
    
    pronouns = cast(Optional[Tuple[str]], raw)

    return pronouns[0] if pronouns else None

def get_user_email(username: str) -> Optional[str]:
    """
    Gets the email for a user account.
    
    Parameters:
        username (str): Username of the account.
    
    Returns:
        out (str): Email for the user.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT email FROM accounts WHERE username = %s", (username,))
    raw = cursor.fetchone()
    conn.close()

    if not raw:
        raise db_exceptions.UserNotFound()
    
    email = cast(Optional[Tuple[str]], raw)

    return email[0] if email else None

def get_bulk_emails(
    accounts: list,
    search_mode: Literal["userID", "username"]
) -> List[Dict[str, str]]:
    """
    Allows services to supply a list of accounts and get their emails.
    
    Parameters:
        accounts (list): List of accounts.
        search_mode (str): Specify if the accounts parameter is a list of 'userID' or 'username'.
    
    Returns:
        out (list): List of emails for each account. 
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Check search mode
    if search_mode == "userID":
        search_column = "user_id"
    else:
        search_column = "username"

    # Create placeholders for the list of values
    placeholders = ', '.join(['%s'] * len(accounts))

    # Generate the SQL query dynamically with parameter placeholders
    query = f"SELECT username, email FROM accounts WHERE {search_column} IN ({placeholders})"

    # Execute the query with the list of values
    cursor.execute(query, accounts)

    # Fetch the results
    found_accounts = cursor.fetchall()
    conn.close()

    emails = []

    for account in found_accounts:
        username = account[0] if account and isinstance(account[0], str) else None
        email = account[1] if account and isinstance(account[1], str) else None

        if not username or not email:
            continue

        emails.append({"username": username, "email": email})

    return emails

def get_username(account_id: str) -> str:
    """
    Gets the username from  an account id.
    
    Parameters:
        account_id (str): The userId for the account.
    
    Returns:
        out (str): Username for the account.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT username FROM accounts WHERE user_id = %s", (account_id,))
    raw = cursor.fetchone()
    conn.close()

    if not raw:
        raise db_exceptions.UserNotFound()
    
    username = cast(Tuple[str], raw)

    return username[0]

def get_user_id(username: str) -> str:
    """
    Gets the account id from the username.
    
    Parameters:
        username (str): Username of the account.
    
    Returns:
        out (str): Id of the user.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM accounts WHERE username = %s", (username,))
    raw = cursor.fetchone()
    conn.close()

    if not raw:
        raise db_exceptions.UserNotFound()
    
    userId = cast(Tuple[str], raw)

    return userId[0]

def check_if_user_exists(user: str) -> bool:
    """
    Checks to see if a user exists.

    Parameters:
        user (str): The user to check for.

    Returns:
        out (bool): If the user exists.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM accounts WHERE username = %s", (user,))
    data = cursor.fetchone()
    cursor.close()

    return True if data else False
    
def get_role(username: str) -> Optional[str]:
    """
    Get the users role.

    Parameters:
        username (str): The username of the account.

    Returns:
        out (str): The role of the user.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT role FROM accounts WHERE username = %s", (username,))
    raw = cursor.fetchone()
    conn.close()

    if not raw:
        raise db_exceptions.UserNotFound()
    
    role = cast(Optional[Tuple[str]], raw)

    return role[0] if role else None


def get_all_accounts() -> Optional[list]:
    """
    Gets all Lif Accounts.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM accounts")
    accounts = cursor.fetchall()

    return accounts

def search_users(query: str) -> List[db_models.UserSearch]:
    """
    Search users in the database.

    Parameters:
        query (str): The user to search.

    Returns:
        out (List[UserSearch]): List of results from the search.
    """
    conn = connections.get_connection()
    cursor = cast(MySQLCursorDict, conn.cursor(dictionary=True))

    # Search database for users
    cursor.execute("""SELECT username, user_id, role FROM accounts 
                   WHERE username LIKE %s
                   LIMIT 20""",
                   (query,))
    resultsRAW = cursor.fetchall()
    results: list[db_models.UserSearch] = []

    for result in resultsRAW:
        if not result: continue

        results.append(db_models.UserSearch(
            userId=str(result["user_id"]),
            username=str(result["username"]),
            role=str(result["role"]),
            permissions=[]
        ))

    # Add list of permissions to each result
    user_ids = [result.userId for result in results]
    format_strings = ','.join(['%s'] * len(user_ids))

    sqlQuery = f"SELECT account_id, node FROM permissions WHERE account_id IN ({format_strings})"
    cursor.execute(sqlQuery, user_ids)
    permissions = cursor.fetchall()

    for permission in permissions:
        if not permission: continue

        for result in results:
            if result.userId: result.permissions.append(
                str(permission["node"])
            )

    return results

def get_user_info(account_id: str) -> db_models.UserInfo:
    """
    Get info about a user.
    Parameters:
        account_id (str): The id of the account.
    Raises:
        app.database.exceptions.UserNotFound: The user was not found.
    Returns:
        out (UserInfo): The user requested.
    """
    conn = connections.get_connection()
    cursor = cast(MySQLCursorDict, conn.cursor(dictionary=True))

    cursor.execute("SELECT * FROM accounts WHERE user_id = %s", (account_id,))
    userInfo = cursor.fetchone()

    if not userInfo:
        raise db_exceptions.UserNotFound()
    
    user = db_models.UserInfo(
        userId=account_id,
        username=str(userInfo["username"]),
        pronouns=str(userInfo["pronouns"]),
        bio=str(userInfo["bio"]),
        role=str(userInfo["role"]),
        permissions=[]
    )

    # Get user permissions
    cursor.execute("SELECT node FROM permissions WHERE account_id = %s",
                   (account_id,))
    permissions = cursor.fetchall()

    for node in permissions:
        if not node: continue
        user.permissions.append(str(node["node"]))

    return user

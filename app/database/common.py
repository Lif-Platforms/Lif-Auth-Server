from mysql.connector import MySQLConnection
from app.database import connections
from typing import Optional, cast, Tuple

def check_user_exists_by_id(
        user_id: str,
        conn: Optional[MySQLConnection] = None
) -> bool:
    """
    Check if the user exists by their user id

    Parameters:
        user_id (str): The id of the user
        conn (MySQLConnection): If supplied, this function will use the supplied connection. 
                                If not, it will create a new one and close it once complete.

    Returns:
        out (bool): If the user was found.
    """
    mysqlConn = connections.get_connection() if not conn else conn
    cursor = mysqlConn.cursor()

    # Check if the user exists
    cursor.execute("SELECT user_id FROM accounts WHERE username = %s", (user_id,))
    user = cast(Optional[Tuple[str]], cursor.fetchone())

    # Close db conn but only if it was created by this function
    # Otherwise the function caller will handle the conn
    if not conn:
        mysqlConn.close()

    return True if user else False

def get_username_from_email(email) -> Optional[str]:
    """
    Gets the username from an email address.

    Parameters:
        email (str): Email of the account.

    Returns:
        out (Optional[str]): Username of the user.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Get username from email
    cursor.execute("SELECT username FROM accounts WHERE email = %s", (email,))
    data = cursor.fetchone()
    conn.close()

    username = cast(str, data[0]) if data else None

    return username

def get_user_id(username: str) -> Optional[str]:
    """
    Get a user id from a users username.

    Parameters:
        username (str): The username for the account.

    Returns:
        out (Optional[str]): The id of the user or None if user not found.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT user_id FROM accounts WHERE username = %s", (username,))
    userRaw = cursor.fetchone()
    user = cast(str, userRaw[0]) if userRaw else None

    return user
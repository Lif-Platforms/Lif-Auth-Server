import secrets
from app.database import connections
from typing import Optional, Tuple, cast, List
from app.database import exceptions as db_exceptions
import hashlib
from app.database import common as db_common
from mysql.connector import MySQLConnection
from app.models import database as db_models

def update_user_bio(username, data) -> None:
    """
    Handles updating the user bio.
    
    Parameters:
        username (str): Username of the account.
        data (str): The new bio.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT username FROM accounts WHERE username = %s", (username,))
    user = cast(Optional[Tuple[str]], cursor.fetchone())

    if not user:
        raise db_exceptions.UserNotFound()

    # Grab user info from database
    cursor.execute("UPDATE accounts SET bio = %s WHERE username = %s", (data, username))
    conn.commit()
    conn.close()

def update_user_pronouns(username, data) -> None:
    """
    Updates user pronouns for an account.
    
    Parameters:
        username (str): Username of the account.
        data (str): The new pronouns.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT username FROM accounts WHERE username = %s", (username,))
    user = cast(Optional[Tuple[str]], cursor.fetchone())

    if not user:
        raise db_exceptions.UserNotFound()

    # Update pronouns in database
    cursor.execute("UPDATE accounts SET pronouns = %s WHERE username = %s", (data, username))
    conn.commit()
    conn.close()

def update_user_salt(username: str, salt: str) -> None:
    """
    Updates the salt for the password of a user account.
    
    Parameters:
        username (str): Username of the account.
        salt (str): New password salt.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT username FROM accounts WHERE username = %s", (username,))
    user = cast(Optional[Tuple[str]], cursor.fetchone())

    if not user:
        raise db_exceptions.UserNotFound()

    # Update salt in database
    cursor.execute("UPDATE accounts SET salt = %s WHERE username = %s", (salt, username))
    conn.commit()
    conn.close()

def update_password(username: str, password: str) -> None:
    """
    Updates the password of a user account.
    
    Parameters:
        username (str): Username of the account.
        password (str): New password for the account.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Check if the user exists
    cursor.execute("SELECT username FROM accounts WHERE username = %s", (username,))
    user = cast(Optional[Tuple[str]], cursor.fetchone())

    if not user:
        raise db_exceptions.UserNotFound()
    
    # Generate a new password salt and hash the new password
    salt = secrets.token_bytes(16).hex()
    saltedPassword = password+salt
    passwordHash = hashlib.sha256(saltedPassword.encode()).hexdigest()

    # Update password and salt in database
    cursor.execute("UPDATE accounts SET password = %s WHERE username = %s", (passwordHash, username))
    cursor.execute("UPDATE accounts SET salt = %s WHERE username = %s", (salt, username,))
    conn.commit()
    conn.close()

def set_role(account_id, role) -> None:
    """
    Updates the role of a Lif Account.
    
    Parameters:
        account_id (str): UserId of the account.
        role (str): Role that the account will be set to.
    """
    conn = cast(MySQLConnection, connections.get_connection())
    cursor = conn.cursor()

    # Check if the user exists
    if not db_common.check_user_exists_by_id(
        user_id=account_id,
        conn=conn
    ):
        raise db_exceptions.UserNotFound()

    # Set role of user
    cursor.execute("UPDATE accounts SET role = %s WHERE user_id = %s", (role, account_id,))
    conn.commit()
    conn.close()

def update_roles(users: List[db_models.RoleList]) -> None:
    """
    Update roles in bulk.

    Parameters:
        users (List[RoleList]): List of users and their roles to update.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    query = "UPDATE accounts SET role = %s WHERE user_id = %s"
    values = [(user.role, user.userId) for user in users]

    cursor.executemany(query, values)
    conn.commit()
    conn.close()

def update_permissions(users: List[db_models.PermissionsList]) -> None:
    """
    Update permissions in bulk. Will remove all existing permissions for users and add new ones.

    Parameters:
        users (List[PermissionsList]): List of users and their new permissions.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Delete all existing permissions for all listed users
    query = "DELETE FROM permissions WHERE account_id = %s"
    values = [(user.userId,) for user in users]

    cursor.executemany(query, values)

    # Add new permissions for all users
    query = "INSERT INTO permissions (account_id, node) VALUES (%s, %s)"
    masterValues = []

    for user in users:
        values = [(user.userId, permission) for permission in user.permissions]
        masterValues.extend(values)

    cursor.executemany(query, masterValues)
    conn.commit()
    conn.close()

def update_email(account_id: str, email: str) -> None:
    """
    Updates the email on a Lif Account.
    
    Parameters:
        account_id (str): UserId of the account.
        email (str): New email the account.
    """
    conn = cast(MySQLConnection, connections.get_connection())
    cursor = conn.cursor()

    # Check if the user exists
    if not db_common.check_user_exists_by_id(
        user_id=account_id,
        conn=conn
    ):
        raise db_exceptions.UserNotFound()

    # Update user email
    cursor.execute("UPDATE accounts SET email = %s WHERE user_id = %s", (email, account_id,))
    conn.commit()
    conn.close()

def add_permission_node(account_id: str, node: str) -> None:
    """
    Adds a permission node to a user.
    
    Parameters:
        account_id (str): UserId of the account.
        node (str): Permission node to add to the account.
    """
    conn = cast(MySQLConnection, connections.get_connection())
    cursor = conn.cursor()

    # Check if user exists
    if not db_common.check_user_exists_by_id(
        user_id=account_id,
        conn=conn
    ):
        raise db_exceptions.UserNotFound()

    # Add user permissions
    cursor.execute("INSERT INTO permissions (account_id, node) VALUES (%s, %s)", (account_id, node,))
    conn.commit()
    conn.close()

def remove_permission_node(account_id: str, node: str) -> None:
    """
    Removes a permission node from an account.
    
    Parameters:
        account_id (str): UserId of the account.
        node (str): Permission node to remove from the account.
    """
    conn = cast(MySQLConnection, connections.get_connection())
    cursor = conn.cursor()

    # Check if user exists
    if not db_common.check_user_exists_by_id(
        user_id=account_id,
        conn=conn
    ):
        raise db_exceptions.UserNotFound()

    # Remove user permissions
    cursor.execute("DELETE FROM permissions WHERE account_id = %s AND node = %s", (account_id, node,))
    conn.commit()
    conn.close()

def reset_token(username: str) -> None:
    """
    Resets the token on an account.

    Parameters:
        username (str): Username of the account.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    # Generate user token
    token = str(secrets.token_hex(16 // 2))

    # Update token in database
    cursor.execute("UPDATE accounts SET token = %s WHERE username = %s", (token, username))
    conn.commit()
    conn.close()

def save_2fa_secret(account_id: str, secret: str) -> None:
    """
    Save the users 2-factor auth secret.
    Parameters:
        account_id (str): The id of the account.
        secret (str): The users 2fa secret.
    """
    conn = connections.get_connection()
    cursor = conn.cursor()

    cursor.execute("UPDATE accounts SET 2fa_secret = %s WHERE user_id = %s",
                   (secret, account_id))
    conn.commit()
    conn.close()
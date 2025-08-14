# -------------------------------------
# Description: This script connects to the MySQL database to assign
#              all Lif Accounts user ids.
#
# Author: Superior126
# Creation Date: 11/11/23 
# --------------------------------------

# Import libraries
import uuid
from stdiomask import getpass
import mysql.connector

# Ask for database host/credentials
db_host = input('Enter Database Host: ')
db_user = input('Enter Database User: ')
db_password = getpass('Enter Database Password: ', mask='*')
db_database = input('Enter Database: ')

# Connect to MySQL database
print("Connecting to MySQL...")

try:
    conn = mysql.connector.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_database
    )
    print('Connection Successful!')

except Exception as error:
    print('MySQL connection failed with exception: ' + error)
    quit() 

# Define database cursor
cursor = conn.cursor()

# Get all accounts from MySQL database
print('Fetching user accounts...')

cursor.execute("SELECT * FROM accounts")
accounts = cursor.fetchall()

# Assign all users user ids
print('Assigning user ids...')

for user in accounts: 

    # Check if account already has a user id
    if user[8] == None:
        # Generate new user id
        user_id = str(uuid.uuid4()) 

        # Update account in database
        cursor.execute("UPDATE accounts SET user_id = %s WHERE username = %s", (user_id, user[1]))

# Commit all changes to database and close MySQL connection
conn.commit()
conn.close()

print("Operation Complete!")
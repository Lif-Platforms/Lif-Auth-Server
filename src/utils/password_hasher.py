import hashlib
import utils.db_interface as database
import secrets

# Function for getting the password hash using the salt in the database
# Requires username to find the hash associated with the password
def get_hash_with_database_salt(username, password):
    # Gets the salt from the database
    salt = database.info.get_password_salt(username)

    if salt == False:
        return False  
    else:
        # Adding salt at the last of the password
        dataBase_password = password+salt
        # Encoding the password
        hashed = hashlib.sha256(dataBase_password.encode())
        
        # Returns the password hash 
        return hashed.hexdigest()
    
# Generate radom salt and get password hash
def get_hash_gen_salt(password):
    # Generate random salt
    salt = secrets.token_bytes(16)

    # Adding salt at the last of the password
    password_and_salt = password+salt.hex()

    # Encoding the password
    hashed = hashlib.sha256(password_and_salt.encode())
    
    # Returns the password hash 
    return {"password": hashed.hexdigest(), "salt": salt.hex()}
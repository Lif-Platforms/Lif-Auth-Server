from flask import Flask, jsonify
import utils.db_interface as database
import utils.password_hasher as hasher
from flask import send_file
from flask_cors import CORS, cross_origin
import os
from flask import Flask, send_from_directory
import utils.email_checker as email_interface

app = Flask(__name__)
CORS(app)


@app.route('/')
def home():
    return 'Welcome to Lif Auth Server!'

@app.route('/.well-known/acme-challenge/<filename>')
def acme_challenge(filename):
    return send_from_directory('.well-known/acme-challenge', filename)

@app.route('/login/<username>/<password>')
@cross_origin()
def login(username, password):
    # Gets password hash
    password_hash = hasher.get_hash_with_database_salt(username=username, password=password)

    # Checks if password hash was successful 
    if password_hash == False:
        return jsonify({"Status": "Unsuccessful", "Token": "None"})
    
    else:
        # Verifies credentials with database
        status = database.verify_credentials(username=username, password=password_hash)

        if status == "Good!":
            # Gets token from database
            token = database.retrieve_user_token(username=username)

            # Returns info to client
            return jsonify({"Status": "Successful", "Token": token})
        
        else: 
            # Tells client credentials are incorrect
            return jsonify({"Status": "Unsuccessful", "Token": "None"})
        
@app.route('/verify_token/<username>/<token>')
def verify_token(username, token): 
    # Gets token from database 
    database_token = database.retrieve_user_token(username=username)

    if database_token == False: 
        return jsonify({"Status": "Unsuccessful"})
    
    elif database_token == token:
        return jsonify({"Status": "Successful"})
    
    else: 
        return jsonify({"Status": "Unsuccessful"})
    
@app.route('/get_pfp/<username>')
def get_pfp(username):
    # Checks if the use has a profile pic uploaded
    if os.path.isfile(f'user_images/pfp/{username}'):
         return send_file(f'user_images/pfp/{username}', mimetype='image/gif')
    
    else: 
        # Returns default image if none is uploaded
         return send_file('user_images/pfp/default.png', mimetype='image/gif')
    
@app.route('/get_banner/<username>')
def get_banner(username):
    # Checks if the use has a profile pic uploaded
    if os.path.isfile(f'user_images/banner/{username}'):
         return send_file(f'user_images/banner/{username}', mimetype='image/gif')
    
    else: 
        # Returns default image if none is uploaded
         return send_file('user_images/banner/default.png', mimetype='image/gif')
    
@app.route('/create_account/<username>/<email>/<password>')
def create_account(username, email, password):
    # Check username usage
    username_status = database.check_username(username)
    if username_status == True:
        return {"status": "unsuccessful", "reason": "Username Already in Use!"}
    
    # Check email usage
    email_status = database.check_email(email)
    if email_status ==  True:
        return {"status": "unsuccessful", "reason": "Email Already in Use!"}
    
    # Check if email is valid
    email_isValid = email_interface.is_valid_email(email)
    if email_isValid == False:
        return {"status": "unsuccessful", "reason": "Email is Invalid!"}
    
    # Hash user password
    password_hash = hasher.get_hash_gen_salt(password)

    # Create user account
    database.create_account(username=username, password=password_hash['password'], email=email, password_salt=password_hash['salt'])

    return {"status": "ok"}

if __name__ == '__main__':
    app.run(debug=True, port=8002)
from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse, RedirectResponse
from starlette.responses import Response
import tldextract
import os
import yaml
import json
import re
import io
from PIL import Image, ImageDraw
import sentry_sdk
from _version import __version__
from utils import db_interface as database
from utils import password_hasher as hasher
from utils import email_checker as email_interface
from utils import access_control as access_control
from utils import mail_service_interface as mail_service

# Check setup
print("Checking user images folder...")
if os.path.isdir("user_images") == False:
    os.mkdir("user_images")
    print("Created 'user_images' directory!")

if os.path.isdir("user_images/pfp") == False:
    os.mkdir("user_images/pfp")
    print("Created 'user_images/pfp' directory!")

if os.path.isdir("user_images/banner") == False:
    os.mkdir("user_images/banner")
    print("Created 'user_images/banner' directory!")

# Check location of assets folder
if os.path.isdir("assets"):
    assets_folder = "assets"

else: 
    assets_folder = "src/assets"

# Check location of resources folder
if os.path.isdir("resources"):
    resources_folder = "resources"

else: 
    resources_folder = "src/resources"

# Check the config.yml to ensure its up-to-date
print("Checking config...")

if not os.path.isfile("config.yml"):
    with open("config.yml", 'x') as config:
        config.close()

with open("config.yml", "r") as config:
    contents = config.read()
    configurations = yaml.safe_load(contents)
    config.close()

# Ensure the configurations are not None
if configurations == None:
    configurations = {}

# Open reference json file for config
with open(f"{resources_folder}/json data/default_config.json", "r") as json_file:
    json_data = json_file.read()
    default_config = json.loads(json_data)

if not os.path.isfile('access-control.yml'):
    with open("access-control.yml", 'x') as config:
        config.close()

# Compare config with json data
for option in default_config:
    if not option in configurations:
        configurations[option] = default_config[option]
        print(f"Added '{option}' to config!")

# Open config in write mode to write the updated config
with open("config.yml", "w") as config:
    new_config = yaml.safe_dump(configurations)
    config.write(new_config)
    config.close()

# Get run environment 
__env__= os.getenv('RUN_ENVIRONMENT')

print("Setup check complete!")

database.load_config()

# Set access token and url for mail service
mail_service.set_config(configurations['mail-service-token'], configurations['mail-service-url'])

print(__env__)

# Get logging config
log_config_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "log_config.ini")

# Enable/disable developer docs based on env
if __env__ == 'PRODUCTION':
    enable_dev_docs = None
else:
    enable_dev_docs = '/docs'

# Init sentry SDK
sentry_sdk.init(
    dsn="https://1c74e81ca13325c5ac417ea583f98d09@o4507181227769856.ingest.us.sentry.io/4507181538410496",
    environment='production' if __env__ == 'PRODUCTION' else 'development'
)

app = FastAPI(
     title="Lif Authentication Server",
     description="Official API for Lif Platforms authentication services.",
     version=__version__,
     docs_url=enable_dev_docs,
     redoc_url=None
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=configurations['allow-origins'],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/", methods=["GET", "HEAD"])
async def main():
    return "Welcome to the Lif Auth Server!"

@app.get("/login/{username}/{password}")
async def login(username: str, password: str):
    """
    ## Login Route For Lif Accounts (DEPRECIATED)
    Handles the authentication process for Lif Accounts.
    
    ### Parameters:
    - **username (str):** The username of the account.
    - **password (str):** The password for the account.

    ### Returns:
    - **JSON:** Status of login and user token.
    """
    # Gets password hash
    password_hash = hasher.get_hash_with_database_salt(username=username, password=password)

    # Checks if password hash was successful
    if not password_hash:
        return {"Status": "Unsuccessful", "Token": "None"}

    # Verifies credentials with database
    status = database.auth.verify_credentials(username=username, password=password_hash)

    if status == "OK":
        # Gets token from database
        token = database.info.retrieve_user_token(username=username)

        # Returns info to client
        return {"Status": "Successful", "Token": token}
    
    elif status == "ACCOUNT_SUSPENDED":
        return {"Status": "Unsuccessful", "Token": "None", "Suspended": True}

    else:
        # Tells client credentials are incorrect
        return {"Status": "Unsuccessful", "Token": "None", "Suspended": False}

@app.post('/lif_login')
@app.post('/auth/login')
async def lif_login(username: str = Form(), password: str = Form(), permissions: str = None):
    """
    ## Login Route For Lif Accounts (NEW)
    Handles the authentication process for Lif Accounts.

    ### Parameters:
    - **username (str):** The username of the account.
    - **password (str):** The password for the account.

    ### Query Parameters:
    - **permissions:** List of required permission nodes for successful authentication

    ### Returns:
    - **JSON:** Token for user account.
    """
    # Gets password hash
    password_hash = hasher.get_hash_with_database_salt(username=username, password=password)

    # Checks if password hash was successful
    if not password_hash:
        raise HTTPException(status_code=401, detail='Invalid Login Credentials!')

    # Verifies credentials with database
    status = database.auth.verify_credentials(username=username, password=password_hash)
    
    if status == "OK":
        # Gets token from database
        token = database.info.retrieve_user_token(username=username)

        # Check if required permissions were given
        if permissions is not None:
            # Separate permissions
            perms = permissions.split(",")

            # Get account id
            account_id = database.info.get_user_id(username)

            # Keep track of checks
            # In order for a successful authentication the checks must equal the number of permission nodes provided
            checks = 0

            # Check each perm
            for perm in perms:
                status = database.auth.check_account_permission(account_id, perm)

                # Check status and update checks
                if status:
                    checks += 1

            # Check is all checks were successful
            if checks == len(perms):
                return {'token': token}
            
            else:
                raise HTTPException(status_code=403, detail="No Permission")
        else:
            return {'token': token}
    
    elif status == "ACCOUNT_SUSPENDED":
        raise HTTPException(status_code=403, detail="Account Suspended!")
    
    else: 
        # Tells client credentials are incorrect
        raise HTTPException(status_code=401, detail='Incorrect Login Credentials')
    
@app.get("/auth/logout")
async def log_out(response: Response, redirect = None):
    """
    ## Logout Route For Lif Accounts
    Handles the logout process for Lif Accounts.

    ### Parameters:
    none

    ### Query Parameters
    - **redirect:** url to redirect to after the logout completes.

    ### Returns:
    - **STRING:** Status of the operation.
    """
    response.delete_cookie(key="LIF_USERNAME", path="/", domain=".lifplatforms.com")
    response.delete_cookie(key="LIF_TOKEN", path="/", domain=".lifplatforms.com")

    # Create a RedirectResponse
    redirect_response = RedirectResponse(url=redirect)

    # Copy the cookies from the response to the redirect response
    for cookie in response.headers.getlist("set-cookie"):
        redirect_response.headers.append("set-cookie", cookie)

    if redirect != None:
        # Check to ensure redirect URL goes to a Lif Platforms domain
        extracted = tldextract.extract(redirect)
        domain = f"{extracted.domain}.{extracted.suffix}"

        if domain == "lifplatforms.com":
            return redirect_response
        else:
            print(domain)
            raise HTTPException(status_code=400, detail="Untrusted redirect url.")
    else:
        return "Log Out Successful"

@app.get("/account/reset_token")
async def reset_token(request: Request):
    # Get auth details
    username = request.headers.get("username")
    token  = request.headers.get("token")

    # Verify token in database
    auth_status = database.auth.check_token(username, token)

    if  auth_status == "Ok":
        # Reset token in database
        database.update.reset_token(username)

        return "Token Reset"
    elif auth_status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account suspended")
    else:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@app.post("/update_pfp")
@app.post("/account/update_avatar")
async def update_pfp(file: UploadFile = File(), username: str = Form(), token: str = Form()):
    """
    ## Update User Avatar (Profile Picture)
    Allows users to update their avatar (profile picture).
    
    ### Parameters:
    - **file (file):** The image to be set as the avatar.
    - **username (str):** The username for the account.
    - **token (str):** The token for the account.

    ### Returns:
    - **dict:** Status of the operation.
    """
    # Verify user token
    status = database.auth.check_token(username=username, token=token)

    if status == "Ok":
        # Read the contents of the profile image
        contents = await file.read()

        # Save user avatar
        with open(f"user_images/pfp/{username}.png", "wb") as write_file:
            write_file.write(contents)
            write_file.close()

        return {'Status': 'Ok'}
    
    elif status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account Suspended!")

    else:
        raise HTTPException(status_code=401, detail="Invalid Token!")

@app.post("/update_profile_banner")
@app.post("/account/update_profile_banner")
async def update_banner(file: UploadFile = File(), username: str = Form(), token: str = Form()):
    """
    ## Update User Banner
    Allows users to update their account banner.
    
    ### Parameters:
    - **file (file):** The image to be set as the banner.
    - **username (str):** The username for the account.
    - **token (str):** The token for the account.

    ### Returns:
    - **dict:** Status of the operation.
    """
    # Verify user token
    status = database.auth.check_token(username=username, token=token)

    if status == "Ok":
        # Read the contents of the profile image
        contents = await file.read()

        # Save user avatar
        with open(f"user_images/banner/{username}.png", "wb") as write_file:
            write_file.write(contents)
            write_file.close()

        return {'Status': 'Ok'}
    
    elif status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account Suspended")
    
    else:
        raise HTTPException(status_code=401, detail="Invalid Token!")

@app.post('/update_account_info/personalization')
@app.post('/account/update_info/personalization')
async def update_account_info(username: str = Form(), token: str = Form(), bio: str = Form(), pronouns: str = Form()):
    """
    ## Update User Account Info
    Allows users to update their account information (bio, pronouns, etc...)
    
    ### Parameters:
    - **username (str):** The username for the account.
    - **token (str):** The token for the account.
    - **bio (str):** The bio for the account.
    - **pronouns (str):** The pronouns for the account.

    ### Returns:
    - **JSON:** Status of the operation.
    """
    # Verify user token
    token_status = database.auth.check_token(username=username, token=token)

    if token_status == "Ok":
        database.update.update_user_bio(username=username, data=bio)
        database.update.update_user_pronouns(username=username, data=pronouns)

        return JSONResponse(status_code=200, content="Updated Successfully")
    
    elif token_status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account Suspended")
    
    else:
        raise HTTPException(status_code=401, detail="Invalid Token!")

@app.get("/get_user_bio/{username}")
@app.get("/profile/get_bio/{username}")
async def get_user_bio(username: str):
    """
    ## Get User Account Bio
    Allows services to get the bio information for a given account
    
    ### Parameters:
    - **username (str):** The username for the account.

    ### Returns:
    - **str:** Bio for the account.
    """
    user_bio = database.info.get_bio(username=username)

    # Check if user exists
    if user_bio != "INVALID_USER":
        return user_bio
    else:
        raise HTTPException(status_code=404, detail="User not found")

@app.get("/get_user_pronouns/{username}")
@app.get("/profile/get_pronouns/{username}")
async def get_user_pronouns(username: str):
    return database.info.get_pronouns(username=username)
    
@app.get('/get_account_info/{data}/{account}')
@app.get('/account/get_info/{data}/{account}')
async def get_account_data(data, account, request: Request, search_mode: str = "username"):
    """
    ## Get Account Info
    Allows services to access sensitive information on Lif Accounts.

    ### Headers
    - **access-token (str):** Services access token. 
    
    ### Parameters:
    - **data (str):** Type of data being requested.
    - **account (str):** Account associated with the data.

    ### Returns:
    - **dict:** Data the service requested.
    """
    # Get access token from request header
    access_token = request.headers.get('access-token')

    # Verify access token is valid
    if access_control.verify_token(access_token):
        # Check what data the server is requesting
        if data == "email":
            # Verify server has permission to access the requested information
            if access_control.has_perms(token=access_token, permission='account.email'): 
                # Check how the server should perform its data search
                if account == "USE_HEADERS":
                    # Get accounts header
                    accounts = request.headers.get("accounts").split(",")

                    # Get accounts from database
                    database_accounts = database.info.get_bulk_emails(accounts, search_mode)

                    email_list = []

                    # Extract email from accounts
                    for user_account in database_accounts:
                        email_list.append(user_account[3])

                    return email_list
                
                else:     
                    return {"email": database.info.get_user_email(username=account)}
            else:
                raise HTTPException(status_code=403, detail="No Permission!")
        else:
            raise HTTPException(status_code=400, detail="Unknown Data Type!")
    else:
        raise HTTPException(status_code=403, detail="Invalid Token!")

@app.get("/verify_token/{username}/{token}")
async def verify_token(username: str, token: str):
    """
    ## Verify User Token (DEPRECIATED)
    Allows services to verify the authenticity of a token.
    
    ### Parameters:
    - **username (str):** The username for the account.
    - **token (str):** The token for the account.

    ### Returns:
    - **dict:** Status of the operation.
    """
    # Gets token from database
    token_status = database.auth.check_token(username=username, token=token)

    if token_status == "Ok":
        return {"Status": "Successful"}
        
    elif token_status == "SUSPENDED":
        return {"Status": "Unsuccessful"}
    
    else:
        return {"Status": "Unsuccessful"}
    
def crop_to_circle(image: Image.Image) -> Image.Image:
    """
    Crop an image to a circle shape.
    """
    # Ensure the image is square
    width, height = image.size
    min_dimension = min(width, height)
    left = (width - min_dimension) // 2
    top = (height - min_dimension) // 2
    right = (width + min_dimension) // 2
    bottom = (height + min_dimension) // 2
    image = image.crop((left, top, right, bottom))

    # Create a mask for the circular crop
    mask = Image.new('L', (min_dimension, min_dimension), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, min_dimension, min_dimension), fill=255)

    # Apply the mask to the image
    result = Image.new('RGBA', (min_dimension, min_dimension))
    result.paste(image, (0, 0), mask)
    return result

@app.get("/get_pfp/{username}")
@app.get("/profile/get_avatar/{username}")
async def get_pfp(username: str, crop: bool = False):
    """
    ## Get User Avatar (Profile Picture)
    Allows services to get the avatar (profile picture) of a specified account. 
    
    ### Parameters:
    - **username (str):** The username for the account.

    ### Query Parameters
    - **crop (boolean):** Whether or not the avatar should be cropped to a circle shape.

    ### Returns:
    - **file:** The avatar the service requested.
    """
    # Sanitize the username
    filtered_username = re.sub(r'[^a-zA-Z1-9\._]+', '', username)
        
    # Construct the file path using the sanitized username
    avatar_path = f"user_images/pfp/{filtered_username}"

    # Check if the file exists and is a regular file
    if os.path.isfile(avatar_path):
        image = Image.open(avatar_path)
    else:
        # Load default image if the user's banner doesn't exist
        image = Image.open(f'{assets_folder}/default_pfp.png')

    # Crop the image to a circle if the crop parameter is True
    if crop:
        image = crop_to_circle(image)

    # Save the image to a BytesIO object
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # Serve the image
    return Response(content=img_byte_arr.getvalue(), media_type='image/png')

@app.get("/get_banner/{username}")
@app.get("/profile/get_banner/{username}")
async def get_banner(username: str):
    """
    ## Get User Banner
    Allows services to get the account banner of a specified account.
    
    ### Parameters:
    - **username (str):** The username for the account.

    ### Returns:
    - **file:** The banner the service requested.
    """
    # Sanitize the username
    filtered_username = re.sub(r'[^a-zA-Z1-9\._]+', '', username)

    # Construct the file path using the sanitized username
    banner_path = f"user_images/banner/{filtered_username}"

    # Check if the file exists and is a regular file
    if os.path.isfile(banner_path):
        response = FileResponse(banner_path, media_type='image/gif')
    else:
        # Return default image if the user's banner doesn't exist
        response = FileResponse(f'{assets_folder}/default_banner.png', media_type='image/gif')

    # Add caching time limit to image
    response.headers["Cache-Control"] = "public, max-age=3600"

    return response
    
@app.post("/create_lif_account")
@app.post("/account/create_account")
async def create_lif_account(request: Request):
    """
    ## Create Lif Account (NEW)
    Handles the creation of Lif Accounts
    
    ### Parameters:
    - **username (str):** The username for the account.
    - **password (str):** The password for the account.
    - **email (str):** The email for the account.

    ### Returns:
    - **dict:** Status of the operation.
    """
    # Get POST data
    data = await request.json()
    username = data["username"]
    password = data["password"]
    email = data["email"]

    # Check username usage
    username_status = database.auth.check_username(username)
    if username_status:
        raise HTTPException(status_code=409, detail="Username Already in Use!")

    # Check email usage
    email_status = database.auth.check_email(email)
    if email_status:
        raise HTTPException(status_code=409, detail="Email Already in Use!")

    # Check if email is valid
    email_isValid = email_interface.is_valid_email(email)
    if not email_isValid:
        raise HTTPException(status_code=400, detail="Invalid Email!")

    # Hash user password
    password_hash = hasher.get_hash_gen_salt(password)

    # Create user account
    database.auth.create_account(username=username, password=password_hash['password'], email=email, password_salt=password_hash['salt'])

    # Send welcome email
    mail_service.send_welcome_email(email)

    return {"Status": "Ok"}  

@app.get("/check_account_info_usage/{type}/{info}")
@app.get("/account/check_info_usage/{type}/{info}")
async def check_account_info_usage(type: str, info: str):
    """
    ## Check Account Info Usage
    Allows services to check the usage of certain account info (username, email, etc.) before requesting the account creation
    
    ### Parameters:
    - **type (str):** Type of info being checked.
    - **info (str):** The info being checked.

    ### Returns:
    - **dict:** Status of the operation.
    """
    if type == "username":
        # Check username usage
        username_status = database.auth.check_username(info)
        if username_status:
            raise HTTPException(status_code=409, detail="Username Already in Use!")
        else:
            return {"Status": "Ok"}

    if type == "email":
        # Check email usage
        email_status = database.auth.check_email(info)
        if email_status:
            raise HTTPException(status_code=409, detail="Email Already in Use!")
        else:
            return {"Status": "Ok"}

    if type == "emailValid":
        # Check if email is valid
        email_isValid = email_interface.is_valid_email(info)
        if not email_isValid:
            raise HTTPException(status_code=400, detail="Invalid Email!")
        else:
            return {"Status": "Ok"}

@app.get("/create_account/{username}/{email}/{password}")
async def create_account(username: str, email: str, password: str):
    """
    ## Create Lif Account (DEPRECIATED)
    Handles the creation of Lif Accounts. 
    
    ### Parameters:
    - **username (str):** The username for the account.
    - **password (str):** The password for the account.
    - **email (str):** The email for the account.

    ### Returns:
    - **dict:** Status of the operation.
    """
    # Check username usage
    username_status = database.auth.check_username(username)
    if username_status:
        return {"status": "unsuccessful", "reason": "Username Already in Use!"}

    # Check email usage
    email_status = database.auth.check_email(email)
    if email_status:
        return {"status": "unsuccessful", "reason": "Email Already in Use!"}

    # Check if email is valid
    email_isValid = email_interface.is_valid_email(email)
    if not email_isValid:
        return {"status": "unsuccessful", "reason": "Email is Invalid!"}

    # Hash user password
    password_hash = hasher.get_hash_gen_salt(password)

    # Create user account
    database.auth.create_account(username=username, password=password_hash['password'], email=email, password_salt=password_hash['salt'])

    return {"status": "ok"}

@app.post('/suspend_account')
@app.post('/auth/suspend_account')
async def suspend_account(account_id: str = Form(), access_token: str = Form()):
    """
    ## Suspend User Account
    Updates a users role to "SUSPENDED".
    
    ### Parameters:
    - **account_id (str):** The user id for the account.
    - **access_token (str):** The user/service access token.

    ### Returns:
    - **Text:** Status of the operation.
    """
    # Verify access token
    if access_control.verify_token(access_token):
        # Verify perms
        if access_control.has_perms(access_token, "account.suspend"):
            # Update user role in database
            database.update.set_role(account_id, "SUSPENDED")

            return "ok"
        else:
            raise HTTPException(status_code=403, detail="No Permission")
    else:
        raise HTTPException(status_code=401, detail="Invalid Token")

@app.websocket('/lif_account_recovery')
@app.websocket('/account/account_recovery')
async def account_recovery(websocket: WebSocket):
    await websocket.accept()

    # Stores email and code for later use
    user_email = None
    user_code = None

    # Determines if the user has entered the correct code from the recovery email
    authenticated = False

    # Wait for client to send data
    while True:
        # Tries to receive data from client, if fails then the connection is closed
        try:
            data = await websocket.receive_json()

            # Check what kind of data the client sent
            if 'email' in data:
                # Check email with database
                if database.auth.check_email(data['email']):
                    user_email = data['email']

                    # Send recovery code to user
                    user_code = mail_service.send_recovery_email(user_email)

                    # Tell client email was received
                    await websocket.send_json({"responseType": "emailSent", "message": "Email sent successfully."})
                else:
                    # Tell client email is invalid
                    await websocket.send_json({"responseType": "error", "message": "Invalid Email!"})
                    
            elif 'code' in data:
                # Compare generated code with user provided code
                if data['code'] == user_code:
                    # Sets the user to authenticated so the password can be updated
                    authenticated = True

                    await websocket.send_json({"responseType": "codeCorrect", "message": "Code validated successfully."})
                else:
                    await websocket.send_json({"responseType": "error", "message": "Bad Code"})
                    
            elif 'password' in data:
                if authenticated:
                    # Get password hash and gen salt
                    password_hash = hasher.get_hash_gen_salt(data['password'])

                    # Get username from email
                    username = database.get_username_from_email(user_email)

                    # Update password and salt in database
                    database.update.update_password(username, password_hash['password'])
                    database.update.update_user_salt(username, password_hash['salt'])

                    # Get user token
                    token = database.info.retrieve_user_token(username)

                    await websocket.send_json({"responseType": "passwordUpdated", "username": username, "token": token})
                else:
                    await websocket.send_json({"responseType": "error", "message": "You have not authenticated yet"})
            else:
                await websocket.send_json({"responseType": "error", "message": "Bad Request"})

        except Exception as error:
            await websocket.close()
            print("connection closed due to error: " + str(error))
            break

@app.post('/lif_password_update')
@app.post('/account/update_password')
async def lif_password_update(username: str = Form(), current_password: str = Form(), new_password: str = Form()):
    """
    ## Update Account Password
    Handles the changing of a users account password. 
    
    ### Parameters:
    - **username (str):** The username for the account.
    - **current_password (str):** The current password for the account.
    - **new_password (str):** The new password for the account.

    ### Returns:
    - **JSON:** Status of the operation.
    """
    # Gets password hash
    password_hash = hasher.get_hash_with_database_salt(username=username, password=current_password)

    # Verify old credentials before updating password
    if database.auth.verify_credentials(username=username, password=password_hash) =="OK":
        # Get hashed password and salt
        new_password_data = hasher.get_hash_gen_salt(new_password)

        # Update user salt in database
        database.update.update_user_salt(username=username, salt=new_password_data['salt'])

        # Update user password in database
        database.update.update_password(username=username, password=new_password_data['password'])

        return JSONResponse(status_code=200, content='Updated Password')
    else: 
        raise HTTPException(status_code=401, detail="Invalid Password!")
    
@app.post('/account/update_email')
def update_email(username: str = Form(), password: str = Form(), email: str = Form()):
    # Get password hash
    password_hash = hasher.get_hash_with_database_salt(username, password)

    # Verify login credentials
    auth_status = database.auth.verify_credentials(username, password_hash)

    if auth_status == 'OK':
        # Check if email is valid
        if email_interface.is_valid_email(email):        
            # Check if email is already in use
            if not database.auth.check_email(email):
                # Get account ID
                account_id = database.info.get_user_id(username)

                # Update email
                database.update.update_email(account_id, email)

                return "Ok"
            
            else:
                raise HTTPException(status_code=409, detail="Email already in use!")
        else:
            raise HTTPException(status_code=400, detail="Email is not valid!")

    elif auth_status == 'ACCOUNT_SUSPENDED':
        raise HTTPException(status_code=403, detail="Account Suspended!")
    else:
        raise HTTPException(status_code=401, detail="Invalid Credentials")

@app.api_route('/auth/verify_token', methods=["POST", "GET"])
@app.api_route('/verify_lif_token', methods=["POST", "GET"])
async def verify_lif_token(request: Request, username: str = Form(None), token: str = Form(None), permissions: str = None, role: str = None):
    """
    ## Verify Lif Token (NEW)
    Handles the verification of Lif user tokens. 
    
    ### Parameters (POST):
    - **username (str):** The username for the account.
    - **token (str):** The token for the account.

    ### Cookies (GET):
    - **LIF_USERNAME:** The username for the account.
    - **LIF_TOKEN:** The token for the account.

    ### Query Parameters:
    - **permissions (str):** List of required permission nodes for successful authentication.
    - **role (str):** A role required for successful verification.

    ### Returns:
    - **JSON:** Status of the operation.
    """
    # Check the permissions of an account
    def check_perms(username: str):
        # Check if perms are supplied
        if permissions is not None:
            # Get perms list
            perms = permissions.split(",")

            # Get account id
            account_id = database.info.get_user_id(username)

            # Keep track of checks
            # In order for a successful authentication the checks must equal the number of permission nodes provided
            checks = 0

            # Check perms
            for perm in perms:
                status = database.auth.check_account_permission(account_id, perm)

                # Check status and update checks
                if status:
                    checks += 1

            # Check if all checks passed
            if checks == len(perms):
                return True
            
            else:
                return False
        else:
            return True

    # Check verification method
    if request.method == "POST":
        # Check given token against database token
        check_token_status = database.auth.check_token(username, token)
        
        if check_token_status == "Ok":
            # Check if a role was specified
            if role:
                # Get user role
                user_role = database.info.get_role(username)

                # Check if user has specified role
                if user_role != role:
                    raise HTTPException(status_code=403, detail="No Permission")

            # Check required permissions
            status = check_perms(username)

            if status:
                return JSONResponse(status_code=200, content='Token is valid!')
            else:
                raise HTTPException(status_code=403, detail="No Permission")
                
        elif check_token_status == "SUSPENDED":
            raise HTTPException(status_code=403, detail="Account Suspended!")
        
        else:
            raise HTTPException(status_code=401, detail="Invalid Token!")
        
    elif request.method == "GET":
        # Get username and token cookies
        username_cookie = request.cookies.get("LIF_USERNAME")
        token_cookie = request.cookies.get("LIF_TOKEN")

        # Check given token against database token
        check_token_status = database.auth.check_token(username_cookie, token_cookie)
        
        if check_token_status == "Ok":
            # Check if a role was specified
            if role:
                # Get user role
                user_role = database.info.get_role(username_cookie)

                # Check if user has specified role
                if user_role != role:
                    raise HTTPException(status_code=403, detail="No Permission")

            # Check permissions 
            status = check_perms(username_cookie)

            if status:
                return JSONResponse(status_code=200, content='Token is valid!')
            else:
                raise HTTPException(status_code=403, detail="No Permission")
        
        elif check_token_status == "SUSPENDED":
            raise HTTPException(status_code=403, detail="Account Suspended!")
        else:
            raise HTTPException(status_code=401, detail="Invalid Token!")
    else:
        raise HTTPException(status_code=405, detail="Method Not Allowed")
    
@app.get('/get_username/{account_id}')
@app.get('/account/get_username/{account_id}')
async def get_username(account_id: str):
    return database.info.get_username(account_id=account_id)

@app.get('/get_profile/{username}', response_class=HTMLResponse)
@app.get('/profile/get_profile/{username}', response_class=HTMLResponse)
async def get_profile(username: str, service_url: str = "NA"):
    # Check to ensure provided user exists
    user_exist = database.auth.check_username(username)

    # Set username to guest if not found
    if not user_exist:
        username = "Guest"

    # Get HTML document path
    document_path = os.path.join(os.path.dirname(__file__), "resources/html documents/profile.html")

    # Read HTML document
    with open(document_path, "r") as document:
        html_document = document.read()
        document.close()

    # Add username and to html
    html_document = html_document.replace("{{USERNAME}}", username)
    html_document = html_document.replace("{{SERVICE_URL}}", service_url)

    # Get user bio
    bio = database.info.get_bio(username)

    # Check if user has a set bio
    if isinstance(bio, str):
        # Check if user is valid
        if bio == "INVALID_USER":
            # Set the bio to be blank
            html_document = html_document.replace("{{USER_BIO}}", "")
        else:
            # Add bio to panel
            html_document = html_document.replace("{{USER_BIO}}", bio)

    elif bio is None:
        # Set the bio to be blank
        html_document = html_document.replace("{{USER_BIO}}", "")

    # Return HTML document
    return html_document

@app.route("/auth/update_permissions", methods=["POST", "DELETE"])
async def get_body(request: Request):
    """
    ## Update Permissions
    Updates the user permissions for Lif Accounts. 
    
    ### Parameters:
    - **account_id (str):** The id for the account.
    - **node (str):** The permission node you wish to add/delete.
    - **access_token (str):** Your access token for Auth Server.

    ### Returns:
    - **JSON:** Status of the operation.
    """
    data = await request.json()

    # Get data from json
    account_id = data["account_id"]
    node = data["permission_node"]
    access_token = data["access_token"]

    # Verify access token
    status = access_control.verify_token(access_token)

    if status:
        # Check access token perms
        status = access_control.has_perms(access_token, "account.permissions")

        if status:
            # Check is user exists
            if database.auth.check_user_exists(account_id, "ACCOUNT_ID"):
                # Check HTTP method being used
                if request.method == "POST":
                    # Add permission node
                    database.update.add_permission_node(account_id, node)

                    return JSONResponse(content="Permission Added")

                elif request.method == "DELETE":
                    # Add permission node
                    database.update.remove_permission_node(account_id, node)

                    return JSONResponse(content="Permission Removed")
            else:
                raise HTTPException(status_code=404, detail="User Not Found")
        else:
            raise HTTPException(status_code=403, detail="No Permission")
    else:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
@app.get("/account/get_id/{username}")
def get_account_id(username: str):
    """
    ## Get User Id
    Get the user Id of an account from the username.
    
    ### Parameters:
    - **username (str):** The username for the account.

    ### Returns:
    - **JSON:** Status of the operation.
    """
    return database.info.get_user_id(username)

@app.post("/account/report")
def report_user(user: str = Form(), service: str = Form(), reason: str = Form(), content: str = Form()):
    """
    ## Report User
    Allows the reporting of user accounts.
    
    ### Parameters:
    - **username (str):** The username for the account responsible.
    - **service (str):** The service the incident accrued on. Accepts: Ringer, Dayly, Support.
    - **reason (str):** The reason for reporting this user.
    - **content (str):** The content being reported.

    ### Returns:
    - **STRING:** Status of the operation.
    """
    accepted_services = ["Ringer", "Dayly", "Support"]

    # Check if user is valid
    if database.info.check_if_user_exists(user):
        # Check if service field is valid
        if service in accepted_services:
            # Add report to database
            database.reports.submit_report(user, service, reason, content)

            return "Ok"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid service. Accepted services: {str(accepted_services)}")
    else:
        raise HTTPException(status_code=404, detail="User not found")
    
@app.get("/moderation/reports/get_reports")
def get_reports(request: Request, search_filter: str = None):
    """
    ## Get Reports
    Gets users reports.
    
    ### Parameters:
    - None

    ### Query Parameters:
    - **filter (str):** 'unresolved': All unresolved reports. 'resolved': All resolved reports.

    ### Returns:
    - **STRING:** Status of the operation.
    """
    # Get auth information
    username = request.headers.get("username")
    token = request.headers.get("token")

    # Verify user credentials
    token_status = database.auth.check_token(username, token)

    if token_status == "Ok":
        # Check if user has moderator role
        if database.info.get_role(username) == "MODERATOR":
            # Get reports from database
            reports = database.reports.get_reports(search_filter)

            # Format reports for client
            format_reports = []

            for report in reports:
                format_reports.append({
                    "id": report[0], 
                    "user": report[1], 
                    "service": report[2], 
                    "reason": report[3], 
                    "content": report[4], 
                    "resolved": bool(report[5])
                })

            return format_reports
        else:
            raise HTTPException(status_code=403, detail="No permission!")
        
    elif token_status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account Suspended")
    else:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
@app.get("/moderation/reports/get_report/{report_id}")
def get_report(request: Request, report_id: int):
    """
    ## Get Reports
    Gets users reports.
    
    ### Parameters:
    - **report_id (int): The id of the report to fetch.

    ### Returns:
    - **JSON:** Data for requested report.
    """
    # Get auth information
    username = request.headers.get("username")
    token = request.headers.get("token")

    # Verify user credentials
    token_status = database.auth.check_token(username, token)

    if token_status == "Ok":
        # Check if user has moderator role
        if database.info.get_role(username) == "MODERATOR":
            # Get report from database
            report = database.reports.get_report(report_id)

            # Check if report was found
            if report:
                return {"id": report[0], "user": report[1], "service": report[2], "reason": report[3], "content": report[4], "resolved": report[5]}
            else:
                raise HTTPException(status_code=404, detail="Report Not Found")
        else:
            raise HTTPException(status_code=403, detail="Permission denied")
        
    elif token_status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account Suspended")
    else:
        raise HTTPException(status_code=401, detail="Invalid Token")
    
@app.post("/moderation/suspend_account")
def suspend_account_v2(request: Request, user: str = Form()):
    """
    ## Suspend Account
    Suspends user accounts.
    
    ### Parameters:
    - **user (str): The user being suspended.

    ### Returns:
    - **STRING:** Status of operation.
    """
    username = request.headers.get("username")
    token = request.headers.get("token")

    # Verify user token
    token_status = database.auth.check_token(username, token)

    if token_status == "Ok":
        # Check user role
        if database.info.get_role(username) == "MODERATOR":
            # Get account id of user
            account_id = database.info.get_account_id(user)

            # Check if user exists
            if account_id:
                # Suspend user
                database.update.set_role(account_id, "SUSPENDED")

                return "Ok"
            else:
                raise HTTPException(status_code=404, detail="User not found!")
        else:
            raise HTTPException(status_code=403, detail="No permission")
        
    elif token_status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account suspended")
    else:
        raise HTTPException(status_code=401, detail="Invalid token")
    
@app.post("/moderation/reports/resolve")
def resolve_report(request: Request, report_id: int = Form()):
    """
    ## Resolve Report
    Resolves a user report.
    
    ### Parameters:
    - **report_id (int): The id of the report.

    ### Returns:
    - **STRING:** Status of operation.
    """
    username = request.headers.get("username")
    token = request.headers.get("token")

    # Verify user token
    token_status = database.auth.check_token(username, token)

    if token_status == "Ok":
        # Check user role
        if database.info.get_role(username) == "MODERATOR":
            # Resolve report
            database.reports.resolve_report(report_id)

            return "Ok"
        else:
            raise HTTPException(status_code=403, detail="No permission")
        
    elif token_status == "SUSPENDED":
        raise HTTPException(status_code=403, detail="Account suspended")
    else:
        raise HTTPException(status_code=401, detail="Invalid token")

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, log_config=log_config_file)

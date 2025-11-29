from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    Form,
    UploadFile,
    File,
    WebSocket,
    BackgroundTasks,
    Header,
)
import app.database.exceptions as db_exceptions
from app.database import auth as db_auth
from app.database import update as db_update
from app.database import info as db_info
from app.database import common as db_common
from app.database import reports as db_reports
import requests
import os
import app.config as config
import app.access_control as access_control
from typing import cast, Optional
import re
import socket
import pyotp
from mailjet_rest import Client

router = APIRouter(
    prefix="/account",
    tags=["Account"]
)

@router.get("/reset_token")
@router.get("/v1/reset_token")
async def reset_token(request: Request):
    # Get auth details
    username = request.headers.get("username")
    token  = request.headers.get("token")

    if not username or not token:
        raise HTTPException(status_code=400, detail="Username and token required.")

    # Verify token in database
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Reset token in database
    db_update.reset_token(username)

    return "Token Reset"

@router.post("/update_avatar")
@router.post("/v1/update_avatar")
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
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Read the contents of the profile image
    contents = await file.read()

    # Save user avatar
    with open(f"user_images/pfp/{username}.png", "wb") as write_file:
        write_file.write(contents)
        write_file.close()

    return {'Status': 'Ok'}

@router.post("/update_profile_banner")
@router.post("/v1/update_profile_banner")
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
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Read the contents of the profile image
    contents = await file.read()

    # Save user avatar
    with open(f"user_images/banner/{username}.png", "wb") as write_file:
        write_file.write(contents)
        write_file.close()

    return {'Status': 'Ok'}

@router.post('/update_info/personalization')
@router.post('/v1/update_info/personalization')
async def update_account_info(
    username: str = Form(),
    token: str = Form(),
    bio: str = Form(),
    pronouns: str = Form()
):
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
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    db_update.update_user_bio(username=username, data=bio)
    db_update.update_user_pronouns(username=username, data=pronouns)

    return "Updated Successfully"

@router.get('/get_info/{data}/{account}')
@router.get('/v1/get_info/{data}/{account}')
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
    access_token = cast(Optional[str], request.headers.get('access-token'))

    if not access_token:
        raise HTTPException(status_code=400, detail="access token required.")

    # Verify access token is valid
    if access_control.verify_token(access_token):
        # Check what data the server is requesting
        if data == "email":
            # Verify server has permission to access the requested information
            if access_control.has_perms(token=access_token, permission='account.email'): 
                # Check how the server should perform its data search
                if account == "USE_HEADERS":
                    # Get accounts header
                    accountsHeader = request.headers.get("accounts")
                    accounts = accountsHeader.split(",") if isinstance(accountsHeader, str) else None

                    if not accounts:
                        raise HTTPException(status_code=400, detail="Accounts header required.")
                    
                    if search_mode != "username" and search_mode != "userID":
                        raise HTTPException(status_code=400, detail="Invalid search mode.")

                    # Get accounts from database
                    database_accounts = db_info.get_bulk_emails(accounts, search_mode)

                    email_list = []

                    # Extract email from accounts
                    for user_account in database_accounts:
                        email_list.append(user_account["email"])

                    return email_list
                
                else:     
                    return {"email": db_info.get_user_email(username=account)}
            else:
                raise HTTPException(status_code=403, detail="No Permission!")
        else:
            raise HTTPException(status_code=400, detail="Unknown Data Type!")
    else:
        raise HTTPException(status_code=403, detail="Invalid Token!")
    
def send_welcome_email(email: str, username: str):
    # Load html email document
    document_path = os.path.join(os.path.dirname(__file__), "../resources/html documents/welcome.html")

    with open(document_path, "r") as document:
        email_body = document.read()
        document.close()

    textDocumentPath = os.path.join(os.path.dirname(__file__), "../resources/text documents/welcome.txt")

    with open(textDocumentPath, "r") as document:
        email_text = document.read()
        document.close()

    mailjetKey = config.get_key("mailjet-api-key")
    mailjetSecret = config.get_key("mailjet-api-secret")

    mailjet = Client(
        auth=(mailjetKey, mailjetSecret),
        version="v3.1"
    )

    # Send email via Mailjet API
    mailjet.send.create(data={
        "Messages": [
            {
                "From": {
                    "Email": "no_reply@lifplatforms.com",
                    "Name": "Lif Platforms"
                },
                "To": [
                    {
                        "Email": email,
                        "Name": username
                    }
                ],
                "Subject": "Welcome To Lif Platforms",
                "TextPart": email_text,
                "HTMLPart": email_body
            }
        ]
    })

@router.post("/create_account")
@router.post("/v1/create")
async def create_lif_account(request: Request, bg_tasks: BackgroundTasks):
    """
    ## Create Lif Account
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

    # Create user account
    try:
        token = db_auth.create_account(
            username=username,
            password=password,
            email=email
        )
    except db_exceptions.Conflict:
        raise HTTPException(status_code=409, detail="Username or email is already in use.")

    # Send welcome email
    bg_tasks.add_task(send_welcome_email, email, username)

    return {"Status": "Ok", "Username": username, "Token": token}

def is_valid_email(email):
    # Basic format check
    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return False
    
    # Split email into local part and domain part
    local_part, domain = email.split("@")
    
    # DNS MX record check
    try:
        mx_records = socket.getaddrinfo(domain, None, socket.AF_INET, socket.SOCK_STREAM)
        if not any([record[1] == socket.SOCK_STREAM for record in mx_records]):
            return False
    except socket.gaierror:
        return False
    
    return True


@router.get("/check_info_usage/{type}/{info}")
@router.get("/v1/check_info_usage/{type}/{info}")
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
        username_status = db_auth.check_username(info)
        if username_status:
            raise HTTPException(status_code=409, detail="Username Already in Use!")
        else:
            return {"Status": "Ok"}

    if type == "email":
        # Check email usage
        email_status = db_auth.check_email(info)
        if email_status:
            raise HTTPException(status_code=409, detail="Email Already in Use!")
        else:
            return {"Status": "Ok"}

    if type == "emailValid":
        # Check if email is valid
        email_isValid = is_valid_email(info)
        if not email_isValid:
            raise HTTPException(status_code=400, detail="Invalid Email!")
        else:
            return {"Status": "Ok"}
        
def send_recovery_email(email):
    # Load html email document
    document_path = os.path.join(os.path.dirname(__file__), "../resources/html documents/recovery.html")

    with open(document_path, "r") as document:
        email_body = document.read()
        document.close()

    # Generate recovery code
    recovery_code = ''.join([str(ord(os.urandom(1)) % 10) for _ in range(5)])

    # Add recovery code to email
    email_body = email_body.replace("{{RECOVERY CODE}}", recovery_code)

    service_url = config.get_key("mail-service-url")
    access_token = config.get_key("mail-service-token")

    # Send email request to mail service
    requests.post(
        url=f"{service_url}/service/send_email",
        headers={
            "access-token": access_token,
            "subject": "Your Lif Recovery Code",
            "recipient": email
        },
        data=email_body,
        timeout=15
    )

    return recovery_code

@router.websocket('/account_recovery')
@router.websocket('/v1/recovery')
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
                if db_auth.check_email(data['email']):
                    user_email = data['email']

                    # Send recovery code to user
                    user_code = send_recovery_email(user_email)

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
                    # Get username from email
                    username = db_common.get_username_from_email(user_email)

                    if not username:
                        await websocket.send_json({"responseType": "error", "message": "Internal server error."})
                        continue

                    # Update password and salt in database
                    db_update.update_password(username, data['password'])

                    # Get user token
                    token = db_info.retrieve_user_token(username)

                    await websocket.send_json({"responseType": "passwordUpdated", "username": username, "token": token})
                else:
                    await websocket.send_json({"responseType": "error", "message": "You have not authenticated yet"})
            else:
                await websocket.send_json({"responseType": "error", "message": "Bad Request"})

        except Exception as error:
            await websocket.close()
            print("connection closed due to error: " + str(error))
            break

@router.post('/update_email')
@router.post('/v1/update_email')
def update_email(username: str = Form(), password: str = Form(), email: str = Form()):
    # Verify login credentials
    try:
        db_auth.verify_credentials(username=username, password=password)
    except db_exceptions.InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Check if email is valid
    if is_valid_email(email):        
        # Check if email is already in use
        if not db_auth.check_email(email):
            # Get account ID
            account_id = db_info.get_user_id(username)

            # Update email
            db_update.update_email(account_id, email)

            return "Ok"
        
        else:
            raise HTTPException(status_code=409, detail="Email already in use!")
    else:
        raise HTTPException(status_code=400, detail="Email is not valid!")

@router.get('/get_username/{account_id}')
@router.get('/v1/get_username/{account_id}')
async def get_username(account_id: str):
    return db_info.get_username(account_id=account_id)

@router.post('/update_password')
@router.post('/v1/update_password')
async def lif_password_update(
    username: str = Form(),
    current_password: str = Form(),
    new_password: str = Form()
):
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
    # Verify old credentials before updating password
    try:
        db_auth.verify_credentials(username=username, password=current_password)
    except db_exceptions.InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Update user password in database
    db_update.update_password(username=username, password=new_password)

    return 'Updated Password'

@router.post("/report")
@router.post("/v1/report")
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
    if db_info.check_if_user_exists(user):
        # Check if service field is valid
        if service in accepted_services:
            # Add report to database
            db_reports.submit_report(user, service, reason, content)

            return "Ok"
        else:
            raise HTTPException(status_code=400, detail=f"Invalid service. Accepted services: {str(accepted_services)}")
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.get("/get_id/{username}")
@router.get("/v1/get_id/{username}")
def get_account_id(username: str):
    """
    ## Get User Id
    Get the user Id of an account from the username.
    
    ### Parameters:
    - **username (str):** The username for the account.

    ### Returns:
    - **JSON:** Status of the operation.
    """
    return db_info.get_user_id(username)

@router.get("/v1/2fa-setup")
def setup_2fa(
    username: str = Header(),
    token: str = Header()
):
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    user_id = db_common.get_user_id(username)

    if not user_id:
        raise HTTPException(status_code=500, detail="Internal server error")
    
    try:
        two_FA_secret = db_info.get_2fa_secret(user_id)
    except db_exceptions.UserNotFound:
        raise HTTPException(status_code=500, detail="Internal server error")
    
    # If the user does not have a 2fa secret, generate a new one
    if not two_FA_secret:
        two_FA_secret = pyotp.random_base32()
        db_update.save_2fa_secret(user_id, two_FA_secret)

    return pyotp.totp.TOTP(two_FA_secret).provisioning_uri(
        name=f'{username}@lifplatforms.com',
        issuer_name='Lif Platforms'
    )
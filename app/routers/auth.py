from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse, Response, JSONResponse
import tldextract
from app.database import auth as db_auth
from app.database import exceptions as db_exceptions
from app.database import info as db_info
from app.database import update as db_update
from typing import Optional
import app.access_control as access_control

router = APIRouter(
    prefix="/auth",
    tags=["Auth"]
)

@router.post('/login')
@router.post('/v1/login')
async def lif_login(username: str = Form(), password: str = Form(), permissions: Optional[str] = None):
    """
    ## Login Route For Lif Accounts
    Handles the authentication process for Lif Accounts.

    ### Parameters:
    - **username (str):** The username of the account.
    - **password (str):** The password for the account.

    ### Query Parameters:
    - **permissions:** List of required permission nodes for successful authentication

    ### Returns:
    - **JSON:** Token for user account.
    """
    # Verifies credentials with database
    try:
        db_auth.verify_credentials(username=username, password=password)
    except db_exceptions.InvalidCredentials:
        raise HTTPException(status_code=401, detail="Invalid credentials.")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended!")
    
    # Gets token from database
    try:
        token = db_info.retrieve_user_token(username=username)
    except db_exceptions.UserNotFound:
        raise HTTPException(status_code=500, detail="Internal server error.")

    # Check if required permissions were given
    if permissions is not None:
        # Separate permissions
        perms = permissions.split(",")

        # Get account id
        account_id = db_info.get_user_id(username)

        # Keep track of checks
        # In order for a successful authentication the checks must equal the number of permission nodes provided
        checks = 0

        # Check each perm
        for perm in perms:
            status = db_auth.check_account_permission(account_id, perm)

            # Check status and update checks
            if status:
                checks += 1

        # Check is all checks were successful
        if checks != len(perms):
            raise HTTPException(status_code=403, detail="No Permission")

    return {'token': token}
    
@router.get("/logout")
@router.get("/v1/logout")
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

    if redirect:
        # Check to ensure redirect URL goes to a Lif Platforms domain
        extracted = tldextract.extract(redirect)
        domain = f"{extracted.domain}.{extracted.suffix}"

        # Create a RedirectResponse
        redirect_response = RedirectResponse(url=redirect)

        # Copy the cookies from the response to the redirect response
        for cookie in response.headers.getlist("set-cookie"):
            redirect_response.headers.append("set-cookie", cookie)

        if domain == "lifplatforms.com":
            return redirect_response
        else:
            raise HTTPException(status_code=400, detail="Untrusted redirect url.")
    else:
        return "Log Out Successful"
    
@router.api_route('/verify_token', methods=["POST", "GET"])
@router.api_route('/v1/verify_token', methods=["POST", "GET"])
async def verify_token(
    request: Request,
    username: Optional[str] = Form(None),
    token: Optional[str] = Form(None),
    permissions: Optional[str] = None,
    role: Optional[str] = None
):
    """
    ## Verify Lif Token
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
            account_id = db_info.get_user_id(username)

            # Keep track of checks
            # In order for a successful authentication the checks must equal the number of permission nodes provided
            checks = 0

            # Check perms
            for perm in perms:
                status = db_auth.check_account_permission(account_id, perm)

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
        if not username or not token:
            raise HTTPException(status_code=400, detail="Username and token required.")

        # Check given token against database token
        try:
            db_auth.check_token(username, token)
        except db_exceptions.InvalidToken:
            raise HTTPException(status_code=401, detail="Invalid token.")
        except db_exceptions.AccountSuspended:
            raise HTTPException(status_code=403, detail="Account suspended.")
        
        # Check if a role was specified
        if role:
            # Get user role
            user_role = db_info.get_role(username)

            # Check if user has specified role
            if user_role != role:
                raise HTTPException(status_code=403, detail="No Permission")

        # Check required permissions
        status = check_perms(username)

        if status:
            return "Token is valid!"
        else:
            raise HTTPException(status_code=403, detail="No Permission")
        
    elif request.method == "GET":
        # Get username and token cookies
        username_cookie = request.cookies.get("LIF_USERNAME")
        token_cookie = request.cookies.get("LIF_TOKEN")

        if not username_cookie or not token_cookie:
            raise HTTPException(status_code=400, detail="Username and token cookies required.")

        # Check given token against database token
        try:
            db_auth.check_token(username_cookie, token_cookie)
        except db_exceptions.InvalidToken:
            raise HTTPException(status_code=401, detail="Invalid token.")
        except db_exceptions.AccountSuspended:
            raise HTTPException(status_code=403, detail="Account suspended.")
        
        # Check if a role was specified
        if role:
            # Get user role
            user_role = db_info.get_role(username_cookie)

            # Check if user has specified role
            if user_role != role:
                raise HTTPException(status_code=403, detail="No Permission")

        # Check permissions 
        status = check_perms(username_cookie)

        if status:
            return 'Token is valid!'
        else:
            raise HTTPException(status_code=403, detail="No Permission")
    else:
        raise HTTPException(status_code=405, detail="Method Not Allowed")

@router.post('/suspend_account')
@router.post('/v1/suspend_account')
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
            db_update.set_role(account_id, "SUSPENDED")

            return "ok"
        else:
            raise HTTPException(status_code=403, detail="No Permission")
    else:
        raise HTTPException(status_code=401, detail="Invalid Token")

@router.route("/update_permissions", methods=["POST", "DELETE"])
async def update_permissions(request: Request):
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
            if db_auth.check_user_exists(account_id, "ACCOUNT_ID"):
                # Check HTTP method being used
                if request.method == "POST":
                    # Add permission node
                    db_update.add_permission_node(account_id, node)

                    return JSONResponse(content="Permission Added")

                elif request.method == "DELETE":
                    # Add permission node
                    db_update.remove_permission_node(account_id, node)

                    return JSONResponse(content="Permission Removed")
            else:
                raise HTTPException(status_code=404, detail="User Not Found")
        else:
            raise HTTPException(status_code=403, detail="No Permission")
    else:
        raise HTTPException(status_code=401, detail="Invalid Token")

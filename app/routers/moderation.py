from fastapi import APIRouter, HTTPException, Request, Form
from app.database import auth as db_auth
from app.database import common as db_common
from app.database import info as db_info
from app.database import exceptions as db_exceptions
from app.database import update as db_update

router = APIRouter(
    prefix="/moderation",
    tags=["Moderation"]
)

@router.post("/suspend_account")
@router.post("/v1/suspend-account")
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

    if not username or not token:
        raise HTTPException(status_code=400, detail="Username and token required.")

    # Verify user credentials
    try:
        token_status = db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token.")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Check user role
    if not db_info.get_role(username) == "MODERATOR":
        raise HTTPException(status_code=403, detail="No permission")

    # Get account id of user
    account_id = db_common.get_user_id(user)

    # Check if user exists
    if account_id:
        # Suspend user
        db_update.set_role(account_id, "SUSPENDED")

        return "Ok"
    else:
        raise HTTPException(status_code=404, detail="User not found!")
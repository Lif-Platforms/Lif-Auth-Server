from fastapi import APIRouter, HTTPException, Request, Form, Header, Body, Query
from app.database import auth as db_auth
from app.database import common as db_common
from app.database import info as db_info
from app.database import exceptions as db_exceptions
from app.database import update as db_update
from app.models import moderation as mod_models
from typing import List
from app.models import database as db_models

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
    
@router.put("/v1/manage-privileges")
def manage_privileges(
    data: List[mod_models.ManagePrivileges] = Body(),
    username: str = Header(),
    token: str = Header()
):
    """
    ## Manage Privileges
    Manage the roles and permissions of users.

    ### Headers:
    - **username (str):** Username of your account.
    - **token (str):** Token of your account.

    ### Parameters:
    - **userId (str):** The id of the user being modified.
    - **role (Optional[str]):** The role to set the user to.
    - **permissions (list):** List of permissions to assign the user.
    """
    # Verify user credentials
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Get the users account id
    userId = db_info.get_user_id(username)
    if not userId: raise HTTPException(status_code=500, detail="Internal server error.")
    
    # Verify the user has permission to modify user privileges
    if not db_auth.check_account_permission(
        account_id=userId,
        node="moderation.modify_permissions"
    ): raise HTTPException(status_code=403, detail="No permission.")

    modifyRoles: List[db_models.RoleList] = []
    modifyPermissions: List[db_models.PermissionsList]= []

    # Separate roles and permissions to modify
    for action in data:
        if action.role != None: modifyRoles.append(db_models.RoleList(
            userId=action.userId,
            role=action.role
        ))
        if len(action.permissions) > 0: modifyPermissions.append(db_models.PermissionsList(
            userId=action.userId,
            permissions=action.permissions
        ))
            
    db_update.update_roles(modifyRoles)
    db_update.update_permissions(modifyPermissions)

    return {"status": "ok"}

@router.get("/v1/user-search")
def search_users(
    query: str = Query(),
    username: str = Header(),
    token: str = Header()
) -> List[db_models.UserSearch]:
    # Verify user credentials
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Get the users account id
    userId = db_info.get_user_id(username)
    if not userId: raise HTTPException(status_code=500, detail="Internal server error.")
    
    # Verify the user has permission to modify user privileges
    if not db_auth.check_account_permission(
        account_id=userId,
        node="moderation.search_users"
    ): raise HTTPException(status_code=403, detail="No permission.")

    searchResults: List[db_models.UserSearch] = db_info.search_users(query)
    return searchResults

@router.get("/v1/get_user/{user_id}")
def get_user(
    user_id: str,
    username: str = Header(),
    token: str = Header()
) -> db_models.UserInfo:
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended")
    
    try:
        return db_info.get_user_info(user_id)
    except db_exceptions.UserNotFound:
        raise HTTPException(status_code=404, detail="User not found.")
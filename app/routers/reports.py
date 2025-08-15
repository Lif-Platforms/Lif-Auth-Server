from fastapi import APIRouter, HTTPException, Request, Form
from typing import Optional
from app.database import exceptions as db_exceptions
from app.database import reports as db_reports
from app.database import auth as db_auth
from app.database import info as db_info

router = APIRouter(
    prefix="/moderation/reports",
    tags=["Reports"]
)

@router.get("/get_reports")
@router.get("/v1/get")
def get_reports(request: Request, search_filter: Optional[str] = None):
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

    if not username or not token:
        raise HTTPException(status_code=400, detail="Username and token required.")

    # Verify user credentials
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token.")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Check if user has moderator role
    if not db_info.get_role(username) == "MODERATOR":
        raise HTTPException(status_code=403, detail="No permission.")
    
    # Check if search filter is valid
    if search_filter != "resolved" and search_filter != "unresolved" and search_filter != None:
        raise HTTPException(status_code=400, detail="Invalid search filter.")

    # Get reports from database
    reports = db_reports.get_reports(search_filter)

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

@router.get("/get_report/{report_id}")
@router.get("/v1/get/{report_id}")
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

    if not username or not token:
        raise HTTPException(status_code=400, detail="Username and token required.")

    # Verify user credentials
    try:
        token_status = db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token.")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account suspended.")

    # Check if user has moderator role
    if not db_info.get_role(username) == "MODERATOR":
        raise HTTPException(status_code=403, detail="Permission denied")

    # Get report from database
    report = db_reports.get_report(report_id)

    # Check if report was found
    if report:
        return {
            "id": report[0],
            "user": report[1],
            "service": report[2],
            "reason": report[3],
            "content": report[4],
            "resolved": report[5]
        }
    else:
        raise HTTPException(status_code=404, detail="Report Not Found")
    
@router.post("/resolve")
@router.post("/v1/resolve")
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

    # Resolve report
    db_reports.resolve_report(report_id)

    return "Ok"

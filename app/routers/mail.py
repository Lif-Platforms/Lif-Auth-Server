from fastapi import (
    APIRouter,
    Request,
    HTTPException,
    Header,
    Form,
    File,
    UploadFile,
)
import base64
import app.access_control as access_control
from app.database import info as db_info
from app.database import auth as db_auth
from app.database import exceptions as db_exceptions
from app.database import common as db_common
from mailjet_rest import Client
import app.config as config

router = APIRouter(
    prefix="/mail",
    tags=["Mail"]
)

@router.post("/send_all")
@router.post("/v1/send_all")
async def send_all_mail(request: Request):
    """
    ## Send All Mail
    Sends an email to all users.

    ### Headers:
    - **subject (str):** The subject of the email.
    - **accessToken (str):** Your auth server access token.

    ### Body:
    The content of the email.
    
    ### Parameters:
    None

    ### Returns:
    - **STRING:** Status of operation.
    """
    # Get headers
    subject = request.headers.get("subject")
    access_token = request.headers.get("accessToken")

    # Verify access token
    if not access_token or not access_control.verify_token(access_token):
        raise HTTPException(status_code=401, detail="Invalid access token")
    
    # Verify token has "email.send_all" permission node
    if not access_control.has_perms(
        token=access_token,
        permission="email.send_all"
    ):
        raise HTTPException(status_code=403, detail="insufficient permissions")

    # Get email body
    body = (await request.body()).decode('utf-8')

    # Get all accounts
    accounts = db_info.get_all_accounts()

    mailjetKey = config.get_key("mailjet-api-key")
    mailjetSecret = config.get_key("mailjet-api-secret")

    # Create mailjet client
    mailjet = Client(
        auth=(mailjetKey, mailjetSecret),
        version="v3.1"
    )

    # Create messages for email recipients
    messages = []

    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts to email.")

    for account in accounts:
         messages.append({
            "From": {
                "Email": "no_reply@lifplatforms.com",
                "Name": "Lif Platforms"
            },
            "To": [
                {
                    "Email": account[3],
                    "Name": account[1]
                },
            ],
            "Subject": subject,
            "TextPart": body,
        })

    # Define request data
    data = {
        "Messages": messages
    }

    # Send email
    email_result = mailjet.send.create(data=data)

    # Check email send status
    if email_result.status_code != 200:
        raise HTTPException(status_code=email_result.status_code, detail="Email failed to send!")

    return "Ok"

@router.post("/v2/send_all")
def send_all_v2(
    username: str = Header(),
    token: str = Header(),
    subject: str = Form(),
    textBody: str = Form(),
    file: UploadFile | None = File(default=None),
):
    """
    ## Send All Mail
    Sends an email to all users.

    ### Headers:
    - **username (str):** Your admin username.
    - **token (str):** Your admin token.

    ### Body:
    - **subject (str):** The subject of the email.
    - **textBody (str):** The content of the email.

    ### Returns:
    - **STRING:** Status of operation.
    """
    try:
        db_auth.check_token(username, token)
    except db_exceptions.InvalidToken:
        raise HTTPException(status_code=401, detail="Invalid token")
    except db_exceptions.AccountSuspended:
        raise HTTPException(status_code=403, detail="Account is suspended")
    
    # Get the users account id
    account_id = db_common.get_user_id(username)

    if not account_id:
        raise HTTPException(status_code=500, detail="Internal server error")

    # Check if the user has permission to send all mail
    if not db_auth.check_account_permission(
        account_id,
        "email.send_all"
    ):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Get all accounts
    accounts = db_info.get_all_accounts()

    mailjetKey = config.get_key("mailjet-api-key")
    mailjetSecret = config.get_key("mailjet-api-secret")

    # Create mailjet client
    mailjet = Client(
        auth=(mailjetKey, mailjetSecret),
        version="v3.1"
    )

    # Create messages for email recipients
    messages = []

    if not accounts:
        raise HTTPException(status_code=404, detail="No accounts to email.")

    for account in accounts:
        message = {
            "From": {
                "Email": "no_reply@lifplatforms.com",
                "Name": "Lif Platforms"
            },
            "To": [
                {
                    "Email": account[3],
                    "Name": account[1]
                },
            ],
            "Subject": subject,
            "TextPart": textBody,
        }

        if file:
            file_content = file.file.read()
            html_string = file_content.decode('utf-8')
            message["HTMLPart"] = html_string

        messages.append(message)

    # Send email
    email_result = mailjet.send.create(data={
        "Messages": messages
    })

    # Check email send status
    if email_result.status_code != 200:
        raise HTTPException(status_code=email_result.status_code, detail="Email failed to send!")

    return "Ok"
from fastapi import APIRouter, Request, HTTPException
import app.access_control as access_control
from app.database import info as db_info
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
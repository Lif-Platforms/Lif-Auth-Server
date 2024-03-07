import requests
import os

# Hold mail service access token and url
access_token = None
service_url = None

# Allow main script to set access token and service url
def set_config(token: str, url: str):
    global access_token
    global service_url

    access_token = token
    service_url = url

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

def send_welcome_email(email):
    # Load html email document
    document_path = os.path.join(os.path.dirname(__file__), "../resources/html documents/welcome.html")

    with open(document_path, "r") as document:
        email_body = document.read()
        document.close()

    # Send email request to mail service
    requests.post(
        url=f"{service_url}/service/send_email",
        headers={
            "access-token": access_token,
            "subject": "Welcome To Lif",
            "recipient": email
        },
        data=email_body,
        timeout=15
    )

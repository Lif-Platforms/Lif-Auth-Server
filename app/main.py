from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.__version__ import __version__
import os
import sentry_sdk
from app.config import init_config, get_key
from app.routers import (
    auth,
    account,
    moderation,
    reports,
    profile,
    mail,
)

# Get run environment 
__env__= os.getenv('RUN_ENVIRONMENT')
if __env__ == 'PRODUCTION':
    enable_dev_docs = None
else:
    enable_dev_docs = '/docs'

# Ensure user images folders exist
if not os.path.isdir("user_images/pfp"):
    os.mkdir("user_images/pfp")

if not os.path.isdir("user_images/banner"):
    os.mkdir("user_images/banner")

sentry_sdk.init(
    dsn="https://1c74e81ca13325c5ac417ea583f98d09@o4507181227769856.ingest.us.sentry.io/4507181538410496",
    environment='production' if __env__ == 'PRODUCTION' else 'development'
)

# Initialize the config
init_config()

app = FastAPI(
     title="Lif Authentication Server",
     description="Official API for Lif Platforms authentication services.",
     version=__version__,
     docs_url=enable_dev_docs,
     redoc_url=None
)

# Get allowed origins from config
origins = get_key('allow-origins')
allowedOrigins = origins if isinstance(origins, list) else ["*"]

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=allowedOrigins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.api_route("/", methods=["GET", "HEAD"])
async def main():
    return "Welcome to the Lif Auth Server!"

app.include_router(router=auth.router)
app.include_router(router=account.router)
app.include_router(router=moderation.router)
app.include_router(router=reports.router)
app.include_router(router=profile.router)
app.include_router(router=mail.router)
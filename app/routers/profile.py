from fastapi import APIRouter, HTTPException, Response
from fastapi.responses import FileResponse, HTMLResponse
import os
import io
from PIL import Image, ImageDraw
import re
from app.database import info as db_info
from app.database import auth as db_auth

router = APIRouter(
    prefix="/profile",
    tags=["Profile"]
)

# Define the location of the assets folder
assets_folder = os.path.join(__file__, "app/assets")

@router.get("/get_bio/{username}")
@router.get("/v1/get_bio/{username}")
async def get_user_bio(username: str):
    """
    ## Get User Account Bio
    Allows services to get the bio information for a given account
    
    ### Parameters:
    - **username (str):** The username for the account.

    ### Returns:
    - **str:** Bio for the account.
    """
    user_bio = db_info.get_bio(username=username)

    # Check if user exists
    if user_bio != "INVALID_USER":
        return user_bio
    else:
        raise HTTPException(status_code=404, detail="User not found")

@router.get("/get_pronouns/{username}")
@router.get("/v1/get_pronouns/{username}")
async def get_user_pronouns(username: str):
    return db_info.get_pronouns(username=username)

    
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

@router.get("/get_avatar/{username}")
@router.get("/v1/get_avatar/{username}")
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

@router.get("/get_banner/{username}")
@router.get("/v1/get_banner/{username}")
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

@router.get('/get_profile/{username}', response_class=HTMLResponse)
@router.get('/v1/get_profile/{username}', response_class=HTMLResponse)
async def get_profile(username: str, service_url: str = "NA"):
    # Check to ensure provided user exists
    user_exist = db_auth.check_username(username)

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
    bio = db_info.get_bio(username)

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

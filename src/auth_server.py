from fastapi import FastAPI, HTTPException, Request, Form, File, UploadFile, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
import os
import yaml
import json
from utils import db_interface as database
from utils import password_hasher as hasher
from utils import email_checker as email_interface
from utils import access_control as access_control

app = FastAPI()

# Check setup
print("Checking user images folder...")
if os.path.isdir("user_images") == False:
    os.mkdir("user_images")
    print("Created 'user_images' directory!")

if os.path.isdir("user_images/pfp") == False:
    os.mkdir("user_images/pfp")
    print("Created 'user_images/pfp' directory!")

if os.path.isdir("user_images/banner") == False:
    os.mkdir("user_images/banner")
    print("Created 'user_images/banner' directory!")

# Check location of assets folder
if os.path.isdir("assets"):
    assets_folder = "assets"

else: 
    assets_folder = "src/assets"

# Check location of resources folder
if os.path.isdir("resources"):
    resources_folder = "resources"

else: 
    resources_folder = "src/resources"

# Check the config.yml to ensure its up-to-date
print("Checking config...")

if not os.path.isfile("config.yml"):
    with open("config.yml", 'x') as config:
        config.close()

with open("config.yml", "r") as config:
    contents = config.read()
    configurations = yaml.safe_load(contents)
    config.close()

# Ensure the configurations are not None
if configurations == None:
    configurations = {}

# Open reference json file for config
with open(f"{resources_folder}/json data/default_config.json", "r") as json_file:
    json_data = json_file.read()
    default_config = json.loads(json_data)

if not os.path.isfile('access-control.yml'):
    with open("access-control.yml", 'x') as config:
        config.close()

# Compare config with json data
for option in default_config:
    if not option in configurations:
        configurations[option] = default_config[option]
        print(f"Added '{option}' to config!")

# Open config in write mode to write the updated config
with open("config.yml", "w") as config:
    new_config = yaml.safe_dump(configurations)
    config.write(new_config)
    config.close()

print("Setup check complete!")

database.load_config()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def home():
    return "Welcome to Lif Auth Server!"

@app.get("/login/{username}/{password}")
async def login(username: str, password: str):
    # Gets password hash
    password_hash = hasher.get_hash_with_database_salt(username=username, password=password)

    # Checks if password hash was successful
    if not password_hash:
        return {"Status": "Unsuccessful", "Token": "None"}

    # Verifies credentials with database
    status = database.verify_credentials(username=username, password=password_hash)

    if status == "Good!":
        # Gets token from database
        token = database.retrieve_user_token(username=username)

        # Returns info to client
        return {"Status": "Successful", "Token": token}
    else:
        # Tells client credentials are incorrect
        return {"Status": "Unsuccessful", "Token": "None"}
    
@app.post("/update_pfp")
async def update_pfp(file: UploadFile = File(), username: str = Form(), token: str = Form()):
    # Verify user token
    status = database.check_token(username=username, token=token)

    if status == True:
        # Read the contents of the profile image
        contents = await file.read()

        # Save user avatar
        with open(f"user_images/pfp/{username}.png", "wb") as write_file:
            write_file.write(contents)
            write_file.close()

        return {'Status': 'Ok'}
    else:
        raise HTTPException(status_code=401, detail="Invalid Token!")

@app.post("/update_profile_banner")
async def update_pfp(file: UploadFile = File(), username: str = Form(), token: str = Form()):
    # Verify user token
    status = database.check_token(username=username, token=token)

    if status == True:
        # Read the contents of the profile image
        contents = await file.read()

        # Save user avatar
        with open(f"user_images/banner/{username}.png", "wb") as write_file:
            write_file.write(contents)
            write_file.close()

        return {'Status': 'Ok'}
    else:
        raise HTTPException(status_code=401, detail="Invalid Token!")

@app.post('/update_account_info/personalization')
async def update_account_info(username: str = Form(), token: str = Form(), bio: str = Form(), pronouns: str = Form()):
    # Verify user token
    if database.check_token(username=username, token=token):
        database.update_user_bio(username=username, data=bio)
        database.update_user_pronouns(username=username, data=pronouns)

        return JSONResponse(status_code=200, content="Updated Successfully")
    else:
        raise HTTPException(status_code=401, detail="Invalid Token!")

@app.get("/get_user_bio/{username}")
async def get_user_bio(username: str):
    return database.get_bio(username=username)

@app.get("/get_user_pronouns/{username}")
async def get_user_pronouns(username: str):
    return database.get_pronouns(username=username)
    
@app.get('/get_account_info/{data}/{account}')
async def get_account_data(data, account, request: Request):
    # Get access token from request header
    access_token = request.headers.get('access-token')

    # Verify access token is valid
    if access_control.verify_token(access_token):
        # Check what data the server is requesting
        if data == "email":
            # Verify server has permission to access the requested information
            if access_control.has_perms(token=access_token, permission='account.email'): 
                return {"email": database.get_user_email(username=account)}
            else:
                raise HTTPException(status_code=403, detail="No Permission!")
        else:
            raise HTTPException(status_code=400, detail="Unknown Data Type!")
    else:
        raise HTTPException(status_code=403, detail="Invalid Token!")

@app.get("/verify_token/{username}/{token}")
async def verify_token(username: str, token: str):
    # Gets token from database
    database_token = database.retrieve_user_token(username=username)

    if not database_token:
        return {"Status": "Unsuccessful"}
    elif database_token == token:
        return {"Status": "Successful"}
    else:
        return {"Status": "Unsuccessful"}

@app.get("/get_pfp/{username}")
async def get_pfp(username: str):
    # Checks if the user has a profile pic uploaded
    if os.path.isfile(f"user_images/pfp/{username}"):
        return FileResponse(f"user_images/pfp/{username}", media_type='image/gif')
    else:
        # Returns default image if none is uploaded
        return FileResponse(f'{assets_folder}/default_pfp.png', media_type='image/gif')

@app.get("/get_banner/{username}")
async def get_banner(username: str):
    # Checks if the user has a profile pic uploaded
    if os.path.isfile(f"user_images/banner/{username}"):
        return FileResponse(f"user_images/banner/{username}", media_type='image/gif')
    else:
        # Returns default image if none is uploaded
        return FileResponse(f'{assets_folder}/default_banner.png', media_type='image/gif')
    
@app.post("/create_lif_account")
async def create_lif_account(request: Request):
    # Get POST data
    data = await request.json()
    username = data["username"]
    password = data["password"]
    email = data["email"]

    # Check username usage
    username_status = database.check_username(username)
    if username_status:
        raise HTTPException(status_code=409, detail="Username Already in Use!")

    # Check email usage
    email_status = database.check_email(email)
    if email_status:
        raise HTTPException(status_code=409, detail="Email Already in Use!")

    # Check if email is valid
    email_isValid = email_interface.is_valid_email(email)
    if not email_isValid:
        raise HTTPException(status_code=400, detail="Invalid Email!")

    # Hash user password
    password_hash = hasher.get_hash_gen_salt(password)

    # Create user account
    database.create_account(username=username, password=password_hash['password'], email=email, password_salt=password_hash['salt'])

    return {"Status": "Ok"}  

@app.get("/check_account_info_usage/{type}/{info}")
async def check_account_info_usage(type: str, info: str):
    if type == "username":
        # Check username usage
        username_status = database.check_username(info)
        if username_status:
            raise HTTPException(status_code=409, detail="Username Already in Use!")
        else:
            return {"Status": "Ok"}

    if type == "email":
        # Check email usage
        email_status = database.check_email(info)
        if email_status:
            raise HTTPException(status_code=409, detail="Email Already in Use!")
        else:
            return {"Status": "Ok"}

    if type == "emailValid":
        # Check if email is valid
        email_isValid = email_interface.is_valid_email(info)
        if not email_isValid:
            raise HTTPException(status_code=400, detail="Invalid Email!")
        else:
            return {"Status": "Ok"}

@app.get("/create_account/{username}/{email}/{password}")
async def create_account(username: str, email: str, password: str):
    # Check username usage
    username_status = database.check_username(username)
    if username_status:
        return {"status": "unsuccessful", "reason": "Username Already in Use!"}

    # Check email usage
    email_status = database.check_email(email)
    if email_status:
        return {"status": "unsuccessful", "reason": "Email Already in Use!"}

    # Check if email is valid
    email_isValid = email_interface.is_valid_email(email)
    if not email_isValid:
        return {"status": "unsuccessful", "reason": "Email is Invalid!"}

    # Hash user password
    password_hash = hasher.get_hash_gen_salt(password)

    # Create user account
    database.create_account(username=username, password=password_hash['password'], email=email, password_salt=password_hash['salt'])

    return {"status": "ok"}

@app.websocket('/lif_account_recovery')
async def account_recovery(websocket: WebSocket):
    await websocket.accept()

    # Stores email and code for later use
    user_email = None
    user_code = None

    # Wait for client to send data
    while True:
        data = await websocket.receive_json()

        # Check what kind of data the client sent
        if 'email' in data:
            # Check email with database
            if database.check_email(data['email']) == True:
                user_email = data['email']

                # Tell client email was received
                await websocket.send_json({"responseType": "emailSent", "message": "Email sent successfully."})
            else:
                # Tell client email is invalid
                await websocket.send_json({"responseType": "error", "message": "Invalid Email!"})
        else:
            await websocket.send_json({"responseType": "error", "message": "Bad Request"})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

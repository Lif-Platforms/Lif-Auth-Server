# -------------------------------
# Title: Main Unit Test
# Description: Responsible for testing all routes of Auth Server
# Date: 11/24/23
# -------------------------------

# Imports
import requests
from termcolor import colored
import json

# Format logging
class logger:
    def info(info):
        print(colored(f"INFO: {info}", "green"))

    def warn(warn):
        print(colored(f"WARN: {warn}", "yellow"))

    def error(error):
        print(colored(f"ERR: {error}", "red"))

# Ask tester for host information
auth_url = input('Enter Auth URL: ')

# Test depreciated login route
logger.info("Testing login (DEPRECIATED)...")

print("Please enter correct login credentials")

username = input("Username: ")
password = input("Password: ")

# Will be set once login is successful 
token = None

result = requests.get(url=f"{auth_url}/login/{username}/{password}")

# Check http status code
if result.status_code == 200:
    # Check request content
    content = json.loads(result.content.decode('UTF-8'))

    if content['Status'] == 'Successful':
        logger.info("✓ Test 1 PASSED!")
        token = content['Token']
    else:
        logger.error("X Test 1 FAILED!")
        quit()
else:
    logger.error(f"X Test 1 FAILED! Status Code: {str(result.status_code)}")
    quit()

# Test new Lif login
logger.info("Testing Lif login (NEW)...")

result = requests.post(url=f'{auth_url}/lif_login', data={'username': username, 'password': password})

# Check http status code
if result.status_code == 200:
    logger.info("✓ Test 2 PASSED!")

else:
    logger.error(f"X Test 2 FAILED! Status Code: {str(result.status_code)}")
    quit()

# Test avatar update
logger.info("Testing avatar update...")

file_path = input("Image Path (PNG): ")

result = requests.post(url=f"{auth_url}/update_pfp", data={'username': username, "token": token}, files={'file': open(file_path, "rb")})

# Check status of operation
if result.status_code == 200:
    content = json.loads(result.content.decode('UTF-8'))

    if content['Status'] == "Ok":
        logger.info("✓ Test 3 PASSED!")

    else:
        logger.error("X Test 3 FAILED!")
        quit()
else:
    logger.error(f"X Test 3 FAILED! Status Code: {str(result.status_code)}")
    quit()

# Test user banner update
logger.info("Testing user banner update...")

file_path = input("Image Path (PNG): ")

result = requests.post(url=f"{auth_url}/update_profile_banner", data={'username': username, "token": token}, files={'file': open(file_path, "rb")})

# Check status of operation
if result.status_code == 200:
    content = json.loads(result.content.decode('UTF-8'))

    if content['Status'] == "Ok":
        logger.info("✓ Test 4 PASSED!")

    else:
        logger.error("X Test 4 FAILED!")
        quit()
else:
    logger.error(f"X Test 4 FAILED! Status Code: {str(result.status_code)}")
    quit()

# Test account info update (Personalization)
logger.info("Testing account info update (Personalization)...")

print("Valid pronoun examples: 'he/him', 'she/her', 'they/them'")
pronouns = input("Enter Pronouns: ")

bio = input("Enter Bio: ")

result = requests.post(url=f"{auth_url}/update_account_info/personalization", data={'username': username, "token": token, "pronouns": pronouns, "bio": bio})

# Check status of operation
if result.status_code == 200:
    logger.info("✓ Test 5 PASSED!")

else:
    logger.error(f"X Test 5 FAILED! Status Code: {str(result.status_code)}")
    quit()

# Test get user bio
logger.info("Testing get user bio...")

result = requests.get(url=f"{auth_url}/get_user_bio/{username}")

# Check status of operation
if result.status_code == 200:
    logger.info("✓ Test 6 PASSED!")

else:
    logger.error(f"X Test 6 FAILED! Status Code: {str(result.status_code)}")
    quit()

# Test get user pronouns
logger.info("Testing get user pronouns...")

result = requests.get(url=f"{auth_url}/get_user_pronouns/{username}")

# Check status of operation
if result.status_code == 200:
    logger.info("✓ Test 6 PASSED!")

else:
    logger.error(f"X Test 7 FAILED! Status Code: {str(result.status_code)}")
    quit()

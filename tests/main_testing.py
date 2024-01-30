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

# Keep track of test number
test_number = 1

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
        logger.info(f"✓ Test {str(test_number)} PASSED!")
        token = content['Token']
    else:
        logger.error(f"X Test {str(test_number)} FAILED! Status: {content['Status']}")
        quit()
else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")
    quit()

test_number += 1

# Test new Lif login
logger.info("Testing Lif login (NEW)...")

result = requests.post(url=f'{auth_url}/lif_login', data={'username': username, 'password': password})

# Check http status code
if result.status_code == 200:
    logger.info(f"✓ Test {str(test_number)} PASSED!")

else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")
    quit()

test_number += 1

# Test avatar update
logger.info("Testing avatar update...")

file_path = input("Image Path (PNG): ")

result = requests.post(url=f"{auth_url}/update_pfp", data={'username': username, "token": token}, files={'file': open(file_path, "rb")})

# Check status of operation
if result.status_code == 200:
    content = json.loads(result.content.decode('UTF-8'))

    if content['Status'] == "Ok":
        logger.info(f"✓ Test {str(test_number)} PASSED!")

    else:
        logger.error(f"X Test {str(test_number)} FAILED!")
        quit()
else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")
    quit()

test_number += 1

# Test user banner update
logger.info("Testing user banner update...")

file_path = input("Image Path (PNG): ")

result = requests.post(url=f"{auth_url}/update_profile_banner", data={'username': username, "token": token}, files={'file': open(file_path, "rb")})

# Check status of operation
if result.status_code == 200:
    content = json.loads(result.content.decode('UTF-8'))

    if content['Status'] == "Ok":
        logger.info(f"✓ Test {str(test_number)} PASSED!")

    else:
        logger.error(f"X Test {str(test_number)} FAILED!")
        quit()
else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")
    quit()

test_number += 1

# Test account info update (Personalization)
logger.info("Testing account info update (Personalization)...")

print("Valid pronoun examples: 'he/him', 'she/her', 'they/them'")
pronouns = input("Enter Pronouns: ")

bio = input("Enter Bio: ")

result = requests.post(url=f"{auth_url}/update_account_info/personalization", data={'username': username, "token": token, "pronouns": pronouns, "bio": bio})

# Check status of operation
if result.status_code == 200:
    logger.info(f"✓ Test {str(test_number)} PASSED!")

else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")
    quit()

test_number += 1

# Test get user bio
logger.info("Testing get user bio...")

result = requests.get(url=f"{auth_url}/get_user_bio/{username}")

# Check status of operation
if result.status_code == 200:
    logger.info(f"✓ Test {str(test_number)} PASSED!")

else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")
    quit()

test_number += 1

# Test get user pronouns
logger.info("Testing get user pronouns...")

result = requests.get(url=f"{auth_url}/get_user_pronouns/{username}")

# Check status of operation
if result.status_code == 200:
    logger.info(f"✓ Test {str(test_number)} PASSED!")

else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")
    quit()

test_number += 1

# Test get account info
logger.info("Testing get account info...")

account = input("Enter Account Name: ")
access_token = input("Enter Auth Access Token: ")

result = requests.get(url=f"{auth_url}/get_account_info/email/{account}",
                      headers={"access-token": access_token}
                      )

# Check operation status
if result.status_code == 200:
    logger.info(f"✓ Test {str(test_number)} PASSED!")
else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")

test_number += 1

# Test token verification
logger.info("Testing token verification (DEPRECIATED)...")

result = requests.get(url=f"{auth_url}/verify_token/{username}/{token}")

# Check operation status
if result.status_code == 200:
    # Decode request body
    content = json.loads(result.content.decode('UTF-8'))

    if content['Status'] == "Successful":
        logger.info(f"✓ Test {str(test_number)} PASSED!")
    else:
        logger.error(f"X Test {str(test_number)} FAILED! Status: {content['Status']}")
else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")

test_number += 1

# Test avatars 
logger.info("Testing avatars...")

result = requests.get(f"{auth_url}/get_pfp/{username}")

if result.status_code == 200:
    logger.info(f"✓ Test {str(test_number)} PASSED!")
else:
    logger.error(f"X Test {str(test_number)} FAILED! Status Code: {str(result.status_code)}")

# Authentication
Authentication is how our users log into the service. Auth Server provided a centralized way to log into any Lif Platforms service with one account. This eliminates the need to create an account for each service as well as eliminates the hassle of building out a new system for each service. This page will go over the process that users take when logging into the service.

## Logging In
Users are directed to our centralized login page `my.lifplatforms.com/login` when logging into a service. Some services such as Ringer have their own login pages. These pages interface with Auth Server for the login process. Here are the steps that users take during the login process:

1. **Username/Password:** Users enter their username and password into the login form. This data is sent to Auth Server in the form of form data.

2. **Checking Credentials:** Lif Platforms uses hashing for storing passwords for enhanced security. When checking credentials, Auth Server grabs the username, password hash, and salt from our database. Then, we use the database salt to hash the password provided in the form data. If both usernames and both password hashes are the same, the login succeeds. If not, the login fails.

3. **2-Factor Authentication:** If the user has this feature enabled, an additional step will be required for a successful login. If the username and password checks succeed, but the user has 2FA set up, the authentication will fail with a 401 status code. The server will also return a custom error code indicating the reason for the failure. In the case of 2FA, the error code is: `INVALID_2FA_CODE`. When this happens, the user will need to supply a one-time code for the login to succeed.

4. **Roles & Permissions:** Additional roles and permission nodes can be supplied in the query parameters of the login route. These give Auth Server additional requirements beyond just a successful login. Services can supply a role or list of permission nodes that the user needs to have in order for the login to succeed. This can be used for services that need special permission to access such as internal tools or sites.

5. **Data Return:** After a successful login, Auth Server returns with information that is used for authentication with our services. The data that returns depends on the system being used. These systems are the [JWT System](#jwt-system) and the [Username & Token](#username--token-system) system.

## JWT System
Coming Soon

## Username & Token System
> [!IMPORTANT]
> Lif Platforms is moving away from this system in favor of the new JWT system.

Auth Server uses a username and token system for authentication. After a successful login, Auth Server will return a username and token. The users token is assigned to the user at account creation and rarely changes. When the user wants to authenticate with a service, the client will supply their username and token to the service. The service will then talk to Auth Server to verify the users credentials (the username & token). If successful, the service continues normally. If not, the service will return a 401 status code.
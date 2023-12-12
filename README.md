<h1 align="center">🔐 Lif Authentication Server</h1>
<p align="center">Lif Auth Server is a server for validating logins for Lif Accounts</p>
<div align="center">
  <img alt="Docker Pulls" src="https://img.shields.io/docker/pulls/superior125/lifauthserver?style=for-the-badge">
  <img alt="GitHub issues" src="https://img.shields.io/github/issues/Lif-Platforms/Lif-Auth-Server?style=for-the-badge">
  <img alt="GitHub contributors" src="https://img.shields.io/github/contributors/Lif-Platforms/Lif-Auth-Server?style=for-the-badge">
  <img alt="Codacy grade" src="https://img.shields.io/codacy/grade/b6b940a8aa894b11864e9eff23826c25?style=for-the-badge">
</div>

# 📃 In Detail...
Lif Authentication Server is a server used by Lif to do various tasks regarding Lif accounts. The server can be used for the following:
 - Authenticating user logins
 - Authenticating user actions on services
 - Managing user Lif accounts (pfp, account info, etc.)

# 🔧 How It Works
There are two big parts of the Lif Auth Server. Those are user logins and authenticating user actions.

### User Logins
When a user wants to log into a Lif service they must go through the Lif Auth Server. Here are the steps taken when a user logs in. 
1. The service makes a request to the Lif Auth Server
2. The Lif Auth Server verifies the credentials with the database
3. The Lif Auth Server replies to the service with the status of the operation and (if successful) the user token

### User Actions
When a user executes an action that requires authentication, there are a few steps that are taken.
1. The service makes a request to the Lif Auth Server with the username and token
2. The Lif Auth Server verifies the token with the database. The token must correspond to the account it's for otherwise the verification fails.
3. The Lif Auth Server replies to the service with the status of the verification.

### User Data Retrival 
User data retrieval is usually done by a service. This is for sensitive info in Lif Accounts that the service needs access to. The service will access the data using an access control token. Lif can manage the permissions of these tokens to determine what data they have access to. Here's how it works.
1. The service makes a request to the Lif Auth Server with its access token.
2. Lif Auth Server will look at its local configuration to determine if the access token is valid and if they have permission to access the data it is requesting.
3. Lif Auth Server will reply with the status of the operation and the data the server requested. 

# 👋 HELP WANTED
Lif Platforms is looking for contributors for Ringer and other services from Lif. If you are interested please reach out at: Lif.Platforms@gmail.com

# 🙋‍♂️ Our Team 
<a href="https://github.com/Lif-Platforms/Lif-Auth-Server/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=Lif-Platforms/Lif-Auth-Server" />
</a>

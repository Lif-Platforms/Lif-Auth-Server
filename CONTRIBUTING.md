<h1 align="center">🤝 Auth Server Contributing Guidlines</h1>
<p align="center">This document provides guidelines and best practices for contributing to the Lif Platforms Auth Server project. The Auth Server is a RESTful API that handles authentication and authorization for the Lif Platforms ecosystem. It is built using Python and the FastAPI framework and relies on MySQL as the database backend.</p>

# Before you start
- Make sure you have Python 3.9 or higher installed on your system, along with pip and virtualenv.
- Clone the repository from GitHub and create a virtual environment for the project.
- Install the dependencies using `pip install -r requirements.txt`.
- Read the [code of conduct](CODE_OF_CONDUCT.md) and [license](LICENSE) files.

# Seting Up For Development
1. **Create A Logs File** - Create a file named `/logs/logfile.log` in the root directory of the project.
2. **Setup The Database** - Setup a new MySQL database and import our [base database](https://drive.google.com/drive/folders/1hElqxbTORPwX9QQsDuao80grOXnZNWo0?usp=sharing) into it.
3. **Configure Credentials** - Start Auth Server and wait for it to start. Once started, stop Auth Server. You should now see a `config.yml` in the project's root directory. There you can configure the credentials for your MySQL database and other things.
4. That's it! You have successfully set up Auth Server for development.

# How to contribute
- Create a new branch from the `main` branch and name it according to the feature or bug you are working on.
- Write clear and concise commit messages that explain what you have done and why.
- Write documentation for your code using docstrings and comments, following the [Google style guide](https://google.github.io/styleguide/pyguide.html).
- Push your branch to GitHub and create a pull request against the `main` branch.
- Wait for the code review and address any feedback or suggestions.
- Once your pull request is approved and merged, delete your branch.

Thank you for your interest in contributing to the Lif Platforms Auth Server project. We appreciate your help in making it better and more secure.

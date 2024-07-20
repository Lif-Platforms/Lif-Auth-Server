<h1 align="center">🤝 Auth Server Release Checklist</h1>
<p align="center">A Checklist for publishing new Auth Server Releases.</p>

## 1 - Code Works Locally
Before publishing a release, all code for Auth Server should work locally on your machine. This means that all routes should work as intended with no errors.

## 2 - Code Works In Docker
Lif Platforms uses [Docker](https://www.docker.com/) for deployment and hosting. This means that all code for Auth Server should be tested to ensure it works inside a Docker container.

## 3 - Version Number Is Up-To-Date
Prior to every Auth Server release, the version number in [_version.py](https://github.com/Lif-Platforms/Lif-Auth-Server/blob/main/src/_version.py) should match the one for the release.
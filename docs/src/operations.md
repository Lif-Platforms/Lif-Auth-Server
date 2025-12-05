# Operations
The Operations section provides a practical guide to running, maintaining, and troubleshooting the Auth Server. While the Overview and Architecture pages explain *what* the system does, this section focuses on *how* to keep it healthy and secure in day‑to‑day use.

## Containerization
Auth Server is intended to run inside a Docker container. This has a few benefits.

1. **Isolation:** Ensures that any problems with the software only affect the container and don't affect the rest of the system.

2. **Security:** If a bad actor manages to gain access to the container where Auth Server is running, they will only be able to access what's inside the container and will be cut off from the rest of the system. This will "contain the blast" and prevent harm to other services or the machine itself.

3. **Ease of Setup:** Hosting inside a Docker container makes setup a breeze. Everything you need to run Auth Server is already bundled inside of the Docker image.

4. **Ease of Updates:** We use Docker in combination with WatchTower. This tool automatically checks for updates, downloads the latest image, and recreates the container with the new image.

## Container Setup
In this section, we will learn how to setup the Docker container to run Auth Server.

### Preparation
Before we create our container, there are a few things we need to do. First, create a new folder for you container. This will contain all the files necessary for Auth Server to run. Inside that folder, create the following files:

- config.yml
- access-control.yml

Then create the following directories:

- user_images/pfp
- user_images/banner
- logs

Your final folder structure should look like this:
```
auth-server/
├── config.yml
├── access-control.yml
├── user_images/
│   ├── pfp/
│   └── banner/
└── logs/
```

### Docker Compose
For creating and setting up the container, we recommend using [Docker Compose](https://docs.docker.com/compose/). This will make it easy to maintain in the future. In order to setup your `docker-compose.yml` file, you will need the following:

1. **Image:** superior125/lifauthserver:latest

2. **Ports:** Auth Server runs on port `8002`. You will need to map an external port into your container to access Auth Server.

3. **Volumes:** For Auth Server to run, you will need the following volumes mounted:
    - ./config.yml
    - ./access-control.yml
    - ./user_images/pfp
    - ./user_images/banner
    - ./logs

4. **Environment:** We reccomend setting the `RUN_ENVIRONMENT` variable to tell Auth Server when environment it it running in. If you are running in production, you must set this to `PRODUCTION`. If you are running in a dev environment, you can set this to `DEVELOPMENT` or just not set it at all.

Below is an example of what your `docker-compose.yml` could look like:
```yml
services:
  web:
    image: superior125/lifauthserver:latest
    container_name: lif-auth-server # Optional but recommended
    environment:
      RUN_ENVIRONMENT: PRODUCTION
    ports:
      - "8002:8002"
    volumes:
      - ./config.yml:/config.yml
      - ./access-control.yml:/access-control.yml
      - ./user_images/pfp:/user_images/pfp
      - ./user_images/banner:/user_images/banner
      - ./logs:/logs
    restart: unless-stopped # Optional but recommended
```

## SSL
Auth Server doesn't natively support SSL/HTTPS. For production environments, we recommend putting Auth Server behind a reverse proxy. This will make the process of securing connections with Auth Server over the web significantly easier. We recommend using [Nginx](https://nginx.org/en/) for the reverse proxy and [CertBot](https://certbot.eff.org/) for SSL certificates. Both are free tools.
# Operations
The Operations section provides a practical guide to running, maintaining, and troubleshooting Auth Server. While the Overview and Architecture pages explain *what* the system does, this section focuses on *how* to keep it healthy and secure in day‑to‑day use.

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

## Config.yml
The `config.yml` file is used for configuring Auth Server. In this section, we will go over the configuration options and what they do. Here is an example config file:

```yml
allow-origins:
- '*'
mail-service-token: Token Here
mail-service-url: Url Here
mailjet-api-key: API Key Here
mailjet-api-secret: API Secret Here
mysql-cert-path: cert.pem
mysql-database: Database Here
mysql-host: Host Here
mysql-password: Password Here
mysql-port: Port Here
mysql-ssl: true
mysql-user: Username Here
```

Lets dive deeper into each option and explore what it does.

- **allow-origins:** This option configures the allowed origins for CORS. This is a browser enforced policy that controls what hosts are allowed to access this resource. Here we've set it to allow all origins.

- **mail-service-token:** This is the access token needed to interface with Mail Service. This service handles communication to users via email. This service is being phased out and replaced with MailJet.

- **mail-service-url:** This is the URL Auth Server should use to access Mail Service.

- **mailjet-api-key & mailjet-api-secret:** These are the configuration options for setting the API key for the MailJet API. We use this API to communicate with customers via email.

- **mysql-cert-path:** Local path for the certificate file for MySQL SSL connections. This option is ignored if SSL is disabled.

- **mysql-database:** This is the database that Auth Server will use to store and access data.

- **mysql-host:** Host configuration for the MySQL server used by Auth Server.

- **mysql-password:** Password to the MySQL user assigned to Auth Server.

- **mysql-port:** Port the MySQL Server is hosted on. Defaults to 3306.

- **mysql-ssl:** Tells Auth Server whether or not to use SSL when connecting to MySQL.

- **mysql-user:** MySQL user assigned to Auth Server.
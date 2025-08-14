import os
import yaml

def init_config():
    """"
    Initializes the config with all default configuration options.
    """
    # Create config file if it does not exist
    if not os.path.isfile("config.yml"):
        with open("config.yml", 'x') as config:
            config.close()

    # Load the existing config
    with open("config.yml", "r") as config:
        contents = config.read()
        configurations = yaml.safe_load(contents)
        config.close()

    # Ensure the configurations are not None
    if configurations == None:
        configurations = {}

    # Define a default config
    defaultConfig = {
        "allow-origins": ["*"],
        "mysql-host": "localhost",
        "mysql-port": 3306,
        "mysql-user": "root",
        "mysql-password": "test123",
        "mysql-database": "Lif_Accounts",
        "mysql-ssl": False,
        "mysql-cert-path": "INSERT PATH HERE",
        "mail-service-token": "INSERT TOKEN HERE",
        "mail-service-url": "INSERT URL HERE",
        "mailjet-api-key": "INSERT KEY HERE",
        "mailjet-api-secret": "INSERT SECRET HERE"
    }

    # Compare config with json data
    for option in defaultConfig:
        if not option in configurations:
            configurations[option] = defaultConfig[option]

    # Open config in write mode to write the updated config
    with open("config.yml", "w") as config:
        new_config = yaml.safe_dump(configurations)
        config.write(new_config)
        config.close()

def get_key(key: str):
    """
    Gets a key value from the config.
    Parameters:
        key (str): The key to get the value of.
    Returns:
        Value of the key.
    """
    with open("config.yml", "r") as config:
        content: dict = yaml.safe_load(config)

        if key in content:
            return content[key]
        else:
            return None
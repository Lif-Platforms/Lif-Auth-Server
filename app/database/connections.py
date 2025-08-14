from mysql.connector import connect, ClientFlag
from app.config import get_key

def get_connection():
    mysql_configs = {
        "host": get_key('mysql-host'),
        "port": get_key('mysql-port'),
        "user": get_key('mysql-user'),
        "password": get_key('mysql-password'),
        "database": get_key('mysql-database'), 
    }

    # Check if SSL is enabled
    if get_key('mysql-ssl'):
        # Add ssl get_key( to connection
        mysql_configs['client_flags'] = [ClientFlag.SSL]
        mysql_configs['ssl_ca'] = get_key('mysql-cert-path')

    conn = connect(**mysql_configs)
    return conn

# MySQL Database Configuration
class Config(object):
    db_jdbc_url = "mysql://localhost:3306/clm"
    db_username = "unravel"
    db_password = "unraveldata"

    # Rev-this up after every GA
    UNRAVEL_VERSION_LATEST = "4.5.5.0"

    UNRAVEL_VERSION_TO_TAR = {
        "4.5.5.0": "http://127.0.0.1/unravel-4.5.5.0.tar.gz"
    }

    UNRAVEL_MYSQL_VERSION = "5.7"

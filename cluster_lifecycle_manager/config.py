class Config(object):
    # Rev-this up after every GA
    UNRAVEL_VERSION_LATEST = "4.5.5.0"
    UNRAVEL_VERSION_TO_TAR = {
        "4.5.5.0": "http://127.0.0.1/unravel-4.5.5.0.tar.gz"
    }
    UNRAVEL_MYSQL_VERSION = "5.7"

    # Create Nodes and Clusters for up to this many hours by default
    DEFAULT_TTL_HOURS = 72
    FREE_TRIAL_TTL_HOURS = 168 # 7 days

    # Limits on resources
    MAX_ALLOWED_ACTIVE_NODES = 100
    MAX_ALLOWED_ACTIVE_CLUSTERS = 50
    MAX_ACTIVE_FREE_TRIALS_PER_COMPANY = 10
    MAX_ACTIVE_FREE_TRIALS_PER_EMAIL = 5
    MAX_REQUESTS_PER_MIN = 10

# Python standard-library imports
import sys
import os
import logging

# Third Party imports (sorted alphabetically)
from flask import Flask

# Local imports
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

# Start of flask app, http://127.0.0.1:5000/
app = Flask("app")

# Can now access like so: app.config["DEBUG"]
# It looks for config.py inside of the ./app/ directory
app.config.from_pyfile("config.py")
app.logger.setLevel(logging.INFO)

# Import the views, which in turn needs to import the models.
from saas.webapp.app.views import *

# Register the custom filters
from saas.webapp.app.util import filters

if __name__ == "__main__":
    print("Debug is set to {}".format(app.config["DEBUG"]))
    print("Base Dir is set to {}".format(app.config["BASE_DIR"]))
    app.run()

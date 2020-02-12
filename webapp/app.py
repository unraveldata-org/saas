# Python standard-library imports
import sys
import os
import json
from datetime import datetime, timedelta
import traceback
import logging

# Third Party imports (sorted alphabetically)
# https://pypi.org/project/email-validator/
from email_validator import validate_email, EmailNotValidError

from flask import Flask, request, session, redirect, url_for, escape

# https://pypi.org/project/flask-request-validator/
from flask_request_validator import (PATH, GET, Param, Enum, Pattern, validate_params, AbstractRule)

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Local imports
from webapp.manager import Manager

# Start of flask app, http://127.0.0.1:5000/
app = Flask(__name__)

# TODO, better logging
#logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s : %(message)s")
logger = logging.getLogger("WebApp")
logger.setLevel(logging.INFO)

# Console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)

logger.addHandler(ch)


manager = Manager()

#region Rules
class RuleEmail(AbstractRule):
    """
    Flask Request Validator that ensures an email is properly constructed.
    """

    def validate(self, value):
        """
        Validate the email. Return a list of error messages.
        :param value: Email value (str)
        :return: Return a list of human-readable errors found.
        """
        errors = []

        try:
            v = validate_email(value)  # validate and get info
            email = v["email"]  # replace with normalized form
        except EmailNotValidError as e:
            # email is not valid, exception message is human-readable
            errors.append(str(e))

        return errors
#endregion

#region Routes
@app.route("/")
def index():
    return "Unravel SaaS"


# http://127.0.0.1:5000/start_trial?first_name=Alejandro&last_name=Fernandez&company=Unravel&title=Engineer&email=alejandro@unraveldata.com&cloud_provider=EMR
# http://127.0.0.1:5000/start_trial?first_name=Alejandro&last_name=Fernandez&company=Unravel&title=Engineer&email=alejandro@unraveldata.com&cloud_provider=EMR&send_email=true
# http://127.0.0.1:5000/start_trial?first_name=Alejandro&last_name=Fernandez&company=Unravel&title=Engineer&email=alejandro@unraveldata.com&cloud_provider=EMR&send_email=False
@app.route("/start_trial", methods=["GET", "POST"])
@validate_params(
    Param("first_name", GET, str, required=True),
    Param("last_name", GET, str, required=True),
    Param("company", GET, str, required=True),
    Param("title", GET, str, required=True),
    Param("email", GET, str, required=True, rules=[RuleEmail()]),
    Param("cloud_provider", GET, str, required=True, rules=[Enum("EMR", "HDI", "GCP", "DATABRICKS_ON_AWS", "DATABRICKS_ON_AZURE")]),
    Param("send_email", GET, bool, required=False, default=lambda: False)
)
def start_trial(first_name, last_name, company, title, email, cloud_provider, send_email):
    """
    Start a free-trial of Unravel on the Cloud.
    :param first_name: First name (str)
    :param last_name: Last name (str)
    :param company: Company name (str)
    :param title: Job title (str)
    :param email: Email address (str)
    :param cloud_provider: Cloud Provider name (str)
    :param send_email: Whether to send an email after the cluster is created (bool)
    :return: Return a request id in order to track the progress.
    """
    # TODO
    ip = "127.0.0.1"
    response = {}

    # TODO, utilize send_email
    try:
        trial_request_id = manager.insert_trial_request(first_name, last_name, email, title, company, ip, cloud_provider)
        response = {
            "request_id": trial_request_id
        }
    except Exception as err:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = repr(traceback.extract_tb(exc_traceback))
        logger.error("Error: {}. Stack:\n{}".format(err, tb))
        response = {
            "error": str(err)
        }
    return json.dumps(response)


@app.route("/check_trial", methods=["GET"])
@validate_params(
    Param("request_id", GET, int, required=True)
)
def check_trial(request_id):
    """
    Check the progress of the request to start a free trial
    :param request_id: Request id (int)
    :return: Return metadata about the overall request and the cluster info.
    """
    # TODO, implement this, should check the status of the node_spec and maybe cluster_spec associated with that id.
    app.logger.info("Processing request for id {}".format(request_id))

    response = {}

    # TODO, this will be a more complex object comprising of info about the trial, node, and maybe cluster.
    trial = manager.get_trial_by_id(request_id)

    if trial is not None:
        response = {
            "request_id": request_id,
            "state": trial.state,
            "cluster": {
                "cloud_provider": trial.cloud_provider,
                "headnode_ip": "",
                "unravel_ip": "",
                "expiration": str(datetime.utcnow())
            }
        }
    return json.dumps(response, default=str)
#endregion


if __name__ == "__main__":
    app.run()

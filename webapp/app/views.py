# Python standard library imports
import sys
import json
from datetime import datetime, timedelta
import traceback

# Third-party imports
# https://pypi.org/project/flask-request-validator/
from flask_request_validator import (PATH, GET, Param, Enum, Pattern, validate_params)
from flask import request, session, redirect, url_for, escape
from flask import render_template

# Local imports
from ..run import app
from .util.rules import RuleEmail
from . import manager
from .helpers.constants import Conversion

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/resources")
def resources():
    nodes = manager.get_relevant_nodes()
    # Generate a dictionary from each state to the number of occurrences
    states = [node.state for node in nodes]
    state_counts = {s: states.count(s) for s in states}
    return render_template("resources.html", nodes=nodes, state_counts=state_counts)


@app.route("/request")
def request():
    return render_template("request.html")


@app.route("/trials", methods=["GET"])
@validate_params(
    Param("start_date_epoch_sec", GET, int, required=False, default=lambda: 0)
)
def trials(start_date_epoch_sec):
    """
    Get all active and relevant trials.
    :param start_date_epoch_sec: Optional, start date in epoch secs.
    :return: Render the trials.html page.
    """
    if start_date_epoch_sec > 0:
        start_date = Conversion.unix_time_sec_to_dt(start_date_epoch_sec)
    else:
        start_date = datetime.utcnow() - timedelta(days=7)

    trials = manager.get_relevant_trials(start_date)

    # Generate a dictionary from each state to the number of occurrences
    states = [trial.state for trial in trials]
    state_counts = {s: states.count(s) for s in states}
    return render_template("trials.html", start_date=start_date, trials=trials, state_counts=state_counts)


@app.route("/health")
def health():
    app.logger.info("Health Check")
    return "Unravel SaaS"


# E.g., http://127.0.0.1:5000/start_trial?first_name=Alejandro&last_name=Fernandez&company=Unravel&title=Engineer&email=alejandro@unraveldata.com&cloud_provider=EMR&send_email=true
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
    response = {}

    try:
        headers_list = request.headers.getlist("X-Forwarded-For")
        ip = headers_list[0] if headers_list else request.remote_addr

        # This workflow will not create a cluster since the user has to bring their own.
        trial_request_id = manager.insert_trial_request(first_name, last_name, email, title, company, ip,
                                                        cloud_provider, create_cluster=False, send_email=send_email)
        response = {
            "request_id": trial_request_id
        }
    except Exception as err:
        exc_type, exc_value, exc_traceback = sys.exc_info()
        tb = repr(traceback.extract_tb(exc_traceback))
        app.logger.error("Error: {}. Stack:\n{}".format(err, tb))
        response = {
            "error": "Unable to start free trial. Error: {}".format(err)
        }
    return json.dumps(response)


# E.g., http://127.0.0.1:5000/check_trial?request_id=1
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
    else:
        response = {
            "error": "Unable to find trial request with ID {}".format(request_id)
        }
    return json.dumps(response, default=str)

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

    dashboards = {"Dashboards":
        [
            {"section": "node",
             "type": "pie",
             "title": "Nodes with States",
             "description": "Group the Nodes by their states.",
             "series_name": "Node State",
             "legend": {
                     "launched": {
                         "label": "Launched",
                         "color": "blue"
                     },
                     "ready": {
                         "label": "Ready",
                         "color": "green"
                     },
                     "expired": {
                         "label": "Expired",
                         "color": "orange"
                     },
                     "deleted": {
                         "label": "Deleted",
                         "color": "red"
                     }
            },
            "data": {
                    "launched": 1,
                    "ready": 2,
                    "expired": 3,
                    "deleted": 4
                }
            },

            {"section": "trial",
             "type": "solidgauge",
             "title": "Active Trials",
             "description": "Number of Active Trials.",
             "series_name": "Active Trials",
             "legend": {
                 "min_color": "#DF5353",      # red
                 "center_color": "#DDDF0D",   # yellow
                 "max_color": "#55BF3B"       # green
             },
             "data": {"min": 0, "max": 10, "value": 3}
            },
        ]
    }
    dashboard_json = json.dumps(dashboards)
    return render_template("index.html", dashboard_json=dashboard_json)


@app.route("/resources")
@validate_params(
    Param("status", GET, str, required=False, default=lambda: None),
    Param("msg", GET, str, required=False, default=lambda: None)
)
def resources(status, msg):
    """
    For each type of resource (node, cluster), show a list of the available/relevant ones.
    If got to this page via a redirect from /manage_resource, then will have a status and msg variable
    indicating if was able to perform that action.
    :param status: Optional, status as either "success" or "error".
    :param msg: Optional, message to show based on the last action.
    """
    nodes = manager.get_relevant_nodes()
    # Generate a dictionary from each state to the number of occurrences
    node_states = [node.state for node in nodes]
    node_state_counts = {s: node_states.count(s) for s in node_states}

    clusters = manager.get_relevant_clusters()
    # Generate a dictionary from each state to the number of occurrences
    cluster_states = [cluster.state for cluster in clusters]
    cluster_state_counts = {s: cluster_states.count(s) for s in cluster_states}
    return render_template("resources.html", status=status, msg=msg,
                           nodes=nodes, node_state_counts=node_state_counts,
                           clusters=clusters, cluster_state_counts=cluster_state_counts)

# http://127.0.0.1:5000/manage_resource?resource_type=cluster&resource_id=1&action=expire
@app.route("/manage_resource", methods=["GET"])
@validate_params(
    Param("resource_type", GET, str, required=True),
    Param("resource_id", GET, int, required=True),
    Param("action", GET, str, required=True),
    Param("extra_hours", GET, int, required=False, default=lambda: 0)
)
def manage_resource(resource_type, resource_id, action, extra_hours):
    """
    Manage a resource by either extending its TTL or expiring it with the current time.
    :param resource_type: Resource type is either "cluster" or "node"
    :param resource_id: Resource ID is the int primary key
    :param action: Action is either "extend" or "expire"
    :param extra_hours: If the action is to "extend", then this is the numbre of hours to increase the expiration time
    from the current value.
    """
    status, msg = manager.change_resource_ttl(resource_type, int(resource_id), action, extra_hours)
    return redirect(url_for("resources", status=status, msg=msg))


@app.route("/provision", methods=["GET"])
def provision():
    now = datetime.utcnow()
    curr_epoch_sec = Conversion.dt_to_unix_time_sec(now)
    cluster_name_suffix = "-{}".format(curr_epoch_sec)
    return render_template("provision.html", cluster_name_suffix=cluster_name_suffix)

# The request.html page has a form to create a cluster.
# The parameters can be very dynamic depending on the cloud_provider
@app.route("/create_cluster", methods=["GET"])
def create_cluster():
    cloud_provider = request.args.get("cloud_provider")
    region = request.args.get("region")
    stack_version = request.args.get("stack_version")
    cluster_type = request.args.get("cluster_type")
    cluster_name = request.args.get("cluster_name")
    head_node_type = request.args.get("head_node_type")
    num_head_nodes = request.args.get("num_head_nodes")
    worker_node_type = request.args.get("worker_node_type")
    num_worker_nodes = request.args.get("num_worker_nodes")

    # Will be a CSV that we have to parse
    services = request.args.get("services", "")

    print("Cloud Provider: {}".format(cloud_provider))
    print("Region: {}".format(region))
    print("Stack Version: {}".format(stack_version))
    print("Cluster Type: {}".format(cluster_type))
    print("Cluster Name: {}".format(cluster_name))
    print("Head Node Type: {}".format(head_node_type))
    print("Num Head Nodes: {}".format(num_head_nodes))
    print("Worker Node Type: {}".format(worker_node_type))
    print("Num Worker Nodes: {}".format(num_worker_nodes))
    print("Services: {}".format(services))

    response = manager.insert_cluster_request(cloud_provider, region, stack_version, cluster_type, cluster_name,
                                              head_node_type, num_head_nodes, worker_node_type, num_worker_nodes,
                                              services)

    status = response["status"]
    object_id = response["cluster_spec_id"]

    return redirect(url_for("check_request", type="cluster", id=object_id))


'''
Check the request to provision a node or cluster
E.g., http://127.0.0.1:5000/check_request?type=cluster&id=1
'''
@app.route("/check_request", methods=["GET"])
def check_request():
    type = request.args.get("type")
    object_id = request.args.get("id")

    response = manager.check_resource(type, object_id)

    # These should always be available
    # TODO, add to a lightweight model
    status = response["status"]
    state = response["state"] if "state" in response else None
    cloud_provider = response["cloud_provider"] if "cloud_provider" in response else None
    date_requested = response["date_requested"] if "date_requested" in response else None
    error_message = response["error_message"] if "error_message" in response else None

    object_url = None

    # Note that provision_result.html is called from 2 different routes
    return render_template("provision_result.html", type=type,
                           status=status,
                           object_id=object_id,
                           object_state=state,
                           object_cloud_provider=cloud_provider,
                           object_date_requested=date_requested,
                           object_url=None,
                           error_message=error_message)

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

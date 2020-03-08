# Python standard library imports
import sys
import os
from datetime import datetime, timedelta
import logging

# Third-party imports

# Local imports
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

from saas.db.models import DBRunner, TrialRequest, NodeSpec, Node, ClusterSpec, Cluster


class Manager(object):
    """
    Manager that connects to the database.
    """
    logger = logging.getLogger("Manager")
    logger.setLevel(logging.INFO)

    # Console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    def __init__(self):
        """
        Initialize the manager and connect to the database.
        """
        self.session, self.engine = None, None

        self._connect_to_db()

    def _connect_to_db(self):
        """
        Connect to the MySQL database.
        """
        DBRunner.DEBUG = False
        self.session, self.engine = DBRunner.setup_session(DBRunner.get_unravel_jdbc_url())
        self.logger.info("Connected to the DB successfully")

    def get_active_trials(self):
        """
        Get all currently active trials.
        :return: Return a list of TrialRequest objects.
        """
        self.logger.info("Getting all active trials")
        trials = TrialRequest.get_all_pending()
        return trials

    def get_relevant_trials(self, start_date):
        """
        Get all currently active trials or created after the start date.
        :param start_date: Python DateTime object of the start date.
        :return: Return a list of TrialRequest objects.
        """
        self.logger.info("Getting all relevant trials since {}".format(start_date))
        trials = TrialRequest.get_by_states_or_after_datetime([TrialRequest.State.PENDING], start_date)
        return trials

    def get_relevant_nodes(self):
        """
        Get all active Nodes
        :return: Return a list of Node objects
        """
        self.logger.info("Getting all relevant nodes")
        nodes = Node.get_by_states([Node.State.LAUNCHED, Node.State.READY, Node.State.EXPIRED])
        return nodes

    def get_relevant_clusters(self):
        """
        Get all active Clusters
        :return: Return a list of Cluster objects
        """
        self.logger.info("Getting all relevant clusters")
        clusters = Cluster.get_by_states([Node.State.LAUNCHED, Node.State.READY, Node.State.EXPIRED])
        return clusters

    def check_resource(self, type, object_id):
        response = {
            "status": None,
            "cloud_provider": None, # obj property
            "state": None,          # obj property
            "date_requested": None, # obj property
            "object_url": None,
            "error_message": None
        }

        obj = None
        if type == "cluster":
            obj = ClusterSpec.get_by_id(object_id)
        elif type == "node":
            obj = NodeSpec.get_by_id(object_id)
        else:
            response["status"] = "error"
            response["error_message"] = "Unsupported type: {}".format(type)
            return response

        if obj is None:
            response["status"] = "error"
            response["error_message"] = "Unable to find {} with id {}".format(type, object_id)
        else:
            response["status"] = "success"
            response["cloud_provider"] = obj.get_cloud_provider()
            response["state"] = obj.get_state()
            response["date_requested"] = obj.get_date_requested()

        return response

    def insert_trial_request(self, first_name, last_name, email, title, company, ip, cloud_provider,
                             create_cluster=False, send_email=False):
        """
        Insert a TrialRequest object and return its id to track the progress.
        :param first_name: Customer first name (str)
        :param last_name: Customer last name (str)
        :param email: Customer email (str, should already be validated)
        :param title: Customer job title (str)
        :param company: Customer company name (str)
        :param ip: Customer IP address (str) used to issue the request, useful in detecting DDOS
        :param cloud_provider: Desired Cloud Provider name (str)
        :param create_cluster: Boolean indicating whether to create a cluster.
        :param send_email: Boolean indicating if should send an email once the node (and maybe the cluster) is ready.
        :return: Return the entity's ID if it was successful, otherwise, return None.
        """
        self.logger.info("Inserting a Trial Request. first_name: {}, last_name: {}, email: {}, title: {}, "
                         "company: {}, ip: {}, cloud_provider: {}, create_cluster: {}, send_email: {}".
            format(first_name, last_name, email, title, company, ip, cloud_provider, create_cluster, send_email))

        try:
            # If need to send an email, set "notify_customer" to "pending" meaning it is required after
            # the node and cluster are ready.
            notify_customer = "pending" if send_email else None
            trial = TrialRequest.create_if_not_exists(first_name, last_name, email, title, company, ip, cloud_provider,
                                                      create_cluster, notify_customer=notify_customer)
            trial.save()
            self.session.commit()
            return trial.id
        except Exception as err:
            self.logger.error("Unable to insert trial request. Error: {}".format(err))
        return None

    def get_trial_by_id(self, request_id):
        """
        Get the TrialRequest entity given its id if it exists, otherwise, return None.
        :param request_id: TrialRequest id (int)
        :return: Return the TrialRequest entity, or None.
        """
        trial = TrialRequest.get_by_id(request_id)
        return trial

    def insert_cluster_request(self, cloud_provider_name, region, stack_version, cluster_type, cluster_name,
                               head_node_type, num_head_nodes, worker_node_type, num_worker_nodes, services):
        """
        # TODO
        :param cloud_provider_name:
        :param region:
        :param stack_version:
        :param cluster_type:
        :param cluster_name:
        :param head_node_type:
        :param num_head_nodes:
        :param worker_node_type:
        :param num_worker_nodes:
        :param services:
        :return:
        """
        response = {"cluster_spec_id": None, "status": None, "error_message": None}

        self.logger.info("Inserting a Cluster Request. cloud_provider_name: {}, region: {}, stack_version: {}, "
                         "cluster_name: {}, head_node_type: {}, num_head_nodes:{}, worker_node_type: {}, num_worker_nodes: {}, "
                         "services: {}".
                         format(cloud_provider_name, region, stack_version, cluster_type, cluster_name,
                                head_node_type, num_head_nodes, worker_node_type, num_worker_nodes, services))

        user = "alejandro"
        os_family = None
        jdk = None
        storage = None
        bootstrap_action = None
        is_hdfs_ha = is_rm_ha = is_ssl = is_kerberized = False
        extra = None
        ttl_hours = 72

        try:
            # TODO, change user, add cluster name, TTL hours,
            cluster_spec = ClusterSpec.create_if_not_exists(cluster_name, cloud_provider_name, region, user,
                                                            num_head_nodes, head_node_type, num_worker_nodes, worker_node_type,
                                                            os_family, stack_version, cluster_type, jdk,
                                                            storage, services, bootstrap_action,
                                                            is_hdfs_ha, is_rm_ha, is_ssl, is_kerberized,
                                                            extra, ttl_hours, None)
            cluster_spec.save()
            self.session.commit()
            response["status"] = "success"
            response["cluster_spec_id"] = cluster_spec.id
        except Exception as err:
            self.logger.error("Unable to insert cluster_spec. Error: {}".format(err))
            response["status"] = "error"
            response["error_message"] = "Unable to create a ClusterSpec request. Check the logs for more details."

        return response

    def get_resource(self, resource_type, resource_id):
        resource = None
        if resource_type.lower() not in ["cluster"]:
            raise Exception("Invalid resource type: {}".format(resource_type))

        if resource_id is None or resource_id < 0:
            raise Exception("Invalid resource id: {}".format(resource_id))

        if resource_type.lower() == "cluster":
            resource = Cluster.get_by_id(resource_id)

        if resource is None:
            raise Exception("Could not find {} resource with id {}".format(resource_type, resource_id))

        return resource

    def change_resource_ttl(self, resource_type, resource_id, action, extra_hours):
        """
        Change a resource's TTL by either expiring it (setting ttl_hours to 0) or extending it by some positive value.
        :param resource: The resource type, which is either "cluster" or "node"
        :param resource_id: The resource ID PK.
        :param action: Action string ("expire", "extend")
        :param extra_hours: Optional. If extending, then extra_hours must be a positive integer.
        :return: Return a 2-tuple of <status (str), message (str)>
        """
        status = "success"
        msg = "Successfully updated resource TTL"

        try:
            resource = self.get_resource(resource_type, resource_id)

            if resource is None:
                raise Exception("Resource is None")

            if action.lower() not in ["extend", "expire"]:
                raise Exception("Invalid action value: {}, must be either 'extend' or 'expire'".format(action))

            if action.lower() == "extend" and extra_hours <= 0:
                raise Exception("When extending the lifetime, the extra hours must be a positive integer instead of {}".
                                format(extra_hours))

            if action.lower() == "expire":
                resource.set_ttl_hours(0)
            elif action.lower() == "extend":
                resource.set_ttl_hours(resource.ttl_hours + extra_hours)

            self.session.add(resource)
            self.session.commit()
        except Exception as err:
            status = "error"
            msg = str(err)
            self.logger.error("Unable to {} {} resource {}'s TTL. Error: {}".format(action, resource_type, resource_id, err))

        return status, msg

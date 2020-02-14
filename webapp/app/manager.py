# Python standard library imports
import sys
import os
from datetime import datetime, timedelta
import logging

# Third-party imports

# Local imports
root_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(root_dir)

from saas.db.models import DBRunner, TrialRequest, Node


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

    def get_relevant_trials(self, lookback_days):
        """
        Get all currently active trials or created within the last lookback_days
        :return: Return a list of TrialRequest objects.
        """
        self.logger.info("Getting all relevant trials in the last {} days".format(lookback_days))
        start_date = datetime.utcnow() - timedelta(days=lookback_days)
        trials = TrialRequest.get_by_states_or_after_datetime([TrialRequest.State.PENDING], start_date)
        return trials

    def get_relevant_nodes(self):
        """
        Get all active nodes
        :return: Return a list of Node objects
        """
        self.logger.info("Getting all relevant nodes")
        nodes = Node.get_by_states([Node.State.LAUNCHED, Node.State.READY, Node.State.EXPIRED])
        return nodes

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

# Python standard library imports
import sys
import os
import argparse
import logging
from datetime import datetime, timedelta
import time

# Third-party imports
from daemon import runner

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Local imports
from db.models import DBRunner, TrialRequest, NodeSpec, Node, ClusterSpec, Cluster
from db.config import Config as DBConfig
from cluster_lifecycle_manager.config import Config as CLMConfig
from cluster_lifecycle_manager.models.cloud_provider.cloud_provider import CloudProvider
from cluster_lifecycle_manager.models.cluster_spec_model import ClusterSpecModel
from cluster_lifecycle_manager.utils import Utils


APP_NAME = "unravel_clm"
APPLICATION = "Cluster LifeCycle Manager"

base_path = os.path.dirname(os.path.abspath(__file__))


class ClusterLifecycleManager(object):
    """
    Daemon to manage the lifecycle of nodes and Hadoop Clusters
    """
    logger = Utils.get_logger("ClusterLifecycleManager")

    LOOP_SLEEP_SECS = 10

    def __init__(self, args):
        self.stdin_path = "/dev/null"
        # TODO, use the proper /var/log and /var/run paths
        self.stdout_path = os.path.join(base_path, APP_NAME + ".out")
        self.stderr_path = os.path.join(base_path, APP_NAME + ".err")
        self.pidfile_path = os.path.join(base_path, APP_NAME + ".pid")
        self.pidfile_timeout = 5

        self.session, self.engine = None, None

    def _connect_to_db(self):
        """
        Connect to the MySQL database.
        """
        DBRunner.DEBUG = False
        self.session, self.engine = DBRunner.setup_session(DBRunner.get_unravel_jdbc_url())
        self.logger.info("Connected to the DB successfully")
        
    def _cleanup(self):
        pass

    def _is_new_trial_allowed(self, trial):
        """
        Determine if a new trial request is allowed given the current state of the system
        to prevent a denial of service attack.
        :param trial: TrialRequest object
        :return: Return a boolean indicating if this trial is allowed.
        """
        # Get the current number of active nodes and clusters
        # Ensure that the same email or company doesn't have more than x active requests.
        # Throttle all requests, so prevent a new one if received more than y in the last z minutes.
        allowed = True
        num_active_nodes = len(Node.get_by_states([Node.State.LAUNCHED, Node.State.READY, Node.State.EXPIRED]))

        # TODO, repeat similar logic for Clusters
        num_active_clusters = 0

        active_trials = TrialRequest.get_all_pending()
        active_trials_by_same_company = [t for t in active_trials if t.company.strip().lower() == trial.company.strip().lower()]
        active_trials_by_same_email = [t for t in active_trials if t.email.strip().lower() == trial.email.strip().lower()]

        # This includes requests in all states (even APPROVED and DENIED), since it could mean an attack, so
        # don't process any new requests except those by Unravel.
        total_requests_in_last_min = TrialRequest.get_num_created_after_datetime(datetime.utcnow() - timedelta(minutes=1))

        reason = ""
        if num_active_nodes > CLMConfig.MAX_ALLOWED_ACTIVE_NODES:
            allowed = False
            reason = "Number of active nodes {} exceeds limit of {}".format(num_active_nodes, CLMConfig.MAX_ALLOWED_ACTIVE_NODES)
        elif trial.company.strip().lower() != "unravel" and len(active_trials_by_same_company) > CLMConfig.MAX_ACTIVE_FREE_TRIALS_PER_COMPANY:
            allowed = False
            reason = "Company {} has {} active trials which exceeds limit of {}".\
                format(trial.company, len(active_trials_by_same_company), CLMConfig.MAX_ACTIVE_FREE_TRIALS_PER_COMPANY)
        elif not trial.email.strip().lower().endswith("@unraveldata.com") and len(active_trials_by_same_email) > CLMConfig.MAX_ACTIVE_FREE_TRIALS_PER_EMAIL:
            allowed = False
            reason = "Email {} has {} active trials which exceeds limit of {}".\
                format(trial.email, len(active_trials_by_same_email), CLMConfig.MAX_ACTIVE_FREE_TRIALS_PER_EMAIL)
        elif total_requests_in_last_min > CLMConfig.MAX_REQUESTS_PER_MIN:
            reason = "Total requests in last minute is {} which exceeds limit of {}".format(total_requests_in_last_min, CLMConfig.MAX_REQUESTS_PER_MIN)
            allowed = False

        if allowed is False:
            self.logger.warning("Denied trial request with ID {}. Reason: {}".format(trial.id, reason))
        return allowed

    def _check_for_free_trials(self):
        """
        Check for any new records in the trial_request table that indicate the need to create a NodeSpec
        and optionally a ClusterSpec.
        """
        new_trials = TrialRequest.get_all_pending()
        self.logger.info("There are {} pending trial requests.".format(len(new_trials)))

        # Example of how to create a node_spec for the pending request.
        for trial in new_trials:
            num_denied = 0
            try:
                if trial.cloud_provider not in CloudProvider.NAME.ALL:
                    trial.set_state(TrialRequest.State.DENIED)
                    trial.update()
                    self.session.commit()

                    error = "Trial request {} has cloud provider {} which is not supported.".format(trial.id, trial.cloud_provider)
                    raise Exception(error)

                node_type = "TODO"
                storage_config = "TODO"

                unravel_version = CLMConfig.UNRAVEL_VERSION_LATEST
                unravel_tar = CLMConfig.UNRAVEL_VERSION_TO_TAR[unravel_version]

                approved = self._is_new_trial_allowed(trial)

                if approved:
                    spec = NodeSpec.create_if_not_exists(cloud_provider=trial.cloud_provider, user="free_trial", node_type=node_type,
                                                         storage_config=storage_config, unravel_version=unravel_version,
                                                         unravel_tar=unravel_tar, mysql_version=CLMConfig.UNRAVEL_MYSQL_VERSION,
                                                         install_ondemand=False, extra=None, ttl_hours=CLMConfig.FREE_TRIAL_TTL_HOURS,
                                                         trial_request_id=trial.id)
                    spec.save()
                    trial.set_state(TrialRequest.State.APPROVED)
                    trial.update()

                    self.logger.info("Transitioned TrialRequest with ID {} from pending to approved by creating a NodeSpec. Trial Request: {} has NodeSpec: {}".
                        format(trial.id, trial, spec))
                else:
                    num_denied += 1
                    trial.set_state(TrialRequest.State.DENIED)
                    self.logger.info("Transitioned TrialRequest with ID {} from pending to denied due to potential attack.".
                                     format(trial.id))
                    trial.update()

                self.session.commit()
            except Exception as err:
                self.logger.error("Unable to process trial request with ID {}. Error: {}".format(trial.id, err))

            if num_denied > 0:
                self.logger.info("In this loop, denied {} trials.".format(num_denied))

    def _create_nodes_and_clusters(self):
        """
        Given any pending specs for Nodes and Clusters, actually provision them.
        """
        pending_node_specs = NodeSpec.get_all_pending()
        self.logger.info("There are {} pending Node Specs.".format(len(pending_node_specs)))

        for node_spec in pending_node_specs:
            try:
                self.logger.info("Analyzing Node Spec with ID {}".format(node_spec.id))
                node = Node.create_from_node_spec(node_spec)
                node.save()

                node_spec.set_state(NodeSpec.State.FINISHED)
                node_spec.update()
                self.session.commit()

                self.logger.info("Transitioned NodeSpec with ID {} from pending to finished by creating a Node. NodeSpec: {} has Node: {}".
                    format(node_spec.id, node_spec, node))
            except Exception as err:
                self.logger.error("Unable to launch Node for NodeSpec with ID {}".format(node_spec.id))

        # TODO, very similar to above
        pending_cluster_specs = ClusterSpec.get_all_pending()
        self.logger.info("There are {} pending Cluster Specs.".format(len(pending_cluster_specs)))

        for cluster_spec in pending_cluster_specs:
            try:
                self.logger.info("Analyzing Cluster Spec with ID {}".format(cluster_spec.id))

                cluster_spec_model = ClusterSpecModel.create_from_db_cluster_spec(cluster_spec)
                CloudProvider.resolve_spec(cluster_spec_model)
                cluster_spec_model.validate()

                # This actually instantiates the cluster on EMR/HDI/DataProc
                # TODO, we should try to mock this if possible.
                # id: j-2WVDA2NW2HRGP, request: 5432581b-bf55-4f91-823b-09359e080bf7
                cluster_id, _request_id = CloudProvider.create_cluster(cluster_spec_model)
                # cluster_id = "j-2WVDA2NW2HRGP"
                # _request_id = "5432581b-bf55-4f91-823b-09359e080bf7"

                cluster = Cluster.create_from_cluster_spec(cluster_spec)
                cluster.cluster_id = cluster_id
                cluster.save()

                cluster_spec.set_state(ClusterSpec.State.FINISHED)
                cluster_spec.update()
                self.session.commit()

                self.logger.info("Transitioned ClusterSpec with ID {} from pending to finished by creating a Cluster. ClusterSpec: {} has Cluster: {}".
                    format(cluster_spec.id, cluster_spec, cluster))
            except Exception as err:
                self.logger.error("Unable to launch Cluster for ClusterSpec with ID {}. Error: {}".format(cluster_spec.id, err))

    def _monitor_nodes_and_clusters(self):
        """
        Monitor the newly launched Nodes and Clusters and determine when they are pingable and ready to be delivered.
        This may involve notifying the customers with an email.
        """
        launched = Node.get_by_state(Node.State.LAUNCHED)
        for node in launched:
            # TODO, perform some sort of ping/health, and then update the record with the IP address.
            node.set_state(Node.State.READY)
            node.update()
            self.logger.info("Transitioning Node with ID {} from launched to ready. {}".format(node.id, node))
        self.session.commit()

    def _expire_nodes_and_clusters(self):
        """
        Find any nodes that have been marked as expired and actually delete them once removed from the Cloud Provider.
        Find any nodes that are candidates to expire and transition them into that state.
        """
        # The order matters, should first try to go from EXPIRED -> DELETED in this for-loop.
        expired = Node.get_by_state(Node.State.EXPIRED)
        self.logger.info("There are {} expired Nodes that have already been deleted by their respective Cloud Provider.".format(len(expired)))
        # TODO, perhaps in makes sense to group them based on the Cloud Provider to perform bulk-ops
        for node in expired:
            node.set_state(Node.State.DELETED)
            node.update()
            self.logger.info("Marking Node with ID {} as deleted".format(node.id))
            self.session.commit()

        # The next top-level loop will determine when these are deleted.
        ready_to_expire = Node.get_all_ready_to_expire()
        self.logger.info("There are {} Nodes ready to expire.".format(len(ready_to_expire)))
        for node in ready_to_expire:
            node.set_state(Node.State.EXPIRED)
            node.update()
            self.logger.info("Marking Node with ID {} as expired".format(node.id))
            self.session.commit()

    def run(self):
        """
        Main logic that runs continuously every 10 seconds.
        """
        self.logger.info("Starting {}".format(APPLICATION))
        try:
            self._connect_to_db()
            while True:
                self.logger.info("** Commencing loop again")
                start = datetime.utcnow()
                self._check_for_free_trials()
                self._create_nodes_and_clusters()
                self._monitor_nodes_and_clusters()
                self._expire_nodes_and_clusters()
                end = datetime.utcnow()
                duration = (end - start).total_seconds()
                self.logger.info("** Loop took {} secs. Sleeping for 10 secs.".format(duration))
                time.sleep(10)
        except (KeyboardInterrupt, SystemExit) as err:
            self.logger.error("Safely handling exception. {}".format(err))
            raise


if __name__ == "__main__":
    """
    Call with arguments initd or service. E.g.,
    service unravel_clm start|start|restart
    """
    parser = argparse.ArgumentParser(description="Cluster Lifecycle Manager")
    parser.add_argument("action", nargs='?', default=None)
    args = parser.parse_args()

    action = args.action
    print("Action: {}".format(action))

    app = ClusterLifecycleManager(args)

    if action is not None and action in ["start", "stop", "restart"]:
        daemon_runner = runner.DaemonRunner(app)
        daemon_runner.do_action()
    else:
        app.run()

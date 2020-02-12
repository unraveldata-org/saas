# Python standard library imports
import sys
import os
import argparse
import logging
import time

# Third-party imports
from daemon import runner

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Local imports
from db.models import DBRunner, TrialRequest, NodeSpec, Node
from db.config import Config

APP_NAME = "unravel_clm"
APPLICATION = "Cluster LifeCycle Manager"

base_path = os.path.dirname(os.path.abspath(__file__))

class CloudProvider(object):
    NAME_TO_NODE_TYPE = {
        "EMR": "r4.4xlarge"
    }

    NAME_TO_STORAGE = {
        "EMR": "S3"
    }


class ClusterLifecycleManager(object):

    logger = logging.getLogger("ClusterLifecycleManager")
    logger.setLevel(logging.INFO)

    # Console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    DEFAULT_TTL_HOURS = 72

    def __init__(self, args):
        self.stdin_path = "/dev/null"
        # TODO, use the proper /var/log and /var/run paths
        self.stdout_path = os.path.join(base_path, APP_NAME + ".out")
        self.stderr_path = os.path.join(base_path, APP_NAME + ".err")
        self.pidfile_path = os.path.join(base_path, APP_NAME + ".pid")
        self.pidfile_timeout = 5

        self.session, self.engine = None, None

    def _connect_to_db(self):
        DBRunner.DEBUG = True
        self.session, self.engine = DBRunner.setup_session(DBRunner.get_unravel_jdbc_url())
        self.logger.info("Connected to the DB successfully")
        
    def _cleanup(self):
        pass

    def _check_for_free_trials(self):
        new_trials = TrialRequest.get_all_pending()
        self.logger.info("There are {} pending trial requests.".format(len(new_trials)))

        # Example of how to create a node_spec for the pending request.
        for trial in new_trials:
            # TODO, make more robust
            node_type = CloudProvider.NAME_TO_NODE_TYPE[trial.cloud_provider]
            storage_config = CloudProvider.NAME_TO_STORAGE[trial.cloud_provider]

            unravel_version = Config.UNRAVEL_VERSION_LATEST
            unravel_tar = Config.UNRAVEL_VERSION_TO_TAR[unravel_version]

            # TODO, check for DDOS, which may result in a state of DENIED
            approved = True

            if approved:
                spec = NodeSpec.create_if_not_exists(cloud_provider=trial.cloud_provider, node_type=node_type,
                                                     storage_config=storage_config, unravel_version=unravel_version,
                                                     unravel_tar=unravel_tar, mysql_version=Config.UNRAVEL_MYSQL_VERSION,
                                                     install_ondemand=False, extra=None, ttl_hours=self.DEFAULT_TTL_HOURS, trial_request_id=trial.id)
                spec.save()
                trial.set_state(TrialRequest.State.APPROVED)
                trial.update()

                self.logger.info("Transitioned TrialRequest with ID {} from pending to approved by creating a NodeSpec. Trial Request: {} has NodeSpec: {}".
                    format(trial.id, trial, spec))
            else:
                trial.set_state(TrialRequest.State.DENIED)
                self.logger.info("Transitioned TrialRequest with ID {} from pending to denied due to potential attack.".
                                 format(trial.id))
                trial.update()

            self.session.commit()

    def _create_nodes_and_clusters(self):
        pass
        # TODO, check for records that are "pending" and instantiate them, then update the
        # state to "launched"
        pending_node_specs = NodeSpec.get_all_pending()
        self.logger.info("There are {} pending Node Specs.".format(len(pending_node_specs)))

        for node_spec in pending_node_specs:
            self.logger.info("Analyzing Node Spec with ID {}".format(node_spec.id))
            node = Node.create_from_node_spec(node_spec)
            node.save()

            node_spec.set_state(NodeSpec.State.FINISHED)
            node_spec.update()
            self.session.commit()

            self.logger.info("Transitioned NodeSpec with ID {} from pending to finished by creating a Node. NodeSpec: {} has Node: {}".
                format(node_spec.id, node_spec, node))

    def _monitor_nodes_and_clusters(self):
        # TODO, check for records that are "launched" and determine when they are healthy,
        # then update the state to "ready". If stuck in "launched" for over 6 hours then expire/delete.
        launched = Node.get_by_state(Node.State.LAUNCHED)
        for node in launched:
            node.set_state(Node.State.READY)
            node.update()
            self.logger.info("Transitioning Node with ID {} from launched to ready. {}".format(node.id, node))
        self.session.commit()

    def _expire_nodes_and_clusters(self):
        pass
        # TODO, monitor nodes that are ready and have exceeded their TTL, so set their
        # state to "expired" and launch a job to delete them.
        # Check any "expired" to see if they are actually deleted, and them mark them as "deleted"

        # The order matters, should first try to go from EXPIRED -> DELETED in this for-loop.
        expired = Node.get_by_state(Node.State.EXPIRED)
        self.logger.info("There are {} expired Nodes that have already been deleted.".format(len(expired)))
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
        self.logger.info("Starting {}".format(APPLICATION))
        try:
            self._connect_to_db()
            while True:
                self._check_for_free_trials()
                self._create_nodes_and_clusters()
                self._monitor_nodes_and_clusters()
                self._expire_nodes_and_clusters()
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

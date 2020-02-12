# Python standard library imports
import os
import sys
import logging

root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_dir)

# Local imports
from db.models import DBRunner, TrialRequest


class Manager(object):

    logger = logging.getLogger("Manager")
    logger.setLevel(logging.INFO)

    # Console handler with a higher log level
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch.setFormatter(formatter)

    logger.addHandler(ch)

    DEFAULT_TTL_HOURS = 72

    def __init__(self):
        self.session, self.engine = None, None

        self._connect_to_db()

    def _connect_to_db(self):
        DBRunner.DEBUG = True
        self.session, self.engine = DBRunner.setup_session(DBRunner.get_unravel_jdbc_url())
        self.logger.info("Connected to the DB successfully")

    def insert_trial_request(self, first_name, last_name, email, title, company, ip, cloud_provider):
        create_cluster = False
        self.logger.info("Inserting a Trial Request. first_name: {}, last_name: {}, email: {}, title: {}, company: {}, ip: {}, cloud_provider: {}".format(
            first_name, last_name, email, title, company, ip, cloud_provider
        ))
        trial = TrialRequest.create_if_not_exists(first_name, last_name, email, title, company, ip, cloud_provider, create_cluster)
        trial.save()
        self.session.commit()
        return trial.id

    def get_trial_by_id(self, request_id):
        # TODO, check for object that does not exist
        trial = TrialRequest.get_by_id(request_id)
        return trial


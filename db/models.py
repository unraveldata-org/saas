# Python standard library imports
from datetime import datetime, timedelta
import random, string
import logging

# Third-party imports
from sqlalchemy import create_engine
from sqlalchemy import Column, Boolean, Integer, Float, String, DateTime, ForeignKey, Text
from sqlalchemy import func, and_, or_, not_
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.pool import QueuePool
from sqlalchemy.exc import DatabaseError

# Local imports
from db.config import Config


# SQLAlchemy session
session = None
logger = logging.getLogger("SQLAlchemyModels")


class DBRunner(object):
    """
    Represents a long-running session to the MySQL database using MySQL diaect and PyMySQL connector.
    """
    # Set to True to print the JDBC url (which includes the password), and also echo all statements.
    DEBUG = False

    @classmethod
    def get_unravel_jdbc_url(cls):
        """
        Get the Unravel JDBC URL, which includes the username and password
        :return: Return a string representing the JDBC URL
        """
        jdbc_url = Config.db_jdbc_url

        db_type = jdbc_url.split("://")[0]
        host_port_db = jdbc_url[len(db_type) + 3:]

        if Config.db_password == "":
            url = "{}+pymysql://{}@{}".format(db_type, Config.db_username, host_port_db)
        else:
            url = "{}+pymysql://{}:{}@{}".format(db_type, Config.db_username, Config.db_password, host_port_db)

        # Do not print the URL since it contains a password

        if cls.DEBUG:
            print("JDBC URL: {}".format(url))

        return url

    @classmethod
    def setup_session(cls, jdbc_url):
        """
        Given the JDBC url, set the global SQLAlchemy session and connect it to the appropriate engine
        :param jdbc_url: JDBC URL string
        """
        global session
        global engine
        # https://docs.sqlalchemy.org/en/13/core/engines.html
        # Also, take a look at pessimistic/optimistic connection handling
        # https://docs.sqlalchemy.org/en/13/core/pooling.html#sqlalchemy.pool.QueuePool

        session = None
        engine = None
        try:
            # Can enable echo=True for debugging
            echo = cls.DEBUG is True
            engine = create_engine(jdbc_url, pool_size=128, max_overflow=10, poolclass=QueuePool, echo=echo)
            Session = sessionmaker()
            # Actually bind it to an engine once we know the DB configs
            Session.configure(bind=engine)
            session = Session()
        except Exception as exc:
            raise Exception("Setup session failed with exception: {}".format(exc))

        return session, engine


@as_declarative()
class Base(object):
    """
    Class that is meant to be used as a base for all models that want
    an auto-increment ID as a PK and some CRUD functions that don't auto-commit.
    in order to CRUD to the session and flush, but don't commit.
    E.g.,

    class SomeModel(Base):
        def __init__():
            pass

    element = SomeModel()
    element.set_x(val=y)
    element.save()
    session.commit()
    element.update({"x": "y"})
    session.commit()
    element.delete()
    session.commit()
    """
    id = Column(Integer, primary_key=True)

    def save(self):
        session.add(self)
        self._flush()
        return self

    def update(self, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return self.save()

    def delete(self):
        session.delete(self)
        self._flush()

    def _flush(self):
        try:
            session.flush()
        except DatabaseError:
            session.rollback()
            raise


class TrialRequest(Base):
    """
    Represents a Free Trial request.
    """

    class State:
        PENDING = "pending"
        APPROVED = "approved"
        DENIED = "denied"

    class Type:
        FREE = "free"
        PAID = "paid"

    # The length of Strings is only used during a CREATE TABLE statement
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(256), nullable=False)
    title = Column(String(256), nullable=True)
    company = Column(String(256), nullable=True)
    ip = Column(String(32), nullable=True)
    state = Column(String(32), nullable=False)
    trial_type = Column(String(128), nullable=False)

    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    cloud_provider = Column(String(128), nullable=False)
    create_cluster = Column(Boolean, nullable=False)
    notify_customer = Column(String(32), nullable=True)

    __tablename__ = "trial_request"

    def __init__(self, first_name, last_name, email, title, company, ip, state, trial_type, start_date, cloud_provider, create_cluster, notify_customer):
        """
        Construct a TrialRequest object
        :param first_name: Customer first name (str)
        :param last_name: Customer last name (str)
        :param email: Customer email (str, should already be validated)
        :param title: Customer job title (str)
        :param company: Customer company name (str)
        :param ip: Customer IP address (str) used to issue the request, useful in detecting DDOS
        :param state: Entity state (str)
        :param trial_type: Trial type, e.g., "free" (str)
        :param start_date: Python DateTime UTC object for when the request was created
        :param cloud_provider: Desired Cloud Provider name (str)
        :param create_cluster: Boolean indicating whether to create a cluster.
        :param notify_customer: State of whether the customer has been notified.
        """
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.title = title
        self.company = company
        self.ip = ip
        self.state = state
        self.trial_type = trial_type
        self.start_date = start_date if start_date is not None else datetime.utcnow()
        self.cloud_provider = cloud_provider
        self.create_cluster = create_cluster

        # None means no actions, "pending" means need to send, "finished" means sent.
        self.notify_customer = notify_customer

    def __repr__(self):
        """
        Machine-readable representation of this object.
        :return: Return a machine-readable string that exactly describes this object.
        """
        return u"<TrialRequest(id: {}, first name: {}, last name: {}, email: {}, company: {}, ip: {}, state: {}, " \
               u"trial_type: {}, start_date: {}, cloud_provider: {}, create cluster: {}, notify customer: {})>". \
            format(self.id, self.first_name, self.last_name, self.email, self.company, self.ip, self.state,
                   self.trial_type, self.start_date, self.cloud_provider, self.create_cluster, self.notify_customer)

    @classmethod
    def get_all(cls):
        """
        Get all of the TrialRequest objects that exist.
        :return: Return a list of TrialRequest objects, which could be an empty list.
        """
        return session.query(TrialRequest).all()

    @classmethod
    def get_all_pending(cls):
        """
        Get all TrialRequest objects whose state is PENDING.
        :return: Return a list of TrialRequest objects, which could be an empty list.
        """
        trials = session.query(TrialRequest).filter_by(state=cls.State.PENDING).all()
        return trials

    @classmethod
    def get_by_states_or_after_datetime(cls, states, date):
        """
        Get all TrialRequest objects whose state matches or whose start_date >= given date.
        :param states: List of states (str)
        :param date: Python DateTime object
        :return: Return a list of TrialRequest objects, which could be an empty list.
        """
        return session.query(TrialRequest).filter(or_(TrialRequest.state.in_(states), TrialRequest.start_date >= date)).all()

    @classmethod
    def get_by_id(cls, id):
        """
        Get a TrialRequest object given its id.
        :param id: ID (int PK)
        :return: Return the TrialRequest object if it exists, otherwise, None.
        """
        return session.query(TrialRequest).filter_by(id=id).first()

    @classmethod
    def get_num_created_after_datetime(cls, date):
        """
        Get the number of TrialRequest objects whose start_date is >= the given date.
        This is useful to throttle and prevent an attack.
        :param date: Python DateTime object
        :return: Return the number of TrialRequest objects (int)
        """
        count = session.query(func.count(TrialRequest.id)).filter(TrialRequest.start_date >= date).scalar()
        return count

    @classmethod
    def create_if_not_exists(cls, first_name, last_name, email, title, company, ip, cloud_provider, create_cluster, notify_customer=None):
        """
        Create a TrialRequest with an initial state.
        :return: Return the TrialRequest object that was created
        """
        start_date = datetime.utcnow()
        trial = TrialRequest(first_name=first_name, last_name=last_name, email=email, title=title, company=company,
                             ip=ip, state=cls.State.PENDING, trial_type=cls.Type.FREE, start_date=start_date, cloud_provider=cloud_provider,
                             create_cluster=create_cluster, notify_customer=notify_customer)
        # Still need to call trial.save() and session.commit()
        return trial

    def set_state(self, state):
        """
        Change the state as long as it is allowed.
        :param state: Desired state, which must be one of TrialRequest.State
        """
        allowed_transitions = {
            TrialRequest.State.PENDING: {TrialRequest.State.APPROVED, TrialRequest.State.DENIED},
            TrialRequest.State.APPROVED: {},
            TrialRequest.State.DENIED: {}
        }

        if state == self.state:
            return

        allowed_states = allowed_transitions[self.state]
        if state in allowed_states:
            # Still need to call self.update() and session.commit()
            self.state = state
        else:
            raise Exception("Cannot transition from state {} to {}".format(self.state, state))


class NodeSpec(Base):
    """
    Represents a Node Spec request.
    """

    class State:
        PENDING = "pending"
        FINISHED = "finished"

    DEFAULT_TTL_HOURS = 72

    cloud_provider = Column(String(128), nullable=False)
    region = Column(String(256), nullable=False)
    state = Column(String(32), nullable=False)

    # User that requested it
    user = Column(String(64), nullable=False)
    node_type = Column(String(256), nullable=False)

    storage_config = Column(Text, nullable=True)
    unravel_version = Column(String(64), nullable=False)
    unravel_tar = Column(String(256), nullable=True)
    mysql_version = Column(String(256), nullable=True)
    install_ondemand = Column(Boolean, nullable=False)

    extra = Column(Text, nullable=True)
    date_requested = Column(DateTime, default=datetime.utcnow, nullable=False)
    ttl_hours = Column(Integer, default=DEFAULT_TTL_HOURS, nullable=False)

    # Nullable FK
    trial_request_id = Column(Integer, ForeignKey("trial_request.id"))

    __tablename__ = "node_spec"

    def __repr__(self):
        """
        Machine-readable representation of this object.
        :return: Return a machine-readable string that exactly describes this object.
        """
        return u"<NodeSpec(id: {}, cloud_provider: {}, region: {}, state: {}, user: {}, node_type: {}, unravel_version: {}, unravel_tar: {}, " \
               u"date_requested: {}, ttl_hours: {}, trial_request_id: {})>". \
            format(self.id, self.cloud_provider, self.region, self.state, self.user, self.node_type, self.unravel_version, self.unravel_tar,
                   self.date_requested, self.ttl_hours, self.trial_request_id)

    def __init__(self, cloud_provider, region, user, node_type, storage_config, unravel_version, unravel_tar, mysql_version, install_ondemand, extra, ttl_hours, trial_request_id=None):
        """
        Construct a NodeSpec object
        :param cloud_provider: Cloud Provider name (str)
        :param region: Region name (str)
        :param user: User that requested it (str)
        :param node_type: Node/VM type (str)
        :param storage_config: Some information about its storage, such as number of disks, etc.
        :param unravel_version: Unravel version to install (str), e.g., 4.6.0.1
        :param unravel_tar: Unravel tarball path to wget. Once we move to a tarball approach instead of RPM,
        this may be utilized instead.
        :param mysql_version: MySQL version to install (str)
        :param install_ondemand: Boolean indicating if should also install Unravel Ondemand.
        :param extra: Extra information in JSON in a text/blob column.
        :param ttl_hours: Time to live in hours (int)
        :param trial_request_id: FK (int) to the corresponding TrialRequest object if one exists.
        """
        self.cloud_provider = cloud_provider
        self.region = region
        self.state = self.State.PENDING
        self.user = user
        self.node_type = node_type
        self.storage_config = storage_config
        self.unravel_version = unravel_version
        self.unravel_tar = unravel_tar
        self.mysql_version = mysql_version
        self.install_ondemand = install_ondemand
        self.extra = extra
        self.date_requested = datetime.utcnow()

        # Current number of hours to expire after date_launched.
        # When expiring a resource, simply set it to 0
        self.ttl_hours = ttl_hours if ttl_hours >= 0 else 0

        # FK may be None
        self.trial_request_id = trial_request_id

    @classmethod
    def get_by_trial_request_id(cls, trial_request_id):
        """
        Get the single NodeSpec that was created from the trial request id
        :param trial_request_id: Trial request id (int)
        :return: Return a list of NodeSpec objects (which should be a singleton list).
        """
        spec = session.query(NodeSpec).filter_by(trial_request_id=trial_request_id).all()
        return spec

    @classmethod
    def get_all(cls):
        """
        Get all of the NodeSpec objects that exist.
        :return: Return a list of NodeSpec objects, which could be an empty list.
        """
        return session.query(NodeSpec).all()

    @classmethod
    def get_all_pending(cls):
        """
        Get all NodeSpec objects whose state is PENDING.
        :return: Return a list of NodeSpec objects, which could be an empty list.
        """
        trials = session.query(NodeSpec).filter_by(state=cls.State.PENDING).all()
        return trials

    @classmethod
    def get_by_id(cls, id):
        """
        Get a NodeSpec object given its id.
        :param id: ID (int PK)
        :return: Return the NodeSpec object if it exists, otherwise, None.
        """
        return session.query(NodeSpec).filter_by(id=id).first()

    @classmethod
    def create_if_not_exists(cls, cloud_provider, region, user, node_type, storage_config, unravel_version, unravel_tar,
                             mysql_version, install_ondemand, extra, ttl_hours, trial_request_id=None):
        """
        Create a NodeSpec with an initial state.
        :return: Return the NodeSpec object that was created
        """
        spec = NodeSpec(cloud_provider=cloud_provider, region=region, user=user, node_type=node_type,
                        storage_config=storage_config, unravel_version=unravel_version, unravel_tar=unravel_tar,
                        mysql_version=mysql_version, install_ondemand=install_ondemand, extra=extra,
                        ttl_hours=ttl_hours, trial_request_id=trial_request_id)
        # Still need to call spec.save() and session.commit()
        return spec

    def get_cloud_provider(self):
        return self.cloud_provider

    def get_state(self):
        return self.state

    def get_date_requested(self):
        return self.date_requested

    def set_state(self, state):
        """
        Change the state as long as it is allowed.
        :param state: Desired state, which must be one of NodeSpec.State
        """
        allowed_transitions = {
            NodeSpec.State.PENDING: {NodeSpec.State.FINISHED, },
            NodeSpec.State.FINISHED: {}
        }

        if state == self.state:
            return

        allowed_states = allowed_transitions[self.state]
        if state in allowed_states:
            # Still need to call self.update() and session.commit()
            self.state = state
        else:
            raise Exception("Cannot transition from state {} to {}".format(self.state, state))


class Node(Base):
    """
    Represents a Node object to instantiate, monitor, delete.
    """

    class State:
        LAUNCHED = "launched"
        READY = "ready"
        EXPIRED = "expired"
        DELETED = "deleted"

    cloud_provider = Column(String(128), nullable=False)
    region = Column(String(256), nullable=False)
    state = Column(String(32), nullable=False)
    node_type = Column(String(256), nullable=False)
    node_ip = Column(String(256), nullable=True)

    ttl_hours = Column(Integer, nullable=False)
    date_launched = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_ready    = Column(DateTime, nullable=True)
    date_expired  = Column(DateTime, nullable=True)
    date_deleted  = Column(DateTime, nullable=True)

    # Nullable FK
    node_spec_id = Column(Integer, ForeignKey("node_spec.id"))

    __tablename__ = "node"

    def __repr__(self):
        """
        Machine-readable representation of this object.
        :return: Return a machine-readable string that exactly describes this object.
        """
        dates_msg = ""
        if self.state in [Node.State.LAUNCHED, Node.State.READY, Node.State.EXPIRED, Node.State.DELETED]:
            dates_msg += " date_launched: {},".format(self.date_launched)

        if self.state in [Node.State.READY, Node.State.EXPIRED, Node.State.DELETED]:
            dates_msg += " date_ready: {},".format(self.date_ready)

        if self.state in [Node.State.EXPIRED, Node.State.DELETED]:
            dates_msg += " date_expired: {},".format(self.date_expired)

        if self.state in [Node.State.DELETED]:
            dates_msg += " date_deleted: {},".format(self.date_deleted)

        msg = u"<Node(id: {}, cloud_provider: {}, region: {}, state: {}, node_type: {}, node_ip: {}, " \
              u"ttl_hours: {},{} node_spec_id: {})>".\
            format(self.id, self.cloud_provider, self.region, self.state, self.node_type, self.node_ip,
                   self.ttl_hours, dates_msg, self.node_spec_id)
        return msg

    def __init__(self, cloud_provider, region, node_type, node_ip, ttl_hours, node_spec_id):
        """
        Construct a Node object
        :param cloud_provider: Cloud Provider name (str)
        :param region: Region name (str)
        :param node_type: Node/VM type (str)
        :param node_ip: Node IP address (str)
        :param ttl_hours: Time to live in hours (int)
        :param node_spec_id: FK (int) to the NodeSpec's id.
        """
        self.cloud_provider = cloud_provider
        self.region = region
        self.state = self.State.LAUNCHED
        self.node_type = node_type
        self.node_ip = node_ip
        self.ttl_hours = ttl_hours if ttl_hours >= 0 else 0
        self.date_launched = datetime.utcnow()

        # FK
        self.node_spec_id = node_spec_id

    @classmethod
    def get_by_node_spec_id(cls, node_spec_id):
        """
        Get a Node given the FK to its NodeSpec's id.
        :param node_spec_id: FK (int) of the NodeSpec's id
        :return: Return the singleton list of the Node object.
        """
        node = session.query(Node).filter_by(node_spec_id=node_spec_id).all()
        return node

    @classmethod
    def get_all(cls):
        """
        Get all of the Node objects that exist.
        :return: Return a list of Node objects, which could be an empty list.
        """
        return session.query(Node).all()

    @classmethod
    def get_by_state(cls, state):
        """
        Get all of the Node objects with the given state
        :param state: State (str)
        :return: Return a list of Node objects.
        """
        nodes = session.query(Node).filter_by(state=state).all()
        return nodes

    @classmethod
    def get_by_states(cls, states):
        """
        Get all of the Node objects whose state is in the given list.
        :param states: List of states (str)
        :return: Return a list of Node objects.
        """
        nodes = session.query(Node).filter(Node.state.in_(states)).all()
        return nodes

    @classmethod
    def get_by_id(cls, id):
        """
        Get a Node object given its id.
        :param id: ID (int PK)
        :return: Return the Node object if it exists, otherwise, None.
        """
        return session.query(Node).filter_by(id=id).first()

    @classmethod
    def create_from_node_spec(cls, node_spec):
        """
        Construct a Node object given a NodeSpec.
        :param node_spec: Source information, which is the NodeSpec
        :return: Return a Node object
        """
        # The IP will be determined later
        node = Node.create_if_not_exists(node_spec.cloud_provider, node_spec.region, node_spec.node_type, None, node_spec.ttl_hours, node_spec.id)
        return node

    @classmethod
    def create_if_not_exists(cls, cloud_provider, region, node_type, node_ip, ttl_hours, node_spec_id):
        """
        Create a Node with initial state.
        :return: Return the Node object that was created
        """
        node = Node(cloud_provider=cloud_provider, region=region, node_type=node_type,
                    node_ip=node_ip, ttl_hours=ttl_hours, node_spec_id=node_spec_id)
        # Still need to call node.save() and session.commit()
        return node

    @classmethod
    def get_all_ready_to_expire(self):
        """
        Get a list of the Node objects that are ready to be expired. Their current state could be either
        LAUNCHED or READY.
        :return: Return a list of Node objects to expire.
        """
        now = datetime.utcnow()

        expired = []

        launched = Node.get_by_state(Node.State.LAUNCHED)
        for node in launched:
            if Node.date_launched is not None and (node.date_launched + timedelta(hours=node.ttl_hours)) <= now:
                expired.append(node)

        ready = Node.get_by_state(Node.State.READY)
        for node in ready:
            if node.date_ready is not None and (node.date_ready + timedelta(hours=node.ttl_hours)) <= now:
                expired.append(node)

        return expired

    def set_state(self, state):
        """
        Change the state as long as it is allowed.
        :param state: Desired state, which must be one of Node.State
        """
        now = datetime.utcnow()

        allowed_transitions = {
            Node.State.LAUNCHED: {Node.State.READY, Node.State.EXPIRED},
            Node.State.READY: {Node.State.EXPIRED},
            Node.State.EXPIRED: {Node.State.DELETED},
            Node.State.DELETED: {}
        }

        if state == self.state:
            return

        allowed_states = allowed_transitions[self.state]
        if state in allowed_states:
            self.state = state

            if state == Node.State.READY:
                self.date_ready = now
            elif state == Node.State.EXPIRED:
                self.date_expired = now
            elif state == Node.State.DELETED:
                self.date_deleted = now
        else:
            raise Exception("Cannot transition from state {} to {}".format(self.state, state))

    def set_ttl_hours(self, ttl_hours):
        """
        Change the TTL hours. This is typically done to either
        * extend (increase from current value)
        * expire (set to 0)
        """
        self.ttl_hours = ttl_hours

class ClusterSpec(Base):
    """
    Represents a Cluster Spec request.
    """

    class State:
        PENDING = "pending"
        FINISHED = "finished"

    DEFAULT_TTL_HOURS = 72

    # No guarantee we can actually request that name
    cluster_name = Column(String(128), nullable=True)

    cloud_provider = Column(String(128), nullable=False)
    region = Column(String(256), nullable=False)
    state = Column(String(32), nullable=False)

    # User that requested it
    user = Column(String(64), nullable=False)

    num_head_nodes = Column(Integer, nullable=False)
    head_node_type = Column(String(256), nullable=False)

    num_worker_nodes = Column(Integer, nullable=False)
    worker_node_type = Column(String(256), nullable=False)

    os_family = Column(String(128), nullable=True)
    stack_version = Column(String(128), nullable=False)
    cluster_type = Column(String(128), nullable=False)

    jdk = Column(String(32), nullable=True)
    storage = Column(String(1024), nullable=True)

    services = Column(Text, nullable=True)
    bootstrap_action = Column(Text, nullable=True)

    is_hdfs_ha = Column(Boolean, nullable=False)
    is_rm_ha = Column(Boolean, nullable=False)
    is_ssl = Column(Boolean, nullable=False)
    is_kerberized = Column(Boolean, nullable=False)

    extra = Column(Text, nullable=True)

    date_requested = Column(DateTime, default=datetime.utcnow, nullable=False)
    ttl_hours = Column(Integer, default=DEFAULT_TTL_HOURS, nullable=False)

    # Nullable FK
    trial_request_id = Column(Integer, ForeignKey("trial_request.id"))

    __tablename__ = "cluster_spec"

    def __repr__(self):
        """
        Machine-readable representation of this object.
        :return: Return a machine-readable string that exactly describes this object.
        """
        # TODO, add more stuff here
        return u"<ClusterSpec(id: {}, cluster_name: {}, cloud_provider: {}, region: {}, state: {}, user: {}, trial_request_id: {})>". \
            format(self.id, self.name, self.cloud_provider, self.region, self.state, self.user, self.trial_request_id)

    def __init__(self, cluster_name, cloud_provider, region, user, num_head_nodes, head_node_type, num_worker_nodes, worker_node_type,
                 os_family, stack_version, cluster_type, jdk, storage, services, bootstrap_action,
                 is_hdfs_ha, is_rm_ha, is_ssl, is_kerberized, extra, ttl_hours, trial_request_id=None):
        """
        Construct a ClusterSpec object
        # TODO, populate these
        :param extra: Extra information in JSON in a text/blob column.
        :param ttl_hours: Time to live in hours (int)
        :param trial_request_id: FK (int) to the corresponding TrialRequest object if one exists.
        """
        self.cluster_name = cluster_name
        self.cloud_provider = cloud_provider
        self.region = region
        self.state = self.State.PENDING
        self.user = user
        self.num_head_nodes = num_head_nodes
        self.head_node_type = head_node_type
        self.num_worker_nodes = num_worker_nodes
        self.worker_node_type = worker_node_type
        self.os_family = os_family
        self.stack_version = stack_version
        self.cluster_type = cluster_type
        self.jdk = jdk
        self.storage = storage
        self.services = services
        self.bootstrap_action = bootstrap_action
        self.is_hdfs_ha = is_hdfs_ha
        self.is_rm_ha = is_rm_ha
        self.is_ssl = is_ssl
        self.is_kerberized = is_kerberized
        self.extra = extra
        self.date_requested = datetime.utcnow()
        self.ttl_hours = ttl_hours if ttl_hours >= 0 else 0

        # FK may be None
        self.trial_request_id = trial_request_id

    @classmethod
    def get_by_trial_request_id(cls, trial_request_id):
        """
        Get the single ClusterSpec that was created from the trial request id
        :param trial_request_id: Trial request id (int)
        :return: Return a list of ClusterSpec objects (which should be a singleton list).
        """
        spec = session.query(ClusterSpec).filter_by(trial_request_id=trial_request_id).all()
        return spec

    @classmethod
    def get_all(cls):
        """
        Get all of the ClusterSpec objects that exist.
        :return: Return a list of ClusterSpec objects, which could be an empty list.
        """
        return session.query(ClusterSpec).all()

    @classmethod
    def get_all_pending(cls):
        """
        Get all ClusterSpec objects whose state is PENDING.
        :return: Return a list of ClusterSpec objects, which could be an empty list.
        """
        trials = session.query(ClusterSpec).filter_by(state=cls.State.PENDING).all()
        return trials

    @classmethod
    def get_by_id(cls, id):
        """
        Get a ClusterSpec object given its id.
        :param id: ID (int PK)
        :return: Return the ClusterSpec object if it exists, otherwise, None.
        """
        return session.query(ClusterSpec).filter_by(id=id).first()

    @classmethod
    def create_if_not_exists(cls, cluster_name, cloud_provider, region, user, num_head_nodes, head_node_type,
                             num_worker_nodes, worker_node_type, os_family, stack_version, cluster_type,
                             jdk, storage, services, bootstrap_action, is_hdfs_ha, is_rm_ha, is_ssl, is_kerberized,
                             extra, ttl_hours, trial_request_id=None):
        """
        Create a ClusterSpec with an initial state.
        :return: Return the ClusterSpec object that was created
        """
        spec = ClusterSpec(cluster_name=cluster_name, cloud_provider=cloud_provider, region=region, user=user, num_head_nodes=num_head_nodes,
                           head_node_type=head_node_type, num_worker_nodes=num_worker_nodes, worker_node_type=worker_node_type,
                           os_family=os_family, stack_version=stack_version, cluster_type=cluster_type, jdk=jdk,
                           storage=storage, services=services, bootstrap_action=bootstrap_action,
                           is_hdfs_ha=is_hdfs_ha, is_rm_ha=is_rm_ha, is_ssl=is_ssl, is_kerberized=is_kerberized,
                           extra=extra, ttl_hours=ttl_hours, trial_request_id=trial_request_id)
        # Still need to call spec.save() and session.commit()
        return spec

    def get_cloud_provider(self):
        return self.cloud_provider

    def get_state(self):
        return self.state

    def get_date_requested(self):
        return self.date_requested

    def set_state(self, state):
        """
        Change the state as long as it is allowed.
        :param state: Desired state, which must be one of NodeSpec.State
        """
        allowed_transitions = {
            ClusterSpec.State.PENDING: {ClusterSpec.State.FINISHED, },
            ClusterSpec.State.FINISHED: {}
        }

        if state == self.state:
            return

        allowed_states = allowed_transitions[self.state]
        if state in allowed_states:
            # Still need to call self.update() and session.commit()
            self.state = state
        else:
            raise Exception("Cannot transition from state {} to {}".format(self.state, state))


class Cluster(Base):
    """
    Represents a Cluster object to instantiate, monitor, delete.
    """

    class State:
        LAUNCHED = "launched"
        READY = "ready"
        EXPIRED = "expired"
        DELETED = "deleted"

    # The actual ID and Name assigned by the Cloud Provider, which over time may not be unique.
    cluster_id = Column(String(256), nullable=True)
    cluster_name = Column(String(256), nullable=True)

    cloud_provider = Column(String(128), nullable=False)
    region = Column(String(256), nullable=False)
    state = Column(String(32), nullable=False)

    config = Column(Text, nullable=True)

    ttl_hours = Column(Integer, nullable=False)
    date_launched = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_ready    = Column(DateTime, nullable=True)
    date_expired  = Column(DateTime, nullable=True)
    date_deleted  = Column(DateTime, nullable=True)

    # Nullable FK
    cluster_spec_id = Column(Integer, ForeignKey("cluster_spec.id"))

    __tablename__ = "cluster"

    def __repr__(self):
        """
        Machine-readable representation of this object.
        :return: Return a machine-readable string that exactly describes this object.
        """
        dates_msg = ""
        if self.state in [Node.State.LAUNCHED, Node.State.READY, Node.State.EXPIRED, Node.State.DELETED]:
            dates_msg += " date_launched: {},".format(self.date_launched)

        if self.state in [Node.State.READY, Node.State.EXPIRED, Node.State.DELETED]:
            dates_msg += " date_ready: {},".format(self.date_ready)

        if self.state in [Node.State.EXPIRED, Node.State.DELETED]:
            dates_msg += " date_expired: {},".format(self.date_expired)

        if self.state in [Node.State.DELETED]:
            dates_msg += " date_deleted: {},".format(self.date_deleted)

        msg = u"<Cluster(id: {}, cluster_id: {}, cluster_name: {}, cloud_provider: {}, region: {}, state: {}, " \
              u"ttl_hours: {},{} cluster_spec_id: {})>".\
            format(self.id, self.cluster_id, self.cluster_name, self.cloud_provider, self.region, self.state,
                   self.ttl_hours, dates_msg, self.cluster_spec_id)
        return msg

    def __init__(self, cluster_id, cluster_name, cloud_provider, region, config, ttl_hours, cluster_spec_id):
        """
        Construct a Cluster object
        :param cluster_id: Optional Cluster ID (str)
        :param cluster_name: Optional Cluster name (str)
        :param cloud_provider: Cloud Provider name (str)
        :param region: Region name (str)
        :param config: Config metadata (str)
        :param ttl_hours: Time to live in hours (int)
        :param cluster_spec_id: FK (int) to the ClusterSpec's id.
        """
        self.cluster_id = cluster_id
        self.cluster_name = cluster_name
        self.cloud_provider = cloud_provider
        self.region = region
        self.state = self.State.LAUNCHED
        self.config = config

        # Current number of hours to expire after date_launched.
        # When expiring a resource, simply set it to 0
        self.ttl_hours = ttl_hours if ttl_hours >= 0 else 0
        self.date_launched = datetime.utcnow()

        # FK
        self.cluster_spec_id = cluster_spec_id

    @classmethod
    def get_by_cluster_spec_id(cls, cluster_spec_id):
        """
        Get a Cluster given the FK to its ClusterSpec's id.
        :param cluster_spec_id: FK (int) of the ClusterSpec's id
        :return: Return the singleton list of the Cluster object.
        """
        node = session.query(Cluster).filter_by(cluster_spec_id=cluster_spec_id).all()
        return node

    @classmethod
    def get_all(cls):
        """
        Get all of the Cluster objects that exist.
        :return: Return a list of Cluster objects, which could be an empty list.
        """
        return session.query(Cluster).all()

    @classmethod
    def get_by_state(cls, state):
        """
        Get all of the Cluster objects with the given state
        :param state: State (str)
        :return: Return a list of Cluster objects.
        """
        nodes = session.query(Cluster).filter_by(state=state).all()
        return nodes

    @classmethod
    def get_by_states(cls, states):
        """
        Get all of the Cluster objects whose state is in the given list.
        :param states: List of states (str)
        :return: Return a list of Cluster objects.
        """
        nodes = session.query(Cluster).filter(Cluster.state.in_(states)).all()
        return nodes

    @classmethod
    def get_by_id(cls, id):
        """
        Get a Cluster object given its id.
        :param id: ID (int PK)
        :return: Return the Cluster object if it exists, otherwise, None.
        """
        return session.query(Cluster).filter_by(id=id).first()

    @classmethod
    def create_from_cluster_spec(cls, cluster_spec):
        """
        Construct a Cluster object given a ClusterSpec.
        :param cluster_spec: Source information, which is the ClusterSpec
        :return: Return a Cluster object
        """
        # The Id/Name will be determined later
        cluster = Cluster.create_if_not_exists(cluster_spec.cluster_name, cluster_spec.cloud_provider, cluster_spec.region,
                                            cluster_spec.ttl_hours, cluster_spec.id)
        return cluster

    @classmethod
    def create_if_not_exists(cls, cluster_name, cloud_provider, region, ttl_hours, cluster_spec_id):
        """
        Create a Cluster with initial state.
        :return: Return the Cluster object that was created
        """
        # TODO, for now generate a random id
        cluster_id = "cluster_" + ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        cluster = Cluster(cluster_id=cluster_id, cluster_name=cluster_name, cloud_provider=cloud_provider, region=region,
                          config=None, ttl_hours=ttl_hours, cluster_spec_id=cluster_spec_id)
        # Still need to call node.save() and session.commit()
        return cluster

    @classmethod
    def get_all_ready_to_expire(self):
        """
        Get a list of the Cluster objects that are ready to be expired. Their current state could be either
        LAUNCHED or READY.
        :return: Return a list of Cluster objects to expire.
        """
        now = datetime.utcnow()

        expired = []

        launched = Cluster.get_by_state(Cluster.State.LAUNCHED)
        for cluster in launched:
            if cluster.date_launched is not None and (cluster.date_launched + timedelta(hours=cluster.ttl_hours)) <= now:
                expired.append(cluster)

        ready = Cluster.get_by_state(Cluster.State.READY)
        for cluster in ready:
            if cluster.date_ready is not None and (cluster.date_ready + timedelta(hours=cluster.ttl_hours)) <= now:
                expired.append(cluster)

        return expired

    def set_state(self, state):
        """
        Change the state as long as it is allowed.
        :param state: Desired state, which must be one of Cluster.State
        """
        now = datetime.utcnow()

        allowed_transitions = {
            Cluster.State.LAUNCHED: {Cluster.State.READY, Cluster.State.EXPIRED},
            Cluster.State.READY: {Cluster.State.EXPIRED},
            Cluster.State.EXPIRED: {Cluster.State.DELETED},
            Cluster.State.DELETED: {}
        }

        if state == self.state:
            return

        allowed_states = allowed_transitions[self.state]
        if state in allowed_states:
            self.state = state

            if state == Cluster.State.READY:
                self.date_ready = now
            elif state == Cluster.State.EXPIRED:
                self.date_expired = now
            elif state == Cluster.State.DELETED:
                self.date_deleted = now
        else:
            raise Exception("Cannot transition from state {} to {}".format(self.state, state))

    def set_ttl_hours(self, ttl_hours):
        """
        Change the TTL hours. This is typically done to either
        * extend (increase from current value)
        * expire (set to 0)
        """
        self.ttl_hours = ttl_hours

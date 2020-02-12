# Python standard library imports
from datetime import datetime, timedelta
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
            echo = not cls.DEBUG
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

    # The length of Strings is only used during a CREATE TABLE statement
    first_name = Column(String(128), nullable=False)
    last_name = Column(String(128), nullable=False)
    email = Column(String(256), nullable=False)
    title = Column(String(256), nullable=True)
    company = Column(String(256), nullable=True)
    ip = Column(String(32), nullable=True)
    state = Column(String(32), nullable=False)

    start_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    cloud_provider = Column(String(128), nullable=False)
    create_cluster = Column(Boolean, nullable=False)
    notify_customer = Column(String(32), nullable=True)

    '''
    Read https://docs.sqlalchemy.org/en/13/orm/cascades.html
    If a TrialRequest object is deleted, perform a cascade-delete an all of its
    cluster_spec and node_spec entities.
    Because we have a cascade on "all", then performing the following

    trial = TrialRequest()
    node_spec = NodeSpec()
    trial.node_spec = node_spec
    session.add(trial)

    will implicitly also add node_spec to the session.
    "all" is equivalent to "save-update", "merge", "refresh-expire", "expunge", "delete"
    "delete-orphan" will prevent keeping a NULL foreign key by deleting the row
    back_populates="cluster" and backref="cluster" are mutually exclusive
    '''
    # Relationships
    # one-to-many cluster versions
    #cluster_versions = relationship("ClusterVersion", back_populates="cluster", cascade="all,delete-orphan")

    __tablename__ = "trial_request"

    def __repr__(self):
        return u"<TrialRequest(id: {}, first name: {}, last name: {}, email: {}, company: {}, state: {}, " \
               u"start date: {}, cloud_provider: {}, create cluster: {}, notify customer: {})>". \
            format(self.id, self.first_name, self.last_name, self.email, self.company, self.state,
                   self.start_date, self.cloud_provider, self.create_cluster, self.notify_customer)

    @classmethod
    def get_all(cls):
        """
        Get all of the TrialRequest objects that exist.
        :return: Return a list of TrialRequest objects, which could be an empty list.
        """
        return session.query(TrialRequest).all()

    @classmethod
    def get_all_pending(cls):
        trials = session.query(TrialRequest).filter_by(state=cls.State.PENDING).all()
        return trials

    @classmethod
    def get_by_id(cls, id):
        """
        Get a TrialRequest object given its id.
        :param id: ID (int PK)
        :return: Return the TrialRequest object if it exists, otherwise, None.
        """
        return session.query(TrialRequest).filter_by(id=id).first()

    @classmethod
    def create_if_not_exists(cls, first_name, last_name, email, title, company, ip, cloud_provider, create_cluster, notify_customer=None):
        """
        Create a TrialRequest with initial state.
        :return: Return the TrialRequest object that was created
        """
        start_date = datetime.utcnow()
        trial = TrialRequest(first_name=first_name, last_name=last_name, email=email, title=title, company=company,
                             ip=ip, state=cls.State.PENDING, start_date=start_date, cloud_provider=cloud_provider,
                             create_cluster=create_cluster, notify_customer=notify_customer)
        # Still need to call trial.save() and session.commit()
        return trial

    def set_state(self, state):
        # TODO, check that it is an allowed transition.
        self.state = state
        # Still need to call self.update() and session.commit()


class NodeSpec(Base):
    """
    Represents a Node Spec request.
    """

    class State:
        PENDING = "pending"
        FINISHED = "finished"

    DEFAULT_TTL_HOURS = 72

    cloud_provider = Column(String(128), nullable=False)
    state = Column(String(32), nullable=False)
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
        return u"<NodeSpec(id: {}, cloud_provider: {}, state: {}, node_type: {}, unravel_version: {}, unravel_tar: {}, " \
               u"date_requested: {}, ttl_hours: {}, trial_request_id: {})>". \
            format(self.id, self.cloud_provider, self.state, self.node_type, self.unravel_version, self.unravel_tar,
                   self.date_requested, self.ttl_hours, self.trial_request_id)

    def __init__(self, cloud_provider, node_type, storage_config, unravel_version, unravel_tar, mysql_version, install_ondemand, extra, ttl_hours, trial_request_id=None):
        """
        Construct a NodeSpec object
        # TODO add params description
        """
        self.cloud_provider = cloud_provider
        self.state = self.State.PENDING
        self.node_type = node_type
        self.storage_config = storage_config
        self.unravel_version = unravel_version
        self.unravel_tar = unravel_tar
        self.mysql_version = mysql_version
        self.install_ondemand = install_ondemand
        self.extra = extra
        self.date_requested = datetime.utcnow()
        self.ttl_hours = ttl_hours if ttl_hours >= 0 else 0

        # FK may be None
        self.trial_request_id = trial_request_id

    @classmethod
    def get_by_trial_request_id(cls, trial_request_id):
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
    def create_if_not_exists(cls, cloud_provider, node_type, storage_config, unravel_version, unravel_tar,
                             mysql_version, install_ondemand, extra, ttl_hours, trial_request_id=None):
        """
        Create a NodeSpec with initial state.
        :return: Return the NodeSpec object that was created
        """
        spec = NodeSpec(cloud_provider=cloud_provider, node_type=node_type,
                        storage_config=storage_config, unravel_version=unravel_version, unravel_tar=unravel_tar,
                        mysql_version=mysql_version, install_ondemand=install_ondemand, extra=extra,
                        ttl_hours=ttl_hours, trial_request_id=trial_request_id)
        # Still need to call spec.save() and session.commit()
        return spec

    def set_state(self, state):
        # TODO, check if valid state transition
        self.state = state
        # Still need to call self.update() and session.commit()


class Node(Base):
    """
    Represents a Node object to instantiate, monitor, delete.
    """

    class State:
        LAUNCHED = "launched"
        READY = "ready"
        EXPIRED = "expired"
        DELETED = "deleted"

    EXPIRE_IF_STUCK_HOURS = 24

    cloud_provider = Column(String(128), nullable=False)
    state = Column(String(32), nullable=False)
    node_type = Column(String(256), nullable=False)
    node_ip = Column(String(256), nullable=True)

    ttl_hours = Column(Integer, nullable=False)
    date_launched = Column(DateTime, default=datetime.utcnow, nullable=False)
    date_ready    = Column(DateTime, nullable=True)
    date_expired  = Column(DateTime, nullable=True)
    date_deleted  = Column(DateTime, nullable=True)

    # Nullable FK
    node_spec_id = Column(Integer) #, ForeignKey("node_spec.id"))

    __tablename__ = "node"

    def __repr__(self):
        # TODO, can be a bit smarter to print only relevant date fields based on the state
        return u"<Node(id: {}, cloud_provider: {}, state: {}, node_type: {}, node_ip: {}, ttl_hours: {}, " \
               u"date_launched: {}, date_ready: {}, date_expired: {}, date_deleted: {}," \
               u"node_spec_id: {})>". \
            format(self.id, self.cloud_provider, self.state, self.node_type, self.node_ip, self.ttl_hours,
                   self.date_launched, self.date_ready, self.date_expired, self.date_deleted,
                   self.node_spec_id)

    def __init__(self, cloud_provider, node_type, node_ip, ttl_hours, node_spec_id):
        """
        Construct a NodeSpec object
        # TODO add params description
        """
        self.cloud_provider = cloud_provider
        self.state = self.State.LAUNCHED
        self.node_type = node_type
        self.node_ip = node_ip
        self.ttl_hours = ttl_hours if ttl_hours >= 0 else 0
        self.date_launched = datetime.utcnow()

        # FK
        self.node_spec_id = node_spec_id

    @classmethod
    def get_by_node_spec_id(cls, node_spec_id):
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
        nodes = session.query(Node).filter_by(state=state).all()
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
        node = Node.create_if_not_exists(node_spec.cloud_provider, node_spec.node_type, None, node_spec.ttl_hours, node_spec.id)
        return node

    @classmethod
    def create_if_not_exists(cls, cloud_provider, node_type, node_ip, ttl_hours, node_spec_id):
        """
        Create a Node with initial state.
        :return: Return the Node object that was created
        """
        node = Node(cloud_provider=cloud_provider, node_type=node_type,
                    node_ip=node_ip, ttl_hours=ttl_hours, node_spec_id=node_spec_id)
        # Still need to call node.save() and session.commit()
        return node

    @classmethod
    def get_all_ready_to_expire(self):
        # TODO, change to HOURS instead of secs.
        now = datetime.utcnow()
        '''
        results = session.query(Node).filter(
            or_(
                and_(Node.state == Node.State.LAUNCHED,
                     Node.date_launched + timedelta(seconds=Node.ttl_hours) >= now),
                and_(Node.state == Node.State.READY,
                     Node.date_ready + timedelta(seconds=Node.ttl_hours) >= now),
                # Shouldn't be in EXPIRED longer than say 24 hours.
                and_(Node.state == Node.State.EXPIRED,
                     Node.date_expired + timedelta(hours=Node.EXPIRE_IF_STUCK_HOURS) >= now)
            )).all()
        '''

        expired = []

        launched = Node.get_by_state(Node.State.LAUNCHED)
        for node in launched:
            # TODO, change to HOURS after done with demo
            if node.date_launched + timedelta(seconds=Node.ttl_hours) >= now:
                expired.append(node)

        ready = Node.get_by_state(Node.State.READY)
        for node in launched:
            # TODO, change to HOURS after done with demo
            if node.date_ready + timedelta(seconds=Node.ttl_hours) >= now:
                expired.append(node)

        return expired

    def set_state(self, state):
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
        else:
            raise Exception("Cannot transition from state {} to {}".format(self.state, state))



class ClusterModel(object):
    """
    Represents information about a launched, active, or recently deleted cluster.
    """

    class STATE:
        INITIALIZING = "INITIALIZING"
        READY = "READY"
        DELETING = "DELETING"
        DELETED = "DELETED"

    def __init__(self, cloud_provider, id, name, state, internal_state, date_created, date_ready):
        """

        :param cloud_provider: Cloud Provider name (str)
        :param id: Cluster ID (str)
        :param name: Cluster name (str)
        :param state: Cluster STATE
        :param internal_state: Internal state given by the Cloud Provider
        :param date_created: Python DateTime of when it was created
        :param date_ready: Python DateTime of when it was ready (could be None)
        """
        self.cloud_provider = cloud_provider
        self.id = id
        self.name = name
        self.state = state
        self.internal_state = internal_state
        self.date_created = date_created
        self.date_ready = date_ready

        # Common tags like User/Owner
        self._tags_dict = {}

        # Additional ad-hoc properties
        self._props_dict = {}

    def set_tags(self, tags_dict):
        self._tags_dict = tags_dict

    def set_props(self, props_dict):
        self._props_dict = props_dict

    def __repr__(self):
        """
        Return machine-readable representation.
        :return: Return a string
        """
        return "<ClusterModel. Cloud Provider: {}, ID: {}, name: {}, state: {}, internal_state: {}, date_created: {}, date_ready: {}>".\
            format(self.cloud_provider, self.id, self.name, self.state, self.internal_state, self.date_created, self.date_ready
        )

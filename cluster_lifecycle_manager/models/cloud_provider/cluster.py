class Cluster(object):

    class STATE:
        WAITING = "WAITING"

    def __init__(self, cloud_provider, id, name, state, date_created, date_ready):
        self.cloud_provider = cloud_provider
        self.id = id
        self.name = name
        self.state = state
        self.date_created = date_created
        self.date_ready = date_ready
# Python Standard Library imports

# Third-party imports
from abc import ABC

# Local imports


class CloudProviderManager(ABC):
    """
    Represents an interface for all of the Cloud Provider Managers.
    """

    def create_cluster(self, cluster_spec):
        """
        Create a cluster given the ClusterSpecModel.
        :param cluster_spec: Instance of ClusterSpecModel
        :return: Return a 2-tuple of the form <cluster id, request id>
        """
        raise Exception("Unimplemented")

    def list_clusters(self, region):
        """
        Given a region, list all currently active clusters.
        :param region: Region name (str)
        return: Return a list of Cluster instances.
        """
        raise Exception("Unimplemented")

    def get_cluster_info_by_id(self, region, id):
        """
        Given a region and cluster id, return more information about that cluster.
        :param region: Region name (str)
        :param id: Cluster ID (str)
        :return: Return a Cluster instance
        """
        raise Exception("Unimplemented")

    def get_cluster_info_by_name(self, region, name):
        """
        Given a region and cluster name, return more information about that cluster.
        :param region: Region name (str)
        :param name: Cluster Name (str)
        :return: Return a Cluster instance
        """
        raise Exception("Unimplemented")

    def destroy_cluster(self, region, id):
        """
        Destroy a cluster, assuming that it is still active.
        :param region: Region name (str)
        :param id: Cluster ID (str)
        :return: Return a request Id (str)
        """
        raise Exception("Unimplemented")

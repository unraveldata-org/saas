class ClusterSpec(object):

    def __init__(self, cloud_provider_name, cluster_name, cluster_type, stack_version, user, region=None,
                 head_node_type=None, num_head_nodes=1, worker_node_type=None, num_worker_nodes=1,
                 services=None, root_volume_size_gb=10, master_volume_size_gb=20, worker_volume_size_gb=20, tags=None):
        """

        :param cloud_provider_name:
        :param cluster_name:
        :param cluster_type:
        :param stack_version:
        :param user:
        :param region:
        :param head_node_type:
        :param num_head_nodes:
        :param worker_node_type:
        :param num_worker_nodes:
        :param services:
        :param root_volume_size_gb: in GiB
        :param master_volume_size_gb: in GiB
        :param worker_volume_size_gb: in GiB
        :param tags:
        """
        self.cloud_provider_name = cloud_provider_name
        self.cluster_name = cluster_name
        self.cluster_type = cluster_type

        self.stack_version = stack_version
        self._effective_stack_version = None

        # User submitting the request
        self.user = user

        self.region = region

        self.head_node_type = head_node_type
        self.num_head_nodes = num_head_nodes
        self.worker_node_type = worker_node_type
        self.num_worker_nodes = num_worker_nodes

        # The input services is a list of 2-tuples of the form (Service name, and version)
        # If version is None, will pick the default or latest version.
        self.services = services if services is not None else []

        self.root_volume_size_gb = root_volume_size_gb
        self.master_volume_size_gb = master_volume_size_gb
        self.worker_volume_size_gb = worker_volume_size_gb

        self._vpc = None
        self._network_region = None
        self._subnet = None

        # Map of key-value pairs.
        # We will typically always add the cluster name and the owner anyways later on.
        self.tags = tags if tags is not None else {}

    def set_network(self, vpc, network_region, subnet):
        """
        :param vpc: VPC Name
        :param network_region:

        :param subnet: Subnet
        :return:
        """
        self._vpc = vpc
        self._network_region = network_region
        self._subnet = subnet

    def __repr__(self):
        """
        Return machine-readable representation.
        :return: Return a string
        """
        return "<ClusterSpec. cloud_provider_name: {}, cluster_name: {}, cluster_type: {}, stack_version: {}, " \
               "effective_stack_version: {}, user: {}, region: {}, head_node_type: {}, num_head_nodes: {}, " \
               "worker_node_type: {}, num_worker_nodes: {}, services: {}, " \
               "master_volume_size_gb: {}, worker_volume_size_gb: {}, " \
               "vpc: {}, network_region: {}, subnet: {}, tags: {}>".format(
            self.cloud_provider_name, self.cluster_name, self.cluster_type, self.stack_version, self.user,
            self._effective_stack_version, self.region, self.head_node_type, self.num_head_nodes,
            self.worker_node_type, self.num_worker_nodes, self.services,
            self.master_volume_size_gb, self.worker_volume_size_gb,
            self._vpc, self._network_region, self._subnet, self.tags
        )

    def validate(self):
        # TODO, a bunch of asserts that all values are within a reasonable range.
        assert self.user is not None
        assert self.region is not None
        assert len(self.services) > 0
        assert self.master_volume_size_gb >= 5
        assert self.worker_volume_size_gb >= 5

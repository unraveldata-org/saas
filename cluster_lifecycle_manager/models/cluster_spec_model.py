# Python standard library imports
import re

# Third-party imports

# Local imports (which should try to avoid in this file)
from saas.cluster_lifecycle_manager.models.constants import SERVICE


class ClusterSpecModel(object):

    ALLOWED_TAG_REGEX  = re.compile(r"[a-zA-Z0-9\s_\.:/=+\\-\\\\]+", re.IGNORECASE)

    def __init__(self, cloud_provider, cluster_name, cluster_type, stack_version, user, region=None,
                 head_node_type=None, num_head_nodes=1, worker_node_type=None, num_worker_nodes=1,
                 services=None, root_volume_size_gb=10, master_volume_size_gb=20, worker_volume_size_gb=20, tags=None):
        """
        Represents a request to create a cluster with as much information as possible.
        However, any missing info will use default values.

        :param cloud_provider: Desired Cloud Provider name (str)
        :param cluster_name: Desired cluster name (str). If None, will auto-assign one.
        :param cluster_type: Desired enum of CLUSTER_TYPE. If DEFAULT, will pick one based on the Cloud Provider
        :param stack_version: Desired specific stack version (str), or enum like STACK_VERSION.LATEST, STACK_VERSION.STABLE
        :param user: Username submitting the request (str)
        :param region: Desired region name (str). If None, will pick a default one.
        :param head_node_type: Head Node VM type (str). If None, will pick a default one.
        :param num_head_nodes: Number of Head Nodes. If None, will pick a default value >= 1.
        :param worker_node_type: Worker Node VM type (str). If None, will pick a default one.
        :param num_worker_nodes: Number of Worker Nodes. If None, will pick a default value >= 1.
        :param services: List of services info. Each element is a 2-tuple of the form (service name (str), service version).
        service_version is either a string or None to pick the latest version.
        :param root_volume_size_gb: Root volume size in GiB
        :param master_volume_size_gb: Master volume size in GiB
        :param worker_volume_size_gb: Worker volume size in GiB
        :param tags: Dictionary of tags to add, which are useful for tracking the cluster later.
        """
        self.cloud_provider = cloud_provider
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

        # These are set via a different method call
        self._vpc = None
        self._network_region = None
        self._subnet = None

        # Map of key-value pairs.
        # We will typically always add the cluster name and the owner anyways later on.
        self.tags = tags if tags is not None else {}

    def set_network(self, vpc, network_region, subnet):
        """
        Set the network settings like the VPC, network region, and the subnet.
        :param vpc: VPC Name (str). E.g., vpc-c3d079a4
        :param network_region: Availability zone (str).
        :param subnet: Subnet (str). This depends on the network region.
        """
        self._vpc = vpc
        self._network_region = network_region
        self._subnet = subnet

    def __repr__(self):
        """
        Return machine-readable representation.
        :return: Return a string
        """
        return "<ClusterSpecModel. cloud_provider: {}, cluster_name: {}, cluster_type: {}, stack_version: {}, " \
               "effective_stack_version: {}, user: {}, region: {}, head_node_type: {}, num_head_nodes: {}, " \
               "worker_node_type: {}, num_worker_nodes: {}, services: {}, " \
               "root_volume_size_gb: {}, master_volume_size_gb: {}, worker_volume_size_gb: {}, " \
               "vpc: {}, network_region: {}, subnet: {}, tags: {}>".format(
            self.cloud_provider, self.cluster_name, self.cluster_type, self.stack_version,
            self._effective_stack_version, self.user, self.region, self.head_node_type, self.num_head_nodes,
            self.worker_node_type, self.num_worker_nodes, self.services,
            self.root_volume_size_gb, self.master_volume_size_gb, self.worker_volume_size_gb,
            self._vpc, self._network_region, self._subnet, self.tags
        )

    def validate(self):
        """
        Perform some validation that after the ClusterSpecModel has been resolved by
        one of the CloudProviders, that some of the fields are present.
        """
        # TODO, add more asserts
        assert self.user is not None
        assert self.region is not None
        assert len(self.services) > 0
        assert self.root_volume_size_gb >= 5
        assert self.master_volume_size_gb >= 5
        assert self.worker_volume_size_gb >= 5

        # Check that the tags are properly sanitized.
        for (k, v) in self.tags.items():
            m = self.ALLOWED_TAG_REGEX.match(v)
            if not m:
                raise Exception("Tag {} has an unsupported value: {}. "
                                "Tag values may only contain unicode letters, digits, whitespace, or one of these symbols: "
                                "'_ . : / = + \\ -'".format(k, v))

    @classmethod
    def create_from_db_cluster_spec(cls, record):
        # TODO, Make sure to filter for only the services available overall.
        raw_services = record.services.split(",")
        raw_services = [x.strip() for x in raw_services]

        services = []
        for service_name in raw_services:

            for potential_match in SERVICE.ALL:
                if service_name.lower() == potential_match.lower():
                    services.append((potential_match, None))
                    break

        tags = {
            "Owner": record.user
        }

        # TODO, missing a lot of other params here.
        model = ClusterSpecModel(record.cloud_provider, record.cluster_name, record.cluster_type, record.stack_version,
                                 record.user, record.region, record.head_node_type, record.num_head_nodes,
                                 record.worker_node_type, record.num_worker_nodes, services=services, tags=tags)

        return model

# Python Standard Library imports
import re

# Third-party imports

# Local imports
from saas.cluster_lifecycle_manager.models.cloud_provider.mapping import CloudProviderMapping
from saas.cluster_lifecycle_manager.models.constants import CLUSTER_TYPE, STACK_VERSION


class CloudProvider(object):
    """
    Represents a class with mostly classmethods in order to perform cluster lifecycle commands.
    It is meant to support EMR, HDI, DataProc.
    The methods in this class serve as as an interface so that the actual implementation of say EMR
    can chose to use whatever library or templates it wants (e.g., boto3, Cloud Formation Template, or Terraform).

    """
    """
    Mapping from the Cloud Provider to the default node type and storage information to use.
    """

    class NAME:
        EMR = "EMR"
        HDI = "HDI"
        DATAPROC = "DATAPROC"

        ALL = [EMR, HDI, DATAPROC]

    @classmethod
    def resolve_spec(cls, cluster_spec):
        """
        Given a ClusterSpecModel object, modify some of the requested fields based on the configs of the chosen
        Cloud Provider, e.g., stack version, region, head node type, worker node type, etc.
        :param cluster_spec: Instance of ClusterSpecModel that will be modified.
        :return: Will not return anything, but may raise an Exception if the ClusterSpecModel object ask for
        an invalid config.
        """
        if cluster_spec.cloud_provider not in cls.NAME.ALL:
            raise Exception("Cloud Provider name {} must be one of {}".
                            format(cluster_spec.cloud_provider, ", ".join(cls.NAME.ALL)))

        # Dynamically determine which config we should use
        cp_config_clazz = CloudProviderMapping.NAME_TO_CONFIG_CLASS[cluster_spec.cloud_provider]

        if cluster_spec.cluster_type.upper() == CLUSTER_TYPE.DEFAULT.upper():
            cluster_spec.cluster_type = cp_config_clazz.DEFAULT_CLUSTER_TYPE

        if cluster_spec.cluster_type.upper() not in cp_config_clazz.CLUSTER_TYPES:
            raise Exception("Invalid cluster type: {}, must be one of {}".format(
                cluster_spec.cluster_type, ", ".join(cp_config_clazz.CLUSTER_TYPES)
            ))

        if cluster_spec.stack_version.upper() in [STACK_VERSION.LATEST.upper(), STACK_VERSION.STABLE.upper()]:
            cluster_spec._effective_stack_version = cp_config_clazz.VERSIONS[cluster_spec.stack_version.upper()]
        else:
            # Assume it is a specific version
            if cluster_spec.stack_version not in cp_config_clazz.STACK_VERSIONS:
                raise Exception("Stack version {} is not supported by {}".format(cluster_spec.stack_version, cls.NAME))

            cluster_spec._effective_stack_version = cluster_spec.stack_version
            cluster_spec.stack_version = STACK_VERSION.SPECIFIC

        if cluster_spec.region is None:
            cluster_spec.region = cp_config_clazz.DEFAULT_REGION

        if cluster_spec.region not in cp_config_clazz.SUPPORTED_REGIONS.keys():
            raise Exception("Unsupported region: {}, must be one of {}".format(
                cluster_spec.region, ", ".join(cp_config_clazz.SUPPORTED_REGIONS.keys())
            ))

        if cluster_spec.head_node_type is None or cluster_spec.head_node_type.upper() == "DEFAULT":
            cluster_spec.head_node_type = cp_config_clazz.DEFAULT_HEAD_NODE_TYPE
        else:
            if not cls._is_vm_type_supported(cp_config_clazz, cluster_spec.head_node_type):
                raise Exception("Head Node type {} is not supported".format(cluster_spec.head_node_type))

        if cluster_spec.worker_node_type is None or cluster_spec.worker_node_type.upper() == "DEFAULT":
            cluster_spec.worker_node_type = cp_config_clazz.DEFAULT_WORKER_NODE_TYPE
        else:
            if not cls._is_vm_type_supported(cp_config_clazz, cluster_spec.worker_node_type):
                raise Exception("Worker Node type {} is not supported".format(cluster_spec.worker_node_type))

        # May also need to apply Network-specific settings
        vpc, preferred_az, preferred_subnet = cp_config_clazz.get_network_settings(cluster_spec.region)
        cluster_spec.set_network(vpc, preferred_az, preferred_subnet)

    @classmethod
    def _is_vm_type_supported(cls, cp_config_clazz, vm_type):
        """
        Internal helper function to ensure that the desired vm type is supported by that Cloud Provider.
        :param cp_config_clazz: Reference to the config class for that Cloud Provider
        :param vm_type: Desired VM type (str)
        :return: Return True if there is a match, otherwise, return False.
        """
        # Ensure it matches at least one of the types
        matches = False
        for elem in cp_config_clazz.SUPPORTED_INSTANCE_TYPES:
            if type(elem) == str:
                if vm_type == elem:
                    matches = True
                    break
            elif type(elem) == re.Pattern:
                m = elem.match(vm_type)
                if m:
                    matches = True
                    break
        return matches

    @classmethod
    def create_cluster(cls, cluster_spec):
        """
        Create a cluster given the ClusterSpecModel.
        :param cluster_spec: Instance of ClusterSpecModel
        :return: Return a 2-tuple of the form <cluster id, request id>
        """
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cluster_spec.cloud_provider]
        cp_manager = cp_manager_clazz()
        return cp_manager.create_cluster(cluster_spec)

    @classmethod
    def list_clusters(cls, cloud_provider, region):
        """
        Given a Cloud Provider name and a region, list all currently active clusters.
        :param cloud_provider: Cloud Provider name (str)
        :param region: Region name (str)
        :return: Return a list of Cluster instances.
        """
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cloud_provider]
        cp_manager = cp_manager_clazz()
        return cp_manager.list_clusters(region)

    @classmethod
    def get_cluster_info_by_id(cls, cloud_provider, region, id):
        """
        Given a Cloud Provider name, region, and cluster id, return more information about that cluster.
        :param cloud_provider: Cloud Provider name (str)
        :param region: Region name (str)
        :param id: Cluster ID (str)
        :return: Return a JSON response that depends on the format used by the Cloud Provider.
        """
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cloud_provider]
        cp_manager = cp_manager_clazz()
        return cp_manager.get_cluster_info_by_id(region, id)

    @classmethod
    def get_cluster_info_by_name(cls, cloud_provider, region, name):
        """
        Given a Cloud Provider name, region, and cluster name, return more information about that cluster.
        :param cloud_provider: Cloud Provider name (str)
        :param region: Region name (str)
        :param name: Cluster Name (str)
        :return: Return a JSON response that depends on the format used by the Cloud Provider.
        """
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cloud_provider]
        cp_manager = cp_manager_clazz()
        return cp_manager.get_cluster_info_by_name(region, name)

    @classmethod
    def destroy_cluster(cls, cloud_provider, region, id):
        """
        Destroy a cluster, assuming that it is still active.
        :param cloud_provider: Cloud Provider name (str)
        :param region: Region name (str)
        :param id: Cluster ID (str)
        :return: Return the request ID
        """
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cloud_provider]
        cp_manager = cp_manager_clazz()

        # TODO, perhaps check that it is active first.
        return cp_manager.destroy_cluster(region, id)

from abc import abstractmethod
import re

from saas.cluster_lifecycle_manager.models.cloud_provider.mapping import CloudProviderMapping
from saas.cluster_lifecycle_manager.models.constants import CLUSTER_TYPE, STACK_VERSION


class CloudProvider(object):

    class NAME:
        EMR = "EMR"
        HDI = "HDI"
        DATAPROC = "DATAPROC"

        ALL = [EMR, HDI, DATAPROC]

    @classmethod
    def resolve_spec(cls, cluster_spec):
        if cluster_spec.cloud_provider_name not in cls.NAME.ALL:
            raise Exception("Cloud Provider name {} must be one of {}".
                            format(cluster_spec.cloud_provider_name, ", ".join(cls.NAME.ALL)))

        # Dynamically determine which config we should use
        cp_config_clazz = CloudProviderMapping.NAME_TO_CONFIG_CLASS[cluster_spec.cloud_provider_name]

        if cluster_spec.cluster_type == CLUSTER_TYPE.DEFAULT:
            cluster_spec.cluster_type = cp_config_clazz.DEFAULT_CLUSTER_TYPE

        if cluster_spec.cluster_type not in cp_config_clazz.CLUSTER_TYPES:
            raise Exception("Invalid cluster type: {}, must be one of {}".format(
                cluster_spec.cluster_type, ", ".join(cp_config_clazz.CLUSTER_TYPES)
            ))

        if cluster_spec.stack_version in [STACK_VERSION.LATEST, STACK_VERSION.STABLE]:
            cluster_spec._effective_stack_version = cp_config_clazz.VERSIONS[cluster_spec.stack_version]
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

        if cluster_spec.head_node_type is None:
            cluster_spec.head_node_type = cp_config_clazz.DEFAULT_HEAD_NODE_TYPE
        else:
            if not cls._is_vm_type_supported(cp_config_clazz, cluster_spec.head_node_type):
                raise Exception("Head Node type {} is not supported".format(cluster_spec.head_node_type))

        if cluster_spec.worker_node_type is None:
            cluster_spec.worker_node_type = cp_config_clazz.DEFAULT_WORKER_NODE_TYPE
        else:
            if not cls._is_vm_type_supported(cluster_spec.head_node_type):
                raise Exception("Head Node type {} is not supported".format(cluster_spec.head_node_type))

    def _is_vm_type_supported(cls, cp_config_clazz, vm_type):
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
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cluster_spec.cloud_provider_name]
        cp_manager = cp_manager_clazz()
        cp_manager.create_cluster(cluster_spec)

    @classmethod
    def list_clusters(cls, cloud_provider_name, region):
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cloud_provider_name]
        cp_manager = cp_manager_clazz()
        return cp_manager.list_clusters(region)

    @classmethod
    def get_cluster_info_by_id(cls, cloud_provider_name, region, id):
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cloud_provider_name]
        cp_manager = cp_manager_clazz()
        return cp_manager.get_cluster_info_by_id(region, id)

    @classmethod
    def get_cluster_info_by_name(cls, cloud_provider_name, region, name):
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cloud_provider_name]
        cp_manager = cp_manager_clazz()
        return cp_manager.get_cluster_info_by_name(region, name)

    @classmethod
    def destroy_cluster(cls, cloud_provider_name, region, id):
        # Dynamically determine which manager we should use
        cp_manager_clazz = CloudProviderMapping.NAME_TO_MANAGER_CLASS[cloud_provider_name]
        cp_manager = cp_manager_clazz()
        return cp_manager.destroy_cluster(region, id)
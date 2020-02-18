# Python standard library imports

# Third-party imports

# Local imports
from saas.cluster_lifecycle_manager.models.cloud_provider.config import EMRConfig, HDIConfig
from saas.cluster_lifecycle_manager.models.cloud_provider.manager.emr_manager import EMRManager
from saas.cluster_lifecycle_manager.models.cloud_provider.manager.hdi_manager import HDIManager


class CloudProviderMapping(object):
    """
    Given a Cloud Provider, determine which config and manager to load.
    """
    NAME_TO_CONFIG_CLASS = {
        "EMR": EMRConfig,
        "HDI": HDIConfig
    }

    NAME_TO_MANAGER_CLASS = {
        "EMR": EMRManager,
        "HDI": HDIManager
    }

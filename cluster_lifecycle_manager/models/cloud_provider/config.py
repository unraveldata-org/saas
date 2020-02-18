# Python Standard Library imports
import re

# Third-party imports
from abc import ABC

# Local imports
from saas.cluster_lifecycle_manager.models.constants import CLUSTER_TYPE, STACK_VERSION


class CloudProviderConfig(ABC):
    """
    Template for all of the configs needed by a Cloud Provider
    """
    def __init__(self):
        raise Exception("CloudProviderConfig is meant to be an Abstract final class that can only be extended.")

    NAME = "MISSING"

    DEFAULT_CLUSTER_TYPE = CLUSTER_TYPE.DEFAULT
    CLUSTER_TYPES = []

    STACK_VERSIONS = []

    VERSIONS = {
        STACK_VERSION.LATEST: "",
        STACK_VERSION.STABLE: ""
    }

    DEFAULT_REGION = "DEFAULT_REGION"
    # Mapping from ID to display name
    SUPPORTED_REGIONS = {"DEFAULT_REGION": "DEFAULT_REGION",
                         }

    # Supports both exact string comparison and regex matching
    # https://aws.amazon.com/ec2/instance-types/
    SUPPORTED_INSTANCE_TYPES = ["medium", "large", re.compile(".*", re.IGNORECASE)]

    DEFAULT_HEAD_NODE_TYPE = "large"
    DEFAULT_NUM_HEAD_NODES = 1

    DEFAULT_WORKER_NODE_TYPE = "large"
    DEFAULT_NUM_WORKER_NODES = 2

    SSH_KEY_NAME = "TODO"

    @classmethod
    def get_network_settings(cls, region):
        """
        Given a region, return the VPC, Availability Zone, and Subnet
        :param region: Region name
        :return: Return a 3-tuple of <VPC (str), Availability Zone (str), and Subnet (str)> for that region.
        """
        raise Exception("Unimplemented")
        #return (None, None, None)


# TODO, move all of this into JSON that we can parse.
class EMRConfig(CloudProviderConfig):

    NAME = "EMR"

    DEFAULT_CLUSTER_TYPE = CLUSTER_TYPE.HADOOP
    CLUSTER_TYPES = [CLUSTER_TYPE.HADOOP]

    STACK_VERSIONS = ["5.29.0", "5.28.1", "5.28.0", "5.27.0"]

    VERSIONS = {
        STACK_VERSION.LATEST.upper(): "5.29.0",
        STACK_VERSION.STABLE.upper(): "5.28.1"
    }

    DEFAULT_REGION = "us-east-1"
    # Mapping from ID to display name
    SUPPORTED_REGIONS = {"us-east-1": "US East (N. Virginia)",
                         "us-east-2": "US East (Ohio)",
                         "us-west-1": "US West (N. California)",
                         "us-west-2": "US West (Oregon)"
                        }

    # Supports both exact string comparison and regex matching
    # https://aws.amazon.com/ec2/instance-types/
    SUPPORTED_INSTANCE_TYPES = ["m3.xlarge", "m3.2xlarge",
                                re.compile("[cdghimprsz]{1,2}\d[adns]?\.\d*x?((medium)|(large))", re.IGNORECASE)]

    # 8 CPU and 64 GB RAM, EBS only
    DEFAULT_HEAD_NODE_TYPE = "r5.2xlarge"
    DEFAULT_NUM_HEAD_NODES = 1

    # 8 CPU and 16 GB or RAM, EBS only
    DEFAULT_WORKER_NODE_TYPE = "c5.2xlarge"
    DEFAULT_NUM_WORKER_NODES = 2

    SSH_KEY_NAME = "topcat"

    @classmethod
    def get_network_settings(cls, region):
        """
        Given a region, return the VPC, Availability Zone, and Subnet
        :param region: Region name
        :return: Return a 3-tuple of <VPC (str), Availability Zone (str), and Subnet (str)> for that region.
        """
        # TODO, this entire function body needs to change.

        # 172.31.0.0/16
        vpc = "vpc-c3d079a4"

        # This depends on the vpc, so it is specific to "vpc-c3d079a4"
        # availability zone
        aws_az_to_subnets = {
            "us-east-1a": ["subnet-4c673614"],
            "us-east-1c": ["subnet-e54410cf", "subnet-0f1d2a669de9a7c04"],  # This one is preferred
            "us-east-1d": ["subnet-096575bcc73ff63f9", "subnet-9c383cea"],
            "us-east-1e": ["subnet-869caabb", "subnet-02fcce011320639c2"]
        }

        preferred_az = "us-east-1c"
        preferred_subnet = aws_az_to_subnets[preferred_az][0]

        return (vpc, preferred_az, preferred_subnet)


class HDIConfig(CloudProviderConfig):

    NAME = "HDI"

    DEFAULT_CLUSTER_TYPE = CLUSTER_TYPE.HADOOP
    CLUSTER_TYPES = [CLUSTER_TYPE.HADOOP, CLUSTER_TYPE.SPARK, CLUSTER_TYPE.INTERACTIVE_QUERY, CLUSTER_TYPE.KAFKA,
                     CLUSTER_TYPE.STORM, CLUSTER_TYPE.HBASE]

    STACK_VERSIONS = ["4.0", "3.6"]

    VERSIONS = {
        STACK_VERSION.LATEST.upper(): "4.0",
        STACK_VERSION.STABLE.upper(): "4.0"
    }

    DEFAULT_REGION = "East US"
    # Mapping from ID to display name
    SUPPORTED_REGIONS = {"East US": "East US",
                         "Central US": "Central US",
                         "West Central US": "West Central US",
                         "West US": "West US"
                        }

    # Supports both exact string comparison and regex matching
    # https://azure.microsoft.com/en-in/pricing/details/hdinsight/
    SUPPORTED_INSTANCE_TYPES = ["E2 v3",
                                re.compile("[ADEF]\d+m?( v\d+)?", re.IGNORECASE)]

    DEFAULT_HEAD_NODE_TYPE = "A8 v2"
    DEFAULT_NUM_HEAD_NODES = 1
    DEFAULT_WORKER_NODE_TYPE = "D4 v2"
    DEFAULT_NUM_WORKER_NODES = 2

    # TODO
    SSH_KEY_NAME = None

    @classmethod
    def get_network_settings(cls, region):
        """
        Given a region, return the VPC, Availability Zone, and Subnet
        :param region: Region name
        :return: Return a 3-tuple of <VPC (str), Availability Zone (str), and Subnet (str)> for that region.
        """
        raise Exception("Unimplemented")
        #return (None, None, None)

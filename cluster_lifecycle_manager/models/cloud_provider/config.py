import re

from saas.cluster_lifecycle_manager.models.constants import CLUSTER_TYPE, STACK_VERSION

# TODO, move all of this into JSON that we can parse.
class EMRConfig(object):

    NAME = "EMR"

    DEFAULT_CLUSTER_TYPE = CLUSTER_TYPE.HADOOP
    CLUSTER_TYPES = [CLUSTER_TYPE.HADOOP]

    STACK_VERSIONS = ["5.29.0", "5.28.1", "5.28.0", "5.27.0"]

    VERSIONS = {
        STACK_VERSION.LATEST: "5.29.0",
        STACK_VERSION.STABLE: "5.28.1"
    }

    DEFAULT_REGION = "us-east-1"
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


class HDIConfig(object):

    NAME = "HDI"

    DEFAULT_CLUSTER_TYPE = CLUSTER_TYPE.HADOOP
    CLUSTER_TYPES = [CLUSTER_TYPE.HADOOP, CLUSTER_TYPE.SPARK, CLUSTER_TYPE.INTERACTIVE_QUERY, CLUSTER_TYPE.KAFKA,
                     CLUSTER_TYPE.STORM, CLUSTER_TYPE.HBASE]

    STACK_VERSIONS = ["4.0", "3.6"]

    VERSIONS = {
        STACK_VERSION.LATEST: "4.0",
        STACK_VERSION.STABLE: "4.0"
    }

    # TODO, populate with proper values for HDI
    DEFAULT_REGION = "us-east-1"
    SUPPORTED_REGIONS = {"us-east-1": "US East (N. Virginia)",
                         "us-east-2": "US East (Ohio)",
                         "us-west-1": "US West (N. California)",
                         "us-west-2": "US West (Oregon)"
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

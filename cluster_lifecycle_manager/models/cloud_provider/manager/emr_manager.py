# Python Standard Library imports
import datetime
from dateutil.tz import tzlocal

# Third party imports
import boto3

# Local imports
from saas.cluster_lifecycle_manager.models.cloud_provider.manager.cloud_provider_manager import CloudProviderManager
from saas.cluster_lifecycle_manager.models.cloud_provider.config import EMRConfig
from saas.cluster_lifecycle_manager.models.cluster_model import ClusterModel

from saas.cluster_lifecycle_manager.models.constants import MARKET_TYPE
from saas.cluster_lifecycle_manager.utils import Utils


class EMRManager(CloudProviderManager):
    """
    See https://github.com/unraveldata-org/devops/blob/master/unravel-emr-ansible/tests/emr_helper.py
    as a reference

    For boto3, see
    https://docs.aws.amazon.com/emr/latest/APIReference/API_ListClusters.html
    Internal cluster states: STARTING | BOOTSTRAPPING | RUNNING | WAITING | TERMINATING | TERMINATED | TERMINATED_WITH_ERRORS

    https://docs.aws.amazon.com/emr/latest/APIReference/API_DescribeCluster.html
    """

    CLOUD_PROVIDER_NAME = "EMR"

    class STATE:
        STARTING = "STARTING"
        BOOTSTRAPPING = "BOOTSTRAPPING"
        RUNNING = "RUNNING"
        WAITING = "WAITING"
        TERMINATING = "TERMINATING"
        TERMINATED = "TERMINATED"
        TERMINATED_WITH_ERRORS = "TERMINATED_WITH_ERRORS"

        INIT_STATES = [STARTING, BOOTSTRAPPING]
        READY_STATES = [RUNNING, WAITING]
        DELETING_STATES = [TERMINATING]
        DELETED_STATES = [TERMINATED, TERMINATED_WITH_ERRORS]

    INTERNAL_STATE_TO_CLUSTER_STATE = {
        STATE.STARTING: ClusterModel.STATE.INITIALIZING,
        STATE.BOOTSTRAPPING: ClusterModel.STATE.INITIALIZING,
        STATE.RUNNING: ClusterModel.STATE.READY,
        STATE.WAITING: ClusterModel.STATE.READY,
        STATE.TERMINATING: ClusterModel.STATE.DELETING,
        STATE.TERMINATED: ClusterModel.STATE.DELETED,
        STATE.TERMINATED_WITH_ERRORS: ClusterModel.STATE.DELETED
    }

    def __init__(self):
        self.client = boto3.client("emr", region_name=EMRConfig.DEFAULT_REGION)
        self.logger = Utils.get_logger("EMRManager")

    @staticmethod
    def _get_applications(cluster_spec):
        """
        Internal helper function to map the ClusterSpecModel services into a dictionary where each element is of the form:
        {"Name": $name"}

        :param cluster_spec: Instance of ClusterSpecModel
        :return: Return a dictionary of service names
        """
        app_list = []
        for (name, version) in cluster_spec.services:
            app_list.append({"Name": name.capitalize()})
        return app_list

    @classmethod
    def _get_ebs_config(cls, volume_size_gb, num_volumes=1):
        """
        Get the EBS Volume config given the size in GiB.
        :param volume_size_gb: Size in GiB (int)
        :param num_volumes: Number of volumes (int), which defaults to 1.
        :return: Return a dictionary with metadata about the EBS Volume.
        """
        ebs_dict = {
            "EbsBlockDeviceConfigs": [
                {
                    "VolumeSpecification": {
                        "VolumeType": "gp2",
                        "SizeInGB": volume_size_gb
                    },
                    "VolumesPerInstance": num_volumes
                }
            ],
            "EbsOptimized": True
        }
        return ebs_dict

    @classmethod
    def _get_instance_template(cls, cluster_spec):
        """
        Get the master template used by boto3 to construct a cluster.
        :param cluster_spec: Instance of ClusterSpecModel
        :return: Return the dictionary with the template to create the cluster.
        """
        ssh_key_name = EMRConfig.SSH_KEY_NAME
        assert ssh_key_name is not None

        instance_template = {
            "InstanceGroups": [
                {
                    "Name": "Master nodes",
                    "Market": MARKET_TYPE.ON_DEMAND,
                    "InstanceRole": "MASTER",
                    "InstanceType": cluster_spec.head_node_type,
                    "InstanceCount": cluster_spec.num_head_nodes,
                    "EbsConfiguration": cls._get_ebs_config(cluster_spec.master_volume_size_gb)
                },
                {
                    "Name": "Slave nodes",
                    "Market": MARKET_TYPE.ON_DEMAND,
                    "InstanceRole": "CORE",  # Not adding any "TASK" nodes at all
                    "InstanceType": cluster_spec.worker_node_type,
                    "InstanceCount": cluster_spec.num_worker_nodes,
                    "EbsConfiguration": cls._get_ebs_config(cluster_spec.worker_volume_size_gb)
                }
            ],
            "Ec2KeyName": ssh_key_name,
            "KeepJobFlowAliveWhenNoSteps": True,
            "TerminationProtected": False,
            "Ec2SubnetId": cluster_spec._subnet
        }

        # TODO, add bootstrap action.
        return instance_template

    def create_cluster(self, cluster_spec):
        """
        Create a cluster given the ClusterSpecModel.
        :param cluster_spec: Instance of ClusterSpecModel
        :return: Return a 2-tuple of the form <cluster id, request id>
        """
        self.logger.info("Creating {} Cluster {} from spec:\n{}".format(
            cluster_spec.cloud_provider, cluster_spec.cluster_name, cluster_spec))

        # list of service metadata
        app_list = []

        # Bootstrap actions
        # TODO, populate bootstrap actions
        bsa_list = []

        # Always add a tag for the cluster name and the owner
        tags = cluster_spec.tags if cluster_spec.tags is not None else {}

        # Cluster name and user
        tags["Name"] = cluster_spec.cluster_name
        tags["Owner"] = cluster_spec.user
        # TODO, put env name, note that only some values are allowed in tags.
        tags["Purpose"] = "SaaS Free Trial testing in environment PROD launched by emr_manager.py"

        tags_list = [{"Key": k, "Value": v} for k,v in tags.items()]

        # TODO, move some of these to constants
        kwargs = {
            "Name": cluster_spec.cluster_name,
            "LogUri": "s3://aws-logs-217619106665-us-east-1/elasticmapreduce/",
            "ReleaseLabel": "emr-{0}".format(cluster_spec._effective_stack_version),
            "Applications": EMRManager._get_applications(cluster_spec),
            "BootstrapActions": bsa_list,
            "Instances": EMRManager._get_instance_template(cluster_spec),
            "VisibleToAllUsers": True,
            "JobFlowRole": "EMR_EC2_DefaultRole",
            "ServiceRole": "EMR_DefaultRole",
            "EbsRootVolumeSize": cluster_spec.root_volume_size_gb,
            "Tags": tags_list
        }

        # TODO, this also needs to use the client specific to that region.
        response = self.client.run_job_flow(**kwargs)
        '''
        {'JobFlowId': 'j-1UYMQJJE7KJD8', 
        'ClusterArn': 'arn:aws:elasticmapreduce:us-east-1:217619106665:cluster/j-1UYMQJJE7KJD8', 
        'ResponseMetadata': {
          'RequestId': 'bf8934ac-061a-4ad9-afdf-93c5f4c18def', 
          'HTTPStatusCode': 200, 
          'HTTPHeaders': {
            'x-amzn-requestid': 'bf8934ac-061a-4ad9-afdf-93c5f4c18def', 
            'content-type': 'application/x-amz-json-1.1', 
            'content-length': '118', 
            'date': 'Tue, 25 Feb 2020 06:57:17 GMT'
          }, 
          'RetryAttempts': 0
          }
        }
        '''
        cluster_id = Utils.safe_get(response, ["JobFlowId"], None)
        request_id = Utils.safe_get(response, ["ResponseMetadata", "RequestId"], None)

        self.logger.info("Successfully created Cluster with id: {}, request: {}".format(cluster_id, request_id))
        return cluster_id, request_id

    def list_clusters(self, region):
        """
        Given a region, list all currently active clusters.
        :param region: Region name (str)
        :return: Return a list of Cluster instances.
        """

        # https://docs.aws.amazon.com/emr/latest/APIReference/API_ListClusters.html
        # TODO, this is currently ignoring the region. since it assumes the client
        # was setup to use it already.

        response = self.client.list_clusters(ClusterStates=(self.STATE.INIT_STATES + self.STATE.READY_STATES))

        # List of dicts
        '''
        {
        'Id': 'j-3AY581YLLQP2D', 
        'Name': 'test_cluster_1', 
        'Status': {
          'State': 'WAITING', 
          'StateChangeReason': {
            'Message': 'Cluster ready to run steps.'
          },
          'Timeline': {
            'CreationDateTime': datetime.datetime(2020, 2, 19, 15, 14, 40, 944000, tzinfo=tzlocal()), 
            'ReadyDateTime': datetime.datetime(2020, 2, 19, 15, 19, 1, 943000, tzinfo=tzlocal())
          }
        }, 
        'NormalizedInstanceHours': 32, 
        'ClusterArn': 'arn:aws:elasticmapreduce:us-east-1:217619106665:cluster/j-3AY581YLLQP2D'
        }
        '''
        raw_data = response["Clusters"]

        clusters = []
        for elem in raw_data:
            internal_state = elem["Status"]["State"]
            cluster_state = self.INTERNAL_STATE_TO_CLUSTER_STATE[internal_state]
            date_created = Utils.safe_get(elem, ["Status", "Timeline", "CreationDateTime"], None)
            date_ready = Utils.safe_get(elem, ["Status", "Timeline", "ReadyDateTime"], None)

            cluster = ClusterModel(self.CLOUD_PROVIDER_NAME, elem["Id"], elem["Name"], cluster_state, internal_state,
                              date_created, date_ready)
            clusters.append(cluster)
        return clusters

    def get_cluster_info_by_id(self, region, id):
        """
        Given a region and cluster id, return more information about that cluster.
        :param region: Region name (str)
        :param id: Cluster ID (str)
        :return: Return a Cluster instance
        """
        response = self.client.describe_cluster(ClusterId=id)

        '''
        {
        'Cluster': {
        'Id': 'j-1UYMQJJE7KJD8', 
        'Name': 'test_cluster_1', 
        'Status': {
          'State': 'WAITING', 
          'StateChangeReason': {
            'Message': 'Cluster ready to run steps.'
          }, 
          'Timeline': {
            'CreationDateTime': datetime.datetime(2020, 2, 25, 12, 27, 17, 718000, tzinfo=tzlocal()), 
            'ReadyDateTime': datetime.datetime(2020, 2, 25, 12, 31, 13, 730000, tzinfo=tzlocal())}
          }, 
          'Ec2InstanceAttributes': {
            'Ec2KeyName': 'topcat', 
            'Ec2SubnetId': 'subnet-e54410cf', 
            'RequestedEc2SubnetIds': ['subnet-e54410cf'],
            'Ec2AvailabilityZone': 'us-east-1c', 
            'RequestedEc2AvailabilityZones': [], 
            'IamInstanceProfile': 'EMR_EC2_DefaultRole', 
            'EmrManagedMasterSecurityGroup': 'sg-deb4dba5', 
            'EmrManagedSlaveSecurityGroup': 'sg-ddb4dba6'
          }, 
          'InstanceCollectionType': 'INSTANCE_GROUP', 
          'LogUri': 's3n://aws-logs-217619106665-us-east-1/elasticmapreduce/', 
          'ReleaseLabel': 'emr-5.29.0', 
          'AutoTerminate': False, 
          'TerminationProtected': False, 
          'VisibleToAllUsers': True, 
          'Applications': [{'Name': 'Hadoop', 'Version': '2.8.5'}, {'Name': 'Hive', 'Version': '2.3.6'}, {'Name': 'Spark', 'Version': '2.4.4'}], 
          'Tags': [
            {'Key': 'owner', 'Value': 'alejandro'}, 
            {'Key': 'Name', 'Value': 'test_cluster_1'}
          ], 
          'ServiceRole': 'EMR_DefaultRole', 
          'NormalizedInstanceHours': 0, 
          'MasterPublicDnsName': 'ec2-54-210-83-141.compute-1.amazonaws.com', 
          'Configurations': [], 
          'ScaleDownBehavior': 'TERMINATE_AT_TASK_COMPLETION', 
          'EbsRootVolumeSize': 10, 
          'KerberosAttributes': {}, 
          'ClusterArn': 'arn:aws:elasticmapreduce:us-east-1:217619106665:cluster/j-1UYMQJJE7KJD8', 
          'StepConcurrencyLevel': 1
        }, 
        'ResponseMetadata': {
          'RequestId': 'bb13e4f1-588d-4ab0-a72b-dc40c18d05c2', 
          'HTTPStatusCode': 200, 
          'HTTPHeaders': {
            'x-amzn-requestid': 'bb13e4f1-588d-4ab0-a72b-dc40c18d05c2', 
            'content-type': 'application/x-amz-json-1.1', 
            'content-length': '1336', 
            'date': 'Tue, 25 Feb 2020 07:38:08 GMT'
          }, 
          'RetryAttempts': 0
        }}
        '''

        cluster_info = response["Cluster"]
        internal_state = cluster_info["Status"]["State"]
        cluster_state = self.INTERNAL_STATE_TO_CLUSTER_STATE[internal_state]
        date_created = Utils.safe_get(cluster_info, ["Status", "Timeline", "CreationDateTime"], None)
        date_ready = Utils.safe_get(cluster_info, ["Status", "Timeline", "ReadyDateTime"], None)

        cluster = ClusterModel(self.CLOUD_PROVIDER_NAME, cluster_info["Id"], cluster_info["Name"], cluster_state, internal_state, date_created, date_ready)

        props_dict = {}
        public_dns_name = Utils.safe_get(cluster_info, ["Status", "MasterPublicDnsName"], None)
        if public_dns_name is not None:
            props_dict["dns_name"] = public_dns_name

        tags_dict = {}
        raw_tags = Utils.safe_get(cluster_info, ["Status", "Tags"], None)
        if raw_tags is not None:
            for elem in raw_tags:
                tags_dict[elem["Key"]] = elem["Value"]

        cluster.set_props(props_dict)
        cluster.set_tags(tags_dict)
        return cluster

    def get_cluster_info_by_name(self, region, name):
        """
        Given a region and cluster name, return more information about that cluster.
        :param region: Region name (str)
        :param name: Cluster Name (str)
        :return: Return a Cluster instance
        """
        raise Exception("Not supported on EMR since it only uses an ID instead of a name")

    def destroy_cluster(self, region, id):
        """
        Destroy a cluster, assuming that it is still active.
        :param region: Region name (str)
        :param id: Cluster ID (str)
        :return: Return the request ID (str) to track this.
        """
        # Status will eventually transition to Terminated
        response = self.client.terminate_job_flows(JobFlowIds=[id])
        '''
        {
        'ResponseMetadata': {
          'RequestId': '8126f20b-fc23-4a7b-a52b-9a680dc7cd19', 
          'HTTPStatusCode': 200, 
          'HTTPHeaders': {
            'x-amzn-requestid': '8126f20b-fc23-4a7b-a52b-9a680dc7cd19', 
            'content-type': 'application/x-amz-json-1.1', 
            'content-length': '0', 
            'date': 'Wed, 19 Feb 2020 12:05:50 GMT'
          }, 
          'RetryAttempts': 0
        }
        }
        '''
        return response["ResponseMetadata"]["RequestId"]

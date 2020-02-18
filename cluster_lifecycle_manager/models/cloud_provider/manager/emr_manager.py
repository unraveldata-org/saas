from saas.cluster_lifecycle_manager.models.cloud_provider.manager.cloud_provider_manager import CloudProviderManager
from saas.cluster_lifecycle_manager.models.cloud_provider.config import EMRConfig

from saas.cluster_lifecycle_manager.models.constants import MARKET_TYPE


# Third party imports
import boto3


class EMRManager(CloudProviderManager):
    """
    See https://github.com/unraveldata-org/devops/blob/master/unravel-emr-ansible/tests/emr_helper.py
    as a reference

    For boto3, see
    https://docs.aws.amazon.com/emr/latest/APIReference/API_ListClusters.html
    Internal cluster states: STARTING | BOOTSTRAPPING | RUNNING | WAITING | TERMINATING | TERMINATED | TERMINATED_WITH_ERRORS

    https://docs.aws.amazon.com/emr/latest/APIReference/API_DescribeCluster.html
    """

    def __init__(self):
        self.client = boto3.client("emr", region_name='us-east-1')

    @staticmethod
    def _get_applications(cluster_spec):
        app_list = []
        for (name, version) in cluster_spec.services:
            app_list.append({"Name": name.capitalize()})
        return app_list

    @classmethod
    def _get_ebs_config(cls, volume_size_gb):
        ebs_dict = {
            "EbsBlockDeviceConfigs": [
                {
                    "VolumeSpecification": {
                        "VolumeType": "gp2",
                        "SizeInGB": volume_size_gb
                    },
                    "VolumesPerInstance": 1
                }
            ],
            "EbsOptimized": True
        }
        return ebs_dict

    @classmethod
    def _get_instance_template(cls, cluster_spec):
        """

        :param cluster_spec:
        :return:
        """
        ssh_key_name = EMRConfig.SSH_KEY_NAME

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
            "Region": cluster_spec.region,
            "Ec2SubnetId": cluster_spec._subnet
        }

        return instance_template

    def create_cluster(self, cluster_spec):
        print("Creating cluster")

        # list of service metadata
        app_list = []

        # Bootstrap actions
        bsa_list = []

        # Always add a tag for the cluster name and the owner
        tags = cluster_spec.tags if cluster_spec.tags is not None else {}

        # Cluster name and user
        tags["Name"] = cluster_spec.cluster_name
        tags["owner"] = cluster_spec.user

        tags_list = [{"Key": k, "Value": v} for k,v in tags.items()]

        kwargs = {
            "Name": cluster_spec.cluster_name,
            "LogUri": 's3://aws-logs-217619106665-us-east-1/elasticmapreduce/',
            "ReleaseLabel": 'emr-{0}'.format(cluster_spec._effective_stack_version),
            "Applications": EMRManager._get_applications(cluster_spec),
            "BootstrapActions": bsa_list,
            "Instances": EMRManager._get_instance_template(cluster_spec),
            "VisibleToAllUsers": True,
            "JobFlowRole": "EMR_EC2_DefaultRole",
            "ServiceRole": "EMR_DefaultRole",
            "EbsRootVolumeSize": cluster_spec.root_volume_size_gb,
            "Tags": tags_list
        }

        print(kwargs)
        # TODO, add support for Kerberos

        cluster_id = self.client.run_job_flow(**kwargs)
        return cluster_id

    def list_clusters(self, region):
        # https://docs.aws.amazon.com/emr/latest/APIReference/API_ListClusters.html
        # TODO, this is currently ignoring the region. since it assumes the client
        # was setup to use it already.
        response = self.client.list_clusters(ClusterStates=['WAITING'])

        # List of dicts
        '''
        {'Id': 'j-3AY581YLLQP2D', 'Name': 'test_cluster_1', 'Status': {'State': 'WAITING', 'StateChangeReason': {'Message': 'Cluster ready to run steps.'}, 'Timeline': {'CreationDateTime': datetime.datetime(2020, 2, 19, 15, 14, 40, 944000, tzinfo=tzlocal()), 'ReadyDateTime': datetime.datetime(2020, 2, 19, 15, 19, 1, 943000, tzinfo=tzlocal())}}, 'NormalizedInstanceHours': 32, 'ClusterArn': 'arn:aws:elasticmapreduce:us-east-1:217619106665:cluster/j-3AY581YLLQP2D'}, {'Id': 'j-JP4RA1SM5BPS', 'Name': '4601-QA', 'Status': {'State': 'WAITING', 'StateChangeReason': {'Message': 'Cluster ready after last step completed.'}, 'Timeline': {'CreationDateTime': datetime.datetime(2020, 2, 19, 13, 43, 49, 915000, tzinfo=tzlocal()), 'ReadyDateTime': datetime.datetime(2020, 2, 19, 13, 50, 31, 207000, tzinfo=tzlocal())}}, 'NormalizedInstanceHours': 144, 'ClusterArn': 'arn:aws:elasticmapreduce:us-east-1:217619106665:cluster/j-JP4RA1SM5BPS'}, {'Id': 'j-225JYGZZNAQ0G', 'Name': 'EMR-5.24.0-automated-bootstrap-andy-202002182122', 'Status': {'State': 'WAITING', 'StateChangeReason': {'Message': 'Cluster ready to run steps.'}, 'Timeline': {'CreationDateTime': datetime.datetime(2020, 2, 19, 10, 52, 37, 439000, tzinfo=tzlocal()), 'ReadyDateTime': datetime.datetime(2020, 2, 19, 11, 2, 0, 431000, tzinfo=tzlocal())}}, 'NormalizedInstanceHours': 96, 'ClusterArn': 'arn:aws:elasticmapreduce:us-east-1:217619106665:cluster/j-225JYGZZNAQ0G'}
        '''
        clusters = response["Clusters"]
        return clusters

    def get_cluster_info_by_id(self, region, id):
        """

        :param region:
        :param id:
        :return:
        """

        response = self.client.describe_cluster(ClusterId=id)

        return response

    def get_cluster_info_by_name(self, region, name):
        raise Exception("Not supported on EMR")

    def destroy_cluster(self, region, id):
        # Status will transition to Terminated
        '''
        {'ResponseMetadata': {'RequestId': '8126f20b-fc23-4a7b-a52b-9a680dc7cd19', 'HTTPStatusCode': 200, 'HTTPHeaders': {'x-amzn-requestid': '8126f20b-fc23-4a7b-a52b-9a680dc7cd19', 'content-type': 'application/x-amz-json-1.1', 'content-length': '0', 'date': 'Wed, 19 Feb 2020 12:05:50 GMT'}, 'RetryAttempts': 0}}
        '''
        response = self.client.terminate_job_flows(JobFlowIds=[id])
        return response

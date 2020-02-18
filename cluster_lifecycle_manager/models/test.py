import os
import sys

parent_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(parent_dir)

from saas.cluster_lifecycle_manager.models.cluster_spec import ClusterSpec
from saas.cluster_lifecycle_manager.models.cloud_provider.cloud_provider import CloudProvider
from saas.cluster_lifecycle_manager.models.constants import CLUSTER_TYPE, STACK_VERSION, SERVICE

region = "us-east-1"
services = [(SERVICE.HADOOP, None), (SERVICE.HIVE, None), (SERVICE.SPARK, None)]
cluster_spec = ClusterSpec(CloudProvider.NAME.EMR, "test_cluster_1", CLUSTER_TYPE.DEFAULT, STACK_VERSION.LATEST, "alejandro",
                           region=region, services=services)
print(cluster_spec)

print("Resolve:")
CloudProvider.resolve_spec(cluster_spec)
print(cluster_spec)

# The subnet has to match the VPC and region. subnet-4c673614,subnet-e54410cf,subnet-869caabb,subnet-9c383cea
# This one is set up for VPC-to-VPC peering

# 172.31.0.0/16
vpc = "vpc-c3d079a4"

# This depends on the vpc, so it is specific to "vpc-c3d079a4"
# availability zone
aws_az_to_subnets = {
    "us-east-1a": ["subnet-4c673614"],
    "us-east-1c": ["subnet-e54410cf", "subnet-0f1d2a669de9a7c04"], # This one is preferred
    "us-east-1d": ["subnet-096575bcc73ff63f9", "subnet-9c383cea"],
    "us-east-1e": ["subnet-869caabb", "subnet-02fcce011320639c2"]
}

preferred_az = "us-east-1c"
preferred_subnet = aws_az_to_subnets[preferred_az][0]

cluster_spec.set_network(vpc, preferred_az, preferred_subnet)
cluster_spec.validate()

#cluster_id = CloudProvider.create_cluster(cluster_spec)

cluster_id = "j-3AY581YLLQP2D"
print("Cluster ID: {}".format(cluster_id))

# We want to retrieve things like:
# Master public DNS to SSH into
# Spark History Server UI


clusters = CloudProvider.list_clusters("EMR", region)
print(clusters)

'''
id = "j-3AY581YLLQP2D"
name = 'test_cluster_1'
cluster = CloudProvider.get_cluster_info_by_id("EMR", region, id)
print("ID: {}".format(cluster))

print("Destroying cluster")
resp = CloudProvider.destroy_cluster("EMR", region, id)
print(resp)
'''
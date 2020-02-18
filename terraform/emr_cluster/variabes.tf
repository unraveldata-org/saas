variable "name" {
  default = "FreeTrialCluster"
}

variable "key_name" {
  default = "free-trial-cluster"
}

variable "region" {
  default = "us-east-1c"
}

# Required by us, VPC subnet
variable "subnet_id" {
  default =
}

// size = "${lookup(var.storage_sizes, var.plans["5USD"])}"
variable "subnet_id" {
  type = "map"
  default = {
    "us-east-1c" = "subnet-e54410cf"
  }
}

# Required, VPC ID
variable "vpc_id" {}

# Limit traffic to the outside for security reasons
variable "cidr_block" {
  default = "0.0.0.0/0"
}

# Tag
variable "project" {
  default = "Unravel Free Trial"
}

# Used in the name of serveral AWS resources as well as the Cluster Tag
variable "environment" {
  default = "test"
}

# Required, the release label for the Amazon EMR release
variable "release_label" {
  default = "emr-5.29.0"
}

# The applications installed on this cluster
variable "applications" {
  default = ["ZooKeeper", "Hadoop", "Hive", "Tez", "Pig", "Spark", "Hue", ]
  type    = list(string)
}

# List of configurations supplied for the EMR cluster, such as spark-env
variable "configurations" {
}

variable "instance_groups" {
  default = [
    {
      name           = "MasterInstanceGroup"
      instance_role  = "MASTER"
      instance_type  = "m3.xlarge"
      instance_count = 1
    },
    {
      name           = "CoreInstanceGroup"
      instance_role  = "CORE"
      instance_type  = "m3.xlarge"
      instance_count = "2"
    },
  ]

  type = list(string)
}

# List of bootstrap actions that will be run before Hadoop is started on the cluster nodes.
/*
variable "bootstrap_name" {
  default = "emr_bootstrap_script"
}
variable "bootstrap_uri" {
  default = "s3://unraveldatarepro/unravel_emr_bootstrap.py"
}
variable "bootstrap_args" {
  default = []
  type    = list(string)
}
*/

# The path to the Amazon S3 location where logs for this cluster are stored.
variable "log_uri" {}

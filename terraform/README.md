# WORK IN PROGRESS

# Create Cloud Resources using Terraform
Description about terraform

## Pre-requisites
* Amazon EMR: Needs AWS CLI. Make sure to run,
`aws configure`
Ensure you have the *topcat* key.

* Azure HDInsight: *Not supported at this time*
* Google Dataproc: *Not supported at this time*


## Setting up Terraform
1. **Install terraform:**
Scripts are currently using version v0.12.20.
Can either do `brew install terraform`, or download the CLI from https://www.terraform.io/downloads.htmland then add the dir to your PATH env variable.
1. **First time set-up**: cd to the emr_cluster directory (or other desired Cloud Provider) and execute `terraform init`

## Creating a Cluster
1. **Configure:**
Modify the template (variables.tf) with ingress_cidr_blocks to your own IP.

1. **Analyze**: Analyze the plan before creating the cluster, run `terraform plan`/
Note: The default viz is not very powerful, so can instead use this tool (https://github.com/28mm/blast-radius) to visualize the d3.js file

1. **Create**: Instantiate the cluster, execute `terraform apply`

##  Destroying the cluster
1. **Destroy**: Note that this will also kill the cluster and also all of the dependencies associated with it like security groups, IAM roles, and script on S3.
`terraform destroy`

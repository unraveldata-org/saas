# Cluster Lifecycle Manager
Manages the provisioning, monitoring, and deletion of resources like Nodes (VMs) and Hadoop clusters.
This infrastructure is shared by both the Unravel QE Pipeline and the Free Trial SaaS.

This contains a long-running daemon app that is stateless (so can be restarted at any time) and performs state transitions in the MySQL DB and interacts with the Cloud Providers (EMR, HDI, Dataproc, etc.)

## Requirements
* Python 3.8 with virtual environment.
* DB module installed
* Cloud Provider configuration. 
  * EMR must have AWS access credentials.
    * Install aws cli, e.g., `pip3 install awscli`
    * Login to https://console.aws.amazon.com/
    * Click on your username dropdown, then "Security Credentials"
    * Generate new key ID and secret, and store it securely
    * Run `aws configure` and enter those same details
     
  * HDI: TODO
## Usage
1. Start the daemon using one of 2 methods: ```python unravel_clm.py``` or ```pyton unravel_clm.py start```

# Unravel SaaS on the Cloud
This project includes the necessary libraries, daemons, and databases to manage the Unravel node and Hadoop clusters for any Cloud Provider (EMR, HDI, Dataproc, etc.).
This is consumed by 2 customers:
* Unravel Free Trial workflow:
* Unravel QE Pipeline: 

## Requirements
1. Python 3.8 with virtual environment
1. MySQL database

## First-time setup
1. See db/README.md for instructions on how to create the MySQL DB and add the settings to config.py
1. Create a Python virtual environment that includes the Python library dependencies from db/requirements.txt and webapp/requirements.txt

## Startup
1. Ensure the MySQL DB is running
1. Start the Flask webapp
1. Start the Cluster Lifecycle Manager daemon
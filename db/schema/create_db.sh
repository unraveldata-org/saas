#!/bin/sh

# TODO, add option to allow dropping the current DB if it exists
echo "Dropping existing database"
mysql -h localhost -u root -p -e 'drop database if exists `clm`;'

echo "Creating original schema"

mysql -h localhost -u root -p < 00_ddl_schema.sql

echo "Applying additional DDL and DML changes"

mysql -h localhost -u root -p < 00_dml_data.sql

echo "Done"
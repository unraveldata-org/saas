# Database Schema

### Install MySQL 
* MySQL 8.0.19: https://dev.mysql.com/doc/relnotes/mysql/8.0/en/news-8-0-19.html

### Linux
`service mysql start`

### Mac
`brew services restart mysql`

### Create Schema and any DDL/DML Changes
* `> ./create_db.sh`
* That script will also create the user. E.g.,
```
CREATE USER 'unravel'@'localhost' IDENTIFIED BY 'unraveldata';
GRANT ALL PRIVILEGES ON clm.* TO 'unravel'@'localhost';
FLUSH PRIVILEGES;
```
* Make sure to modify config.py with username and password

#!/bin/sh

DB="clm"
USER="unravel"
PASS="unraveldata"

DROP_DATABASE=0
# Loop through arguments and process them
for arg in "$@"
do
    case $arg in
        -d|--drop)
        DROP_DATABASE=1
        shift # Remove --initialize from processing
        ;;
        -h|--help)
        echo "Usage:\n
  -d|--drop : Drop existing database (defaults to False)
  -h|-help  : Help info"
        shift
        ;;
        *)
        shift
        ;;
    esac
done

echo "Drop existing database: $DROP_DATABASE"
if [[ "$DROP_DATABASE" == 1 ]]; then
    echo "Dropping existing database!!!"
    # Need to escape the backslash in order to escape the backtick.
    cmd="mysql -h localhost -u root -e 'drop database if exists $DB;' -p"
    echo $cmd
    eval "$cmd"
fi

echo "Creating original schema"

cmd="mysql -h localhost -u root -p -e \"CREATE USER IF NOT EXISTS '$USER'@'localhost' IDENTIFIED BY '$PASS';\""
echo $cmd
eval "$cmd"

cmd="mysql -h localhost -u root -p < 00_ddl_schema.sql"
echo $cmd
eval "$cmd"

cmd="mysql -h localhost -u root -p -e \"GRANT ALL PRIVILEGES ON $DB.* TO '$USER'@'localhost';\""
echo $cmd
eval "$cmd"

cmd="mysql -h localhost -u root -p -e \"FLUSH PRIVILEGES;\""
echo $cmd
eval "$cmd"

echo "Done"
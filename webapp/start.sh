#!/bin/sh
export FLASK_APP=app

# Make sure to call > source ../../bin/activate
echo "Starting web app"
flask run

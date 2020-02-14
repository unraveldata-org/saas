#!/bin/sh

# Make sure to call > source ../../../bin/activate
echo "Starting web app in production environment"

export FLASK_DEBUG=0
export FLASK_ENV=production

python run.py

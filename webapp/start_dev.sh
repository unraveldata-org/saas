#!/bin/sh

# Make sure to call > source ../../../bin/activate
echo "Starting web app in development environment"

export FLASK_DEBUG=1
export FLASK_ENV=development

python run.py

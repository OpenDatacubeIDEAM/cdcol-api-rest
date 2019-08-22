#!/bin/bash

# Install new rewuirements
/root/anaconda/bin/pip install -r requirements.txt
# Load env variables 
source environment
# Initialize datacube database and systems
datacube system init
# Create migrations
/root/anaconda/bin/python manage.py makemigrations --noinput --merge
# Migrate changes to the database
/root/anaconda/bin/python manage.py migrate --noinput
# Running the development server
/root/anaconda/bin/python manage.py runserver 0.0.0.0:8000
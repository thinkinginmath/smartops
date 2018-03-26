#!/bin/bash
python /smartops/bin/manage_db.py createdb
uwsgi --http 0.0.0.0:8000 --module smartops.app:app --processes 2 --threads 8

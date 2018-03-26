#!/bin/bash
docker build -t compassindocker/smartops-celery -f Dockerfile_CeleryWorker .
docker push compassindocker/smartops-celery

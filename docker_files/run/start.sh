#!/bin/bash
# 启动服务
set -e
python manage.py collectstatic --noinput
python manage.py makemigrations --noinput
python manage.py migrate

if [ "$ENABLE_CELERY_WORKER" == 'true' ]
then
  celery worker -A workflow.celery_app -l info --logfile='logs/celery_worker.log' &
fi

if [ "$ENABLE_CELERY_BEAT" == 'true' ]
then
  celery beat -A workflow.celery_app -l info --logfile='logs/celery_beat.log' --pidfile= &
fi

uwsgi --ini /data/server/run/uwsgi.ini


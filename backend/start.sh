#!/bin/bash

SERVER_TYPE=${SERVER_TYPE:-WS}
export PYTHONPATH=$PYTHONPATH:$(pwd)
export PYTHONUNBUFFERED=1

echo "======================"
echo "Server Type: $SERVER_TYPE"
echo "======================"

if [ "$SERVER_TYPE" = "HTTP" ]; then
    python manage.py migrate --noinput
    exec gunicorn backend.wsgi:application \
      --bind 0.0.0.0:8000 \
      --workers 3

elif [ "$SERVER_TYPE" = "WS" ]; then
    exec daphne -b 0.0.0.0 -p 8001 backend.asgi:application

elif [ "$SERVER_TYPE" = "CELERY" ]; then
    exec celery -A backend worker -l info --concurrency=1 --prefetch-multiplier=1

elif [ "$SERVER_TYPE" = "CELERY_BEAT" ]; then
    exec celery -A backend beat -l info

else
    echo "Unknown SERVER_TYPE"
    exit 1
fi

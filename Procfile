web: gunicorn locallibrary.wsgi --log-file -

worker: celery -A locallibrary worker
beat: celery -A locallibrary beat -S django
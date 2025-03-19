import os

# Only import Celery if the environment variable is set to "True"
if os.getenv('RUN_CELERY', 'False') == 'True':
    from .celery import app as celery_app  # noqa

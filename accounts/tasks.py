from celery import shared_task


@shared_task
def start_up():
    print('hello world!')
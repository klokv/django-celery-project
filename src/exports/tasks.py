from celery import shared_task
from . import utils as export_utils

@shared_task(name='export_rating_dataset')
def export_rating_dataset_task():
    export_utils.generate_rating_dataset(to_csv=True)

@shared_task(name='export_anime_dataset')
def export_anime_dataset_task():
    export_utils.generate_anime_dataset(to_csv=True)

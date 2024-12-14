import os
from celery import Celery
from celery.schedules import crontab


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'src.settings')

app = Celery('src')
app.config_from_object("django.conf:settings", namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    "run_anime_rating_avg_every_hour": {
        'task': 'task_update_anime_ratings',
        'schedule': 3600,
    },
    "task_update_anime_without_ratings": {
        'task': 'task_update_anime_without_ratings',
        'schedule': 30,
    },
    "daily_anime_idx_refresh": {
        "task": "anime.tasks.update_anime_position_embedding_idx",
        "schedule": crontab(hour=1, minute=0)
    },
    "daily_rating_dataset_export": {
        "task": "export_rating_dataset",
        "schedule": crontab(hour=1, minute=30)
    },
    "daily_rating_dataset_export": {
        "task": "export_anime_dataset",
        "schedule": crontab(hour=2, minute=15)
    },
    "daily_train_surprise_model": {
        "task": "ml.tasks.train_surprise_model_task",
        "schedule": crontab(hour=3, minute=0)
    },
    "daily_model_inference": {
        "task": "ml.tasks.batch_users_prediction_task",
        "schedule": crontab(hour=4, minute=30),
        "kwargs": {"max_pages": 5000, "offset": 200}
    },
}
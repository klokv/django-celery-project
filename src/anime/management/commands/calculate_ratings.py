from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ratings.tasks import task_update_anime_ratings

User = get_user_model()

class Command(BaseCommand):   
    def handle(self, *args, **options):
        task_update_anime_ratings
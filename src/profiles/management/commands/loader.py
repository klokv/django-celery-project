from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from src import utils as src_utils
from anime.models import Anime

User = get_user_model()

class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("count", nargs='?', default=10, type=int)
        parser.add_argument("--anime", action='store_true', default=False)
        parser.add_argument("--users", action='store_true', default=False)
        parser.add_argument("--show-total", action='store_true', default=False)
        
    def handle(self, *args,  **options):
        count = options.get('count')
        show_total = options.get('show_total')
        load_anime = options.get('anime')
        generate_users = options.get('users')

        if load_anime:
            anime_dataset= src_utils.load_anime_data(limit=count)
            anime_new = [Anime(**x) for x in anime_dataset]
            anime_bulk = Anime.objects.bulk_create(anime_new, ignore_conflicts=True)
            print(f"New anime: {len(anime_bulk)}")
            if show_total:
                print(f"Total anime: {Anime.objects.count()}")

        if generate_users:
            profiles = src_utils.get_fake_profiles(count=count)
            new_users = []
            
            for profile in profiles:
                new_users.append(
                    User(**profile)
                )

            user_bulk = User.objects.bulk_create(new_users, ignore_conflicts=True)
            print(f"New users: {len(user_bulk)}")
            if show_total:
                print(f"Total users: {User.objects.count()}")
import random
from celery import shared_task
from django.contrib.auth import get_user_model
from anime.models import Anime
from django.contrib.contenttypes.models import ContentType
from .models import Rating, RatingChoice
from django.db.models import Avg, Count
from django.utils import timezone
import decimal
import time
import datetime
from django.db.models import Exists, OuterRef

User = get_user_model()

@shared_task(name='generate_fake_reviews_task')
def generate_fake_reviews(count=100, users =10, null_avg=False):
    user_s = User.objects.first()
    user_e = User.objects.last()
    random_user_ids = random.sample(range(user_s.id, user_e.id), users)
    users = User.objects.filter(id__in=random_user_ids)
    anime = Anime.objects.all().order_by("?")[:count]
    if null_avg:
        anime = Anime.objects.filter(rating_avg__isnull=True).order_by("?")[:count]
    n_ratings = anime.count()
    rating_choices = [x for x in RatingChoice.values if x is not None]
    user_ratings = [random.choice(rating_choices) for _ in range(0, n_ratings)]

    new_ratings = []
    for anime_entry in anime:
        rating_obj = Rating.objects.create(
            content_object=anime_entry,
            value=user_ratings.pop(),
            user=random.choice(users)
        )
        new_ratings.append(rating_obj.id)
    return new_ratings

@shared_task(name='task_update_anime_ratings')
def task_update_anime_ratings(object_id=None):
    start_time = time.time()
    ctype = ContentType.objects.get_for_model(Anime)
    rating_qs = Rating.objects.filter(content_type=ctype)
    if object_id is not None:
        rating_qs = rating_qs.filter(object_id=object_id)       
    agg_ratings = rating_qs.values('object_id').annotate(average=Avg('value'), count=Count('object_id'))
    for agg_rate in agg_ratings:
        object_id = agg_rate['object_id']
        rating_avg = agg_rate['average']
        rating_count = agg_rate['count']
        score = decimal.Decimal(rating_avg * rating_count * 1.0)
        qs = Anime.objects.filter(id=object_id)
        qs.update(
            rating_avg=rating_avg or 0,
            rating_count=rating_count or 0,
            rating_last_updated=timezone.now(),
            score=score or 0
        )

    total_time = time.time() - start_time
    delta = datetime.timedelta(seconds=int(total_time))
    print(f"Rating update took {delta}({total_time}s)")
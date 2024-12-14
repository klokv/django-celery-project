from celery import shared_task

from django.apps import apps

from django.db.models import Window, F
from django.db.models.functions import DenseRank


@shared_task
def update_anime_position_embedding_idx():
    Anime = apps.get_model('anime', "Anime")
    qs = Anime.objects.all().annotate(
        new_idx=Window(
            expression=DenseRank(),
            order_by=[F('id').asc()]
        )
    ).annotate(final_idx = F('new_idx') - 1)
    updated = 0
    for obj in qs:
        if obj.final_idx != obj.idx:
            updated += 1
            obj.idx = obj.final_idx
            obj.save()
    print(f"Updated {updated} anime idx fields")

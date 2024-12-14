from django.db import models
from django.contrib.contenttypes.fields import GenericRelation
from ratings.models import Rating
from django.utils import timezone
from django.db.models import Q, F, Sum
from django.db.models import Q, F, Sum, Case, When
import datetime
from . import tasks as anime_tasks
from django.db.models.signals import post_save, post_delete

RATING_CALC_TIME_IN_DAYS = 1


class AnimeQuerySet(models.QuerySet):
    def popular(self, reverse=False):
        ordering = '-score'
        if reverse:
            ordering = 'score'
        return self.filter(rating_count__gte=1000).order_by(ordering)
    
    def popular_calc(self, reverse=False):
        ordering = '-score'
        if reverse:
            ordering = 'score'
        return self.annotate(score=Sum(
                F('rating_avg') * F('rating_count'),
                output_field=models.FloatField()
            )
        ).filter(rating_count__gte=1000).order_by(ordering)
    
    def needs_updating(self):
        now = timezone.now()
        days_ago = now - datetime.timedelta(RATING_CALC_TIME_IN_DAYS)
        return self.filter(
            Q(rating_last_updated__isnull=True)|
            Q(rating_last_updated__lte=days_ago)
        )

class AnimeManager(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return AnimeQuerySet(self.model, using=self._db)

    def by_id_order(self, anime_pks=[]):
        qs = self.get_queryset().filter(pk__in=anime_pks)
        maintain_order = Case(*[When(pk=pki, then=idx) for idx, pki in enumerate(anime_pks)])
        return qs.order_by(maintain_order)

    def needs_updating(self):
        return self.get_queryset().needs_updating()   

class Anime(models.Model):
    title = models.CharField(max_length=500, unique=True)
    overview = models.TextField()
    release_date = models.CharField(max_length=20, blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ratings = GenericRelation(Rating)
    rating_last_updated = models.DateTimeField(auto_now=False, auto_now_add=False, blank=True, null=True)
    rating_count = models.IntegerField( blank=True, null=True)
    rating_avg = models.DecimalField(decimal_places=2, max_digits=5, blank=True, null=True)
    score = models.FloatField(blank=True, null=True)
    idx = models.IntegerField(help_text='Position IDs for ML', blank=True, null=True)

    objects = AnimeManager()

    def get_absolute_url(self):
        return f"/anime/{self.id}/"

    def __str__(self):
        if not self.release_date:
            return f"{self.title}"
        return f"{self.title} ({self.release_date})"

    # def rating_avg_display(self):
    #     now = timezone.now()
    #     if not self.rating_last_updated:
    #         return self.calculate_rating()
    #     if self.rating_last_updated > now - datetime.timedelta(minutes=RATING_CALC_TIME_IN_DAYS):
    #         return self.rating_avg
    #     return self.calculate_rating()

    # def calculate_ratings_count(self):
    #     return self.ratings.all().count()
    
    # def calculate_ratings_avg(self):
    #     return self.ratings.avg()
    
    # def calculate_rating(self, save=True):
    #     rating_avg = self.calculate_ratings_avg()
    #     rating_count = self.calculate_ratings_count()
    #     self.rating_count = rating_count
    #     self.rating_avg = rating_avg
    #     self.rating_last_updated = timezone.now()
    #     if save:
    #         self.save()
    #     return self.rating_avg
    

def anime_post_save(sender, instance, created, *args, **kwargs):
    if created and instance.id:
        anime_tasks.update_anime_position_embedding_idx()

post_save.connect(anime_post_save, sender=Anime)

def anime_post_delete(*args, **kwargs):
    anime_tasks.update_anime_position_embedding_idx()

post_delete.connect(anime_post_delete, sender=Anime)
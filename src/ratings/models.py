from django.db import models
from django.conf import settings
from django.db.models.signals import post_save
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db.models import Avg
from django.utils import timezone
from django.apps import apps


# Create your models here.
User = settings.AUTH_USER_MODEL 

class RatingChoice(models.IntegerChoices):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    __empty__ = 'Rate this'

class RatingQuerySet(models.QuerySet):
    def avg(self):
        return self.aggregate(average=Avg('value'))['average']

    def anime(self):
        Anime = apps.get_model('anime', 'Anime')
        ctype = ContentType.objects.get_for_model(Anime)
        return self.filter(active=True, content_type=ctype)

    def as_object_dict(self, object_ids=[]):
        qs = self.filter(object_id__in=object_ids)
        return {f"{x.object_id}": x.value for x in qs}

class RatingManager(models.Manager):
    def get_queryset(self):
        return RatingQuerySet(self.model, using=self.db)

    def anime(self):
        return self.get_queryset().anime()

    def avg(self):
        return self.get_queryset().avg()

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.IntegerField(null=True, blank=True, choices=RatingChoice.choices)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    active = models.BooleanField(default=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    active_update_timestamp = models.DateTimeField(auto_now_add=False, auto_now=False, null=True, blank=True)

    objects = RatingManager()

    class Meta:
        ordering = ['-timestamp']


def rating_post_save(sender, instance, created, *args, **kwargs):
    if created:
        Suggestion = apps.get_model('suggestions', 'Suggestion')
        _id = instance.id 
        if instance.active:
            qs = Rating.objects.filter(
                content_type=instance.content_type,
                object_id=instance.object_id,
                user=instance.user
            ).exclude(id=_id, active=True)
            if qs.exists():
                qs = qs.exclude(active_update_timestamp__isnull=False)
                qs.update(active=False, active_update_timestamp=timezone.now())
            suggestion_qs = Suggestion.objects.filter(
                content_type=instance.content_type,
                object_id=instance.object_id,
                user=instance.user,
                did_rate=False,
            )
            if suggestion_qs.exists():
                suggestion_qs.update(
                    did_rate=True,
                    did_rate_timestamp=timezone.now(),
                    rating_value=instance.value,
                )
post_save.connect(rating_post_save, sender=Rating)
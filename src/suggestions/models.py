from django.db import models
import datetime
from django.db.models import F
from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone

# Create your models here.
User = settings.AUTH_USER_MODEL 

class SuggestionManager(models.Manager):
    def get_recently_suggested(self, anime_ids=[], user_ids=[], days_ago=7):
        data = {}
        delta = datetime.timedelta(days=days_ago)
        time_delta = timezone.now() - delta
        ctype = ContentType.objects.get(app_label='anime', model='anime')
        filter_args = {
            "content_type": ctype,
            "object_id__in": anime_ids,
            "user_id__in": user_ids,
            "active": True,
            "timestamp__gte": time_delta
        }
        dataset = self.get_queryset().filter(**filter_args)
        dataset = dataset.annotate(animeId=F('object_id'), userId=F('user_id')).values("animeId", "userId")
        for d in dataset:
            # print(d) # [{'animeId': abac, 'userId': ad}]
            anime_id = str(d.get("animeId"))
            user_id = d.get('userId')
            if anime_id in data:
                data[anime_id].append(user_id)
            else:
                data[anime_id] = [user_id]
        return data

class Suggestion(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    value = models.FloatField(null=True, blank=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveBigIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")
    timestamp = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)
    # Suggested anime get rated.
    rating_value = models.FloatField(null=True, blank=True)
    did_rate = models.BooleanField(default=False)
    did_rate_timestamp = models.DateTimeField(auto_now_add=False, auto_now=False, blank=True, null=True)
    
    objects = SuggestionManager()

    class Meta:
        ordering = ['-timestamp']


from django.contrib import admin

# Register your models here.
from.models import Anime

class AnimeAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'idx', 'rating_avg', 'rating_count']
    readonly_fields = ['idx', 'rating_avg', 'rating_count']
    search_fields = ['id']

admin.site.register(Anime, AnimeAdmin)
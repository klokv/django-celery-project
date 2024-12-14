from django.db.models import F
from django.contrib.contenttypes.models import ContentType
import csv
import tempfile
from django.core.files.base import File
from anime.models import Anime
from ratings.models import Rating
from .models import Export, ExportDataType


def export_dataset(dataset, fname='dataset.csv', type=ExportDataType.RATINGS):
    if not dataset:
        return
    with tempfile.NamedTemporaryFile(mode='r+') as temp_f:
        dict_writer = None
        for record in dataset:
            if dict_writer is None:
                keys = record.keys()
                dict_writer = csv.DictWriter(temp_f, keys)
                dict_writer.writeheader()
            dict_writer.writerow(record)
        temp_f.seek(0)
        obj = Export.objects.create(type=type)
        obj.file.save(fname, File(temp_f))


def generate_rating_dataset(app_label='anime', model='anime', to_csv=True):
    ctype = ContentType.objects.get(app_label=app_label, model=model)
    qs = Rating.objects.filter(active=True, content_type=ctype)
    qs = qs.annotate(userId=F('user_id'), animeId=F("object_id"), rating=F("value"))

    if to_csv:
        with tempfile.NamedTemporaryFile(mode='r+') as temp_f:
            dict_writer = None
            for record in qs.iterator():
                record_dict = {
                    'userId': record.userId,
                    'animeId': record.animeId,
                    'rating': record.rating,
                }
                if dict_writer is None:
                    keys = record_dict.keys()
                    dict_writer = csv.DictWriter(temp_f, keys)
                    dict_writer.writeheader()
                dict_writer.writerow(record_dict)
            temp_f.seek(0)
            obj = Export.objects.create(type=ExportDataType.RATINGS)
            obj.file.save('rating.csv', File(temp_f))
            

def generate_anime_dataset(to_csv=True):
    qs = Anime.objects.all()
    qs = qs.annotate(animeId=F('id'), animeIdx=F("idx"))
    dataset = qs.values('animeIdx', 'animeId', 'title', 'release_date', 'rating_count', 'rating_avg')
    if to_csv:
        export_dataset(dataset=dataset, fname='anime.csv', type=ExportDataType.ANIME)
    return dataset
import csv
from pprint import pprint
from django.conf import settings
from faker import Faker

ANIME_METADATA_CSV = settings.DATA_DIR / "anime-dataset-2023.csv"

def load_anime_data(limit=1):
    with open(ANIME_METADATA_CSV, newline='', encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        dataset = []
        for i, row in enumerate(reader):
            _id = row.get("anime_id")
            try:
                _id = int(_id)
            except:
                _id = None

            data = {
                "id": _id,
                "title": row.get('Name'),
                "overview": row.get('Synopsis'),
                "release_date": row.get('Premiered')
            }
            dataset.append(data)
            if i + 1 > limit:
                break
        return dataset

def get_fake_profiles(count=10):
    fake = Faker()
    user_data = []
    for i in range(count):
        profile = fake.profile()
        data = {
            "username": profile.get('username'),
            "email": profile.get('mail'),
            "is_active": True
        }
        if 'name' in profile:
            fname, lname = profile.get('name').split()[:2]
            data['first_name'] = fname
            data['last_name'] = lname
        user_data.append(data)
    return user_data
# Generated by Django 5.1.3 on 2024-11-24 00:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('anime', '0002_alter_anime_release_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='anime',
            name='rating_avg',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        migrations.AddField(
            model_name='anime',
            name='rating_count',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='anime',
            name='rating_last_updated',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]

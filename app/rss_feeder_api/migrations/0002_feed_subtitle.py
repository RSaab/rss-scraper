# Generated by Django 3.1 on 2020-08-13 10:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rss_feeder_api', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='subtitle',
            field=models.CharField(max_length=200, null=True),
        ),
    ]
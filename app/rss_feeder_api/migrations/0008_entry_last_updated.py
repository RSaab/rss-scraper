# Generated by Django 3.1 on 2020-08-20 10:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rss_feeder_api', '0007_auto_20200818_1830'),
    ]

    operations = [
        migrations.AddField(
            model_name='entry',
            name='last_updated',
            field=models.DateTimeField(auto_now=True),
        ),
    ]

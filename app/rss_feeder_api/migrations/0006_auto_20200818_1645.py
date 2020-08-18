# Generated by Django 3.1 on 2020-08-18 16:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rss_feeder_api', '0005_auto_20200814_1349'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='entry',
            name='expires',
        ),
        migrations.RemoveField(
            model_name='feed',
            name='lastbuilddate',
        ),
        migrations.AddField(
            model_name='feed',
            name='flagged',
            field=models.BooleanField(default=False),
        ),
    ]
# Generated by Django 3.1 on 2020-08-13 16:23

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('rss_feeder_api', '0002_feed_subtitle'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='entry',
            options={'ordering': ('-updated_at',), 'verbose_name_plural': 'entries'},
        ),
        migrations.AlterModelOptions(
            name='feed',
            options={'ordering': ('-updated_at',), 'verbose_name': 'Feed', 'verbose_name_plural': 'Feeds'},
        ),
        migrations.AddField(
            model_name='entry',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='entry',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterUniqueTogether(
            name='entry',
            unique_together={('guid',)},
        ),
    ]

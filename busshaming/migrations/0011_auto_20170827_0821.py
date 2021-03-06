# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-27 08:21
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('busshaming', '0010_auto_20170820_1322'),
    ]

    operations = [
        migrations.CreateModel(
            name='FeedTimetable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('timetable_url', models.URLField()),
                ('fetch_last_modified', models.CharField(blank=True, max_length=50, null=True)),
                ('feed', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busshaming.Feed')),
            ],
        ),
        migrations.AlterUniqueTogether(
            name='feedtimetable',
            unique_together=set([('feed', 'timetable_url')]),
        ),
    ]

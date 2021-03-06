# -*- coding: utf-8 -*-
# Generated by Django 1.11.4 on 2017-08-11 04:57
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Agency',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Feed',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('timezone', models.CharField(max_length=200)),
                ('realtime_feed_url', models.URLField()),
                ('active', models.BooleanField()),
            ],
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gtfs_route_id', models.CharField(max_length=200)),
                ('route_short_name', models.CharField(max_length=200)),
                ('route_long_name', models.CharField(max_length=200)),
                ('route_desc', models.CharField(blank=True, max_length=500, null=True)),
                ('route_url', models.CharField(blank=True, max_length=200, null=True)),
                ('route_color', models.CharField(blank=True, max_length=7, null=True)),
                ('route_text_color', models.CharField(blank=True, max_length=7, null=True)),
                ('agency_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busshaming.Agency')),
                ('feed_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busshaming.Feed')),
            ],
        ),
        migrations.CreateModel(
            name='Stop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gtfs_stop_id', models.CharField(max_length=200)),
                ('name', models.CharField(max_length=200)),
            ],
        ),
        migrations.CreateModel(
            name='Trip',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('gtfs_trip_id', models.CharField(max_length=200)),
                ('version', models.IntegerField()),
                ('active', models.BooleanField()),
                ('trip_headsign', models.CharField(max_length=200)),
                ('trip_short_name', models.CharField(max_length=200)),
                ('direction', models.SmallIntegerField()),
                ('wheelchair_accessible', models.BooleanField()),
                ('bikes_allowed', models.BooleanField()),
                ('notes', models.TextField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('route_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busshaming.Route')),
            ],
        ),
        migrations.CreateModel(
            name='TripStop',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sequence', models.IntegerField()),
                ('arrival_time', models.CharField(max_length=5)),
                ('departure_time', models.CharField(max_length=5)),
                ('timepoint', models.BooleanField()),
                ('stop_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busshaming.Stop')),
                ('trip_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busshaming.Trip')),
            ],
        ),
        migrations.CreateModel(
            name='TripTimetable',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('monday', models.BooleanField()),
                ('tuesday', models.BooleanField()),
                ('wednesday', models.BooleanField()),
                ('thursday', models.BooleanField()),
                ('friday', models.BooleanField()),
                ('saturday', models.BooleanField()),
                ('sunday', models.BooleanField()),
                ('trip_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busshaming.Trip')),
            ],
        ),
        migrations.AddField(
            model_name='agency',
            name='feed_id',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='busshaming.Feed'),
        ),
    ]

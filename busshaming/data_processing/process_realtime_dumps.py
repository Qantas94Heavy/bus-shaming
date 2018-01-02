import os
from datetime import datetime, timedelta, timezone
import tempfile

import boto3
import pytz
from google.transit import gtfs_realtime_pb2

from busshaming.models import Feed, Trip, TripDate, TripStop, RealtimeEntry, Route, Stop

S3_BUCKET_NAME = os.environ.get('S3_BUCKET_NAME', 'busshaming-realtime-dumps')


def add_missing_tripdate(feed, realtime_trip):
    gtfs_trip_id = realtime_trip.trip_id
    start_date = realtime_trip.start_date
    print(f'Adding missing trip date for gtfs id {gtfs_trip_id} on date {start_date}')
    date = datetime.strptime(start_date, '%Y%m%d').date()
    try:
        trip = Trip.objects.get(gtfs_trip_id=gtfs_trip_id)
        print(f'Found trip: {trip}')
        if TripDate.objects.filter(trip=trip, date=date).count() == 0:
            tripdate = TripDate(trip=trip, date=date, added_from_realtime=True)
            tripdate.save()
            return tripdate
        return TripDate.objects.get(trip=trip, date=date)
    except Trip.DoesNotExist as e:
        print(f'Trip with gtfs id {gtfs_trip_id} does not exist!!')
        try:
            route = Route.objects.get(feed=feed, gtfs_route_id=realtime_trip.route_id)
            newtrip = Trip(
                gtfs_trip_id=gtfs_trip_id,
                active=True,
                direction=0,
                route=route,
                added_from_realtime=True,
                wheelchair_accessible=False,
                bikes_allowed=False,
            )
            newtrip.save()
            print(f'Added new trip: {newtrip}')
            tripdate = TripDate(trip=newtrip, date=date, added_from_realtime=True)
            tripdate.save()
            return tripdate
        except Route.DoesNotExist as e2:
            print('Route did not exist')
            print()
            return None


def add_missing_trip_stop(trip, trip_update, stop_update, feed_tz):
    stop_id = stop_update.stop_id
    stop = get_stop(trip.route.feed, stop_id)

    if TripStop.objects.filter(trip=trip, stop=stop, sequence=stop_update.stop_sequence).count() != 0:
        return
    arrival_time = datetime.fromtimestamp(stop_update.arrival.time, feed_tz)
    arrival_time -= timedelta(seconds=stop_update.arrival.delay)
    departure_time = datetime.fromtimestamp(stop_update.departure.time, feed_tz)
    departure_time -= timedelta(seconds=stop_update.departure.delay)
    newtripstop = TripStop(
        trip=trip,
        stop=stop,
        sequence=stop_update.stop_sequence,
        arrival_time=arrival_time.strftime('%H:%M:%S'),
        departure_time=departure_time.strftime('%H:%M:%S'),
        timepoint=False
    )
    newtripstop.save()


def get_stop(feed, stop_id):
    try:
        stop = Stop.objects.get(feed=feed, gtfs_stop_id=stop_id)
    except Stop.DoesNotExist:
        stop = Stop(feed=feed, gtfs_stop_id=stop_id, name='Unknown', position=None)
        stop.save()
    return stop


def process_trip_update(feed, trip_dates, stops, feed_tz, trip_update, threshold):
    trip = trip_update.trip
    key = (trip.trip_id, trip.start_date)
    if key not in trip_dates:
        trip_date = add_missing_tripdate(feed, trip)
        if trip_date is not None:
            print("COULDN'T FIND IN SCHEDULE: {}".format(key))
            print(trip)
    else:
        trip_date = trip_dates[key]
    if trip_date is None:
        return
    print(f'Upserting realtime entries for tripdate {trip_date.id}')
    for stop_update in trip_update.stop_time_update:
        if trip_date.trip.added_from_realtime:
            add_missing_trip_stop(trip_date.trip, trip_update, stop_update, feed_tz)
        if stop_update.arrival.time < threshold:
            if stop_update.stop_id in stops:
                stop = stops[stop_update.stop_id]
            else:
                stop = get_stop(feed, stop_update.stop_id)
            arrival_time = datetime.fromtimestamp(stop_update.arrival.time, feed_tz)
            departure_time = datetime.fromtimestamp(stop_update.departure.time, feed_tz)
            # Upsert RealtimeEntry
            RealtimeEntry.objects.upsert(trip_date.id, stop.id, stop_update.stop_sequence, arrival_time, stop_update.arrival.delay, departure_time, stop_update.departure.delay)


def process_dump_contents(feed, contents, trip_dates, stops, feed_tz):
    feed_message = gtfs_realtime_pb2.FeedMessage()
    feed_message.ParseFromString(contents)
    now = datetime.now(tz=feed_tz)
    threshold = int((now + timedelta(minutes=3)).timestamp())
    for entity in feed_message.entity:
        if entity.HasField('trip_update'):
            process_trip_update(feed, trip_dates, stops, feed_tz, entity.trip_update, threshold)


def fetch_next_dumps(feed, num_dumps):
    print(f'Processing next {num_dumps} realtime dumps')
    client = boto3.client('s3')
    file_prefix = f'{feed.slug}/'
    last_processed_file = feed.last_processed_dump

    if last_processed_file is not None:
        response = client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=file_prefix, StartAfter=last_processed_file)
    else:
        response = client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=file_prefix)

    results = []

    if response['KeyCount'] != 0:
        print(f'{response["KeyCount"]} new realtime dump(s) for {feed}')
        for i in range(num_dumps):
            key = response['Contents'][i]['Key']
            s3 = boto3.resource('s3')
            tmp, tmp_path = tempfile.mkstemp()
            print(f'Fetching {key}...')
            s3.Object(S3_BUCKET_NAME, key).download_file(tmp_path)
            results.append((key, tmp_path))
    else:
        print(f'No new realtime dump data for {feed}')
    return results


def process_next(num_dumps):
    num_dumps = 1
    feed = Feed.objects.get(slug='nsw-buses')
    cached_dumps = fetch_next_dumps(feed, num_dumps)
    feed_tz = pytz.timezone(feed.timezone)

    if len(cached_dumps) != 0:
        stops = {}
        for stop in Stop.objects.filter(feed=feed):
            stops[stop.gtfs_stop_id] = stop

        for key, tmp_file in cached_dumps:
            trip_dates = {}
            datestr = os.path.split(key)[1].rstrip('.pb')
            fetchtime = datetime.strptime(datestr, '%Y-%m-%dT%H:%M:%S.%f').replace(tzinfo=timezone.utc)
            # Assume no bus runs longer than 48h
            fetchtime = fetchtime.astimezone(feed_tz)
            start = (fetchtime - timedelta(days=2)).date()
            end = (fetchtime + timedelta(days=2)).date()
            for trip_date in TripDate.objects.filter(date__gte=start, date__lte=end).prefetch_related('trip'):
                datestr = trip_date.date.strftime('%Y%m%d')
                trip_dates[(trip_date.trip.gtfs_trip_id, datestr)] = trip_date
            with open(tmp_file, 'rb') as f:
                contents = f.read()
                process_dump_contents(feed, contents, trip_dates, stops, feed_tz)

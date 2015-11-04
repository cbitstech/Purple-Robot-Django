import datetime
import json
import os
import pytz

from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotReading, PurpleRobotPayload
from purple_robot_app.performance import append_performance_sample

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/extract_readings.lock', os.R_OK):
            t = os.path.getmtime('/tmp/extract_readings.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 4 * 60 * 60:
                print('extract_readings: Stale lock - removing...')
                os.remove('/tmp/extract_readings.lock')
            else:
                return

        touch('/tmp/extract_readings.lock')

        tag = 'extracted_readings'
        
        start = timezone.now()
        payloads = list(PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains='ingest_error')[:500])
        end = timezone.now()
        
        query_time = (end - start).total_seconds()

        while len(payloads) > 0:
            touch('/tmp/extract_readings.lock')
            
            start = timezone.now()
            
            for payload in payloads:
                payload.ingest_readings()
            
            end = timezone.now()
            
            perf_values = {}
            perf_values['num_extracted'] = len(payloads)
            perf_values['query_time'] = query_time
            perf_values['extraction_time'] = (end - start).total_seconds()
            
            append_performance_sample('system', 'reading_ingestion_performance', end, perf_values)

            start = timezone.now()
            payloads = list(PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains='ingest_error')[:500])
            end = timezone.now()
            query_time = (end - start).total_seconds()

        readings = PurpleRobotReading.objects.filter(guid=None)[:250]
        
        for reading in readings:
            reading.update_guid()
            
            readings = PurpleRobotReading.objects.filter(guid=None)[:250]

        os.remove('/tmp/extract_readings.lock')

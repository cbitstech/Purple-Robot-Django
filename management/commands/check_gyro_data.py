import datetime
import gzip
import json
import numpy
import pytz
import sys
import tempfile

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from ...models import PurpleRobotReading, PurpleRobotReport

PROBE_NAME = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.GyroscopeProbe'

class Command(BaseCommand):
    def handle(self, *args, **options):
        user_ids = {
#            'nexus5x': '7b9c92ca6cec1800e6df963869a07283',
            'nexus5': '073adb668d74a6aaa7d452eb9f804c99',
            'galaxy-nexus': 'e07af41838040c986a13ae48d4b432f1',
            'livewell_s6': '2b68e946429228ddb3c8a199d1120f10',
#            'galaxy-s4': '9e10a8a91a1fbcef9a4426f9c27b4cb5',
#            'galaxia': 'd1d0518f47d0c65397526c041635770f',
        }
            
        tzinfo = timezone.now().tzinfo
        
#        start = datetime.datetime(2016, 8, 15, 5, 10, 0, 0, tzinfo)
#        end = datetime.datetime(2016, 8, 15, 15, 0, 0, 0, tzinfo)

#        start = datetime.datetime(2016, 8, 18, 15, 10, 0, 0, tzinfo)
#        end = datetime.datetime(2016, 8, 19, 0, 0, 0, 0, tzinfo)

#        start = datetime.datetime(2016, 8, 19, 21, 45, 0, 0, tzinfo)
#        end = datetime.datetime(2016, 8, 21, 18, 0, 0, 0, tzinfo)

        end = timezone.now()
        start = end - datetime.timedelta(hours=24)        

        for name, user_id in user_ids.iteritems():
            intra_sensor_gaps = []
            payload_ranges = []
        
            readings = PurpleRobotReading.objects.filter(user_id=user_id, probe=PROBE_NAME, logged__gte=start, logged__lt=end).order_by('logged')
        
            count = readings.count()
        
            print(name + ' GYRO COUNT: ' + str(count) + ' -- ' + str(timezone.now()))

            index = 0
            
            while index < count:
                for reading in readings[index:(index + 500)]:
                    if index % 100 == 0:
                        print('Progress: ' + str(index) + ' / ' + str(count))
                
                    index += 1
            
                    payload = json.loads(reading.payload)
            
                    timestamps = payload['SENSOR_TIMESTAMP']
            
                    payload_ranges.append((timestamps[0], timestamps[-1] - timestamps[0],))
            
                    for i in range(1, len(timestamps)):
                        if timestamps[i - 1] > timestamps[i]:
                            print('Out of order: ' + str(i) + ' / ' + str(len(timestamps)) + ' -- ' + str(reading.pk) + ' -- ' + str(timestamps[i - 1]))
                            
                            if 'ACTIVE_BUFFER_COUNT' in payload:
                                print('ACTIVE BUFFERS: ' + str(payload['ACTIVE_BUFFER_COUNT']))
                            else:
                                print('NO ACTIVE BUFFER')
                        else:
                            intra_sensor_gaps.append(timestamps[i] - timestamps[i - 1])

            if count > 0:
                intra_mean = numpy.mean(intra_sensor_gaps) / 1000000
                intra_stdev = numpy.std(intra_sensor_gaps) / 1000000
                intra_min = numpy.min(intra_sensor_gaps) / 1000000
                intra_max = numpy.max(intra_sensor_gaps) / 1000000
        
                print('READINGS -- MEAN: ' + str(intra_mean) + ' -- STDEV: ' + str(intra_stdev) + ' -- MIN: ' + str(intra_min) + ' --- MAX: ' + str(intra_max))
        
                payload_ranges.sort(key=lambda item: item[0])
        
                payload_sizes = []
        
                for pr in payload_ranges:
                    payload_sizes.append(pr[1])
            
                pr_mean = numpy.mean(payload_sizes) / 1000000
                pr_stdev = numpy.std(payload_sizes) / 1000000
                pr_min = numpy.min(payload_sizes) / 1000000
                pr_max = numpy.max(payload_sizes) / 1000000
        
                print('PAYLOADS -- MEAN: ' + str(pr_mean) + ' -- STDEV: ' + str(pr_stdev) + ' -- MIN: ' + str(pr_min) + ' --- MAX: ' + str(pr_max))

                diffs = []
                
                for i in range(1, len(payload_ranges)):
                    diffs.append(payload_ranges[i][0] - (payload_ranges[i - 1][0] + payload_ranges[i - 1][1]))

                diff_mean = numpy.mean(diffs) / 1000000
                diff_stdev = numpy.std(diffs) / 1000000
                diff_min = numpy.min(diffs) / 1000000
                diff_max = numpy.max(diffs) / 1000000

                print('DIFFS    -- MEAN: ' + str(diff_mean) + ' -- STDEV: ' + str(diff_stdev) + ' -- MIN: ' + str(diff_min) + ' --- MAX: ' + str(diff_max))
            else: 
                print('WAITING FOR DATA')

        

from datetime import datetime
import json
import pytz
import tempfile
import urllib
import urllib2

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from purple_robot_app.models import *

PROBE_NAME = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.GyroscopeProbe'

class Command(BaseCommand):
    def handle(self, *args, **options):
        hashes = PurpleRobotPayload.objects.order_by().values('user_id').distinct()
        
        for hash in hashes:
            hash = hash['user_id']

            payloads = PurpleRobotReading.objects.filter(user_id=hash, probe=PROBE_NAME).order_by('logged')
            
            count = payloads.count()
            if count > 0:
                temp_file = tempfile.TemporaryFile()
                
                temp_file.write('User ID\tTimestamp\tX\tY\tZ\n')
                
                index = 0
                
                while index < count:
                    end = index + 100
                    
                    if end > count:
                        end = count
                
                    for payload in payloads[index:end]:
                        reading_json = json.loads(payload.payload)
                        
                        ts = []
                        xs = []
                        ys = []
                        zs = []
                        
                        for t in reading_json['EVENT_TIMESTAMP']:
                            ts.append(t)
    
                        for x in reading_json['X']:
                            xs.append(x)
    
                        for y in reading_json['Y']:
                            ys.append(y)
    
                        for z in reading_json['Z']:
                            zs.append(z)
                    
                        for i in range(0, len(ts)):
                            x = xs[i]
                            y = ys[i]
                            z = zs[i]
                            t = ts[i]
                            
                            temp_file.write(hash + '\t' + str(t) + '\t' + str(x) + '\t' + str(y) + '\t' + str(z) + '\n')
                            
                    index += 100
                
                temp_file.seek(0)
                        
                report = PurpleRobotReport(generated=timezone.now(), mime_type='text/plain', probe=PROBE_NAME, user_id=hash)
                report.save()
                report.report_file.save(hash + '-gyroscope.txt', File(temp_file))
                report.save()
                
                print('Wrote ' + hash + '-gyroscope.txt')

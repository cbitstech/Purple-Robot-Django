from datetime import datetime
import gzip
import json
import pytz
import tempfile
import urllib
import urllib2

from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.utils.text import slugify
from purple_robot_app.models import *

class Command(BaseCommand):
    def handle(self, *args, **options):
        hashes = PurpleRobotPayload.objects.order_by().values('user_id').distinct()
        
        labels = PurpleRobotReading.objects.exclude(probe__startswith='edu.northwestern').values('probe').distinct()
        
        for hash in hashes:
            hash = hash['user_id']
            
            for label in labels:
                slug_label = slugify(label['probe'])
                
                payloads = PurpleRobotReading.objects.filter(user_id=hash, probe=label['probe']).order_by('logged')
            
                count = payloads.count()

                if count > 0:
                    temp_file = tempfile.TemporaryFile()
                    gzf = gzip.GzipFile(mode='wb', fileobj=temp_file)

                    gzf.write('User ID\tTimestamp\tValue\n')
                
                    index = 0
                
                    while index < count:
                        end = index + 100
                    
                        if end > count:
                            end = count
                
                        for payload in payloads[index:end]:
                            reading_json = json.loads(payload.payload)

                            gzf.write(hash + '\t' + str(reading_json['TIMESTAMP']) + '\t' + reading_json['FEATURE_VALUE'] + '\n')
                            
                        index += 100
                
                    gzf.flush()
                    gzf.close()
                
                    temp_file.seek(0)
                        
                    report = PurpleRobotReport(generated=timezone.now(), mime_type='application/x-gzip', probe=slug_label, user_id=hash)
                    report.save()
                    report.report_file.save(hash + '-' + slug_label + '.txt.gz', File(temp_file))
                    report.save()
                
                    print('Wrote ' + hash + '-' + slug_label + '.txt')

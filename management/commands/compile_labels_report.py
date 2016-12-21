import datetime
import gzip
import json
import pytz
import tempfile

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from purple_robot_app.models import PurpleRobotReading, PurpleRobotReport

from purple_robot.settings import REPORT_DEVICES

class Command(BaseCommand):
    def handle(self, *args, **options):
        hashes = REPORT_DEVICES # PurpleRobotPayload.objects.order_by().values('user_id').distinct()

#        start = datetime.datetime.now() - datetime.timedelta(days=120)
        start_ts = datetime.datetime(2015, 11, 10, 0, 0, 0, 0, tzinfo=pytz.timezone('US/Central'))
        end_ts = start_ts + datetime.timedelta(days=1)
        
        labels = PurpleRobotReading.objects.exclude(probe__startswith='edu.northwestern').values('probe').distinct()
        
        for user_hash in hashes:
            for label in labels:
                slug_label = slugify(label['probe'])
                
                payloads = PurpleRobotReading.objects.filter(user_id=user_hash, probe=label['probe'], logged__gte=start_ts, logged__lt=end_ts).order_by('logged')
                
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

                            gzf.write(user_hash + '\t' + str(reading_json['TIMESTAMP']) + '\t' + reading_json['FEATURE_VALUE'] + '\n')
                            
                        index += 100
                
                    gzf.flush()
                    gzf.close()
                
                    temp_file.seek(0)
                        
                    report = PurpleRobotReport(generated=timezone.now(), mime_type='application/x-gzip', probe=slug_label, user_id=hash)
                    report.save()
                    report.report_file.save(user_hash + '-' + slug_label + '.txt.gz', File(temp_file))
                    report.save()

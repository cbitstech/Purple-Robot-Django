import datetime
import gzip
import json
import pytz
import sys
import tempfile

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotReading, PurpleRobotReport
from purple_robot.settings import REPORT_DEVICES

PROBE_NAME = 'edu.northwestern.cbits.purple_robot_manager.probes.studies.fallnet.FallNetProbe'

class Command(BaseCommand):
    def handle(self, *args, **options):
        hashes = REPORT_DEVICES # PurpleRobotPayload.objects.order_by().values('user_id').distinct()
        
        start_ts = timezone.now() - datetime.timedelta(days=120)
#        start_ts = datetime.datetime(2015, 7, 3, 5, 0, 0, 0, tzinfo=pytz.timezone('US/Central'))
        end_ts = timezone.now() # start_ts + datetime.timedelta(hours=1)

#        print('HASHES: ' + str(hashes))

        for user_hash in hashes:
            # hash = hash['user_id']

            payloads = PurpleRobotReading.objects.filter(user_id=user_hash, probe=PROBE_NAME, logged__gte=start_ts, logged__lt=end_ts).order_by('logged')
            
            count = payloads.count()
            
#            print(user_hash + ' -- ' + str(count))
            
            if count > 0:
                temp_file = tempfile.TemporaryFile()

                gzf = gzip.GzipFile(mode='wb', fileobj=temp_file)
                gzf.write('User ID\tTimestamp\tACCELEROMETER_READING_COUNT\tGYROSCOPE_READING_COUNT\tBAROMETER_READING_COUNT\tIS_FALL\tNOT_FALL_ODDS\tNOT_FALL_SUM\tNOT_FALL_PROBABILITY\tEVALUATION_WINDOW_START\tEVALUATION_WINDOW_END\tEVALUATION_WINDOW_SIZE\n')
                
                index = 0
                
                while index < count:
                    end = index + 100
                    
                    if end > count:
                        end = count
                
                    for payload in payloads[index:end]:
                        reading_json = json.loads(payload.payload)
                        
                        is_fall = 0 
                        
                        if reading_json['IS_FALL']:
                            is_fall = 1
                        
                        accel_count = ''
                        
                        if 'ACCELEROMETER_READING_COUNT' in reading_json:
                            accel_count = str(reading_json['ACCELEROMETER_READING_COUNT'])

                        gyro_count = ''
                        
                        if 'GYROSCOPE_READING_COUNT' in reading_json:
                            gyro_count = str(reading_json['GYROSCOPE_READING_COUNT'])

                        baro_count = ''
                        
                        if 'BAROMETER_READING_COUNT' in reading_json:
                            baro_count = str(reading_json['BAROMETER_READING_COUNT'])
                            
                        eval_start = ''

                        if 'EVALUATION_WINDOW_START' in reading_json:
                            eval_start = str(reading_json['EVALUATION_WINDOW_START'])

                        eval_end = ''

                        if 'EVALUATION_WINDOW_END' in reading_json:
                            eval_end = str(reading_json['EVALUATION_WINDOW_END'])

                        eval_size = ''

                        if 'EVALUATION_WINDOW_SIZE' in reading_json:
                            eval_end = str(reading_json['EVALUATION_WINDOW_SIZE'])
                        
                        gzf.write(user_hash + '\t' + str(reading_json['TIMESTAMP']) + '\t' + accel_count + '\t' + gyro_count + '\t' + baro_count + '\t' + str(is_fall) + '\t' + str(reading_json['NOT_FALL_ODDS']) + '\t' + str(reading_json['NOT_FALL_SUM']) + '\t' + str(reading_json['NOT_FALL_PROBABILITY']) + '\t' + eval_start + '\t' + eval_end + '\t' + eval_size + '\n')
                            
                    index += 100
                    
                gzf.flush()
                gzf.close()
                
                temp_file.seek(0)
                        
                report = PurpleRobotReport(generated=timezone.now(), mime_type='application/x-gzip', probe=PROBE_NAME, user_id=user_hash)
                report.save()
                report.report_file.save(user_hash + '-fallnet.txt.gz', File(temp_file))
                report.save()

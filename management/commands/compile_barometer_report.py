import datetime
import gzip
import json
import pytz
import sys
import tempfile

from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot.settings import REPORT_DEVICES
from purple_robot_app.models import PurpleRobotReading, PurpleRobotReport

PROBE_NAME = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.PressureProbe'

class Command(BaseCommand):
    def handle(self, *args, **options):
        hashes = REPORT_DEVICES # PurpleRobotPayload.objects.order_by().values('user_id').distinct()

#        start = datetime.datetime.now() - datetime.timedelta(days=120)
        start_ts = datetime.datetime(2015, 7, 3, 5, 0, 0, 0, tzinfo=pytz.timezone('US/Central'))
        end_ts = start_ts + datetime.timedelta(hours=1)
        
        for user_hash in hashes:
            # hash = hash['user_id']

            payloads = PurpleRobotReading.objects.filter(user_id=user_hash, probe=PROBE_NAME, logged__gte=start_ts, logged__lt=end_ts).order_by('logged')
            
            count = payloads.count()
            if count > 0:
                temp_file = tempfile.TemporaryFile()
                gzf = gzip.GzipFile(mode='wb', fileobj=temp_file)
                
                gzf.write('User ID\tSensor Timestamp\ttNormalized Timestamp\tCPU Timestamp\tAltitude\tPressure\n')
                
                index = 0

                last_sensor = sys.maxint
                base_ts = 0
                
                while index < count:
                    end = index + 100
                    
                    if end > count:
                        end = count
                
                    for payload in payloads[index:end]:
                        reading_json = json.loads(payload.payload)
                        
                        ns = []
                        ss = []
                        ts = []
                        xs = []
                        ys = []
                        
                        has_sensor = False
                        
                        if 'SENSOR_TIMESTAMP' in reading_json:
                            has_sensor = True
                            
                            for s in reading_json['SENSOR_TIMESTAMP']:
                                ss.append(s)

                        for t in reading_json['EVENT_TIMESTAMP']:
                            ts.append(t)
                            
                            if has_sensor is False:
                                ss.append(-1)
                                ns.append(-1)

                        if has_sensor:
                            for i in range(0, len(ss)):
                                sensor_ts = float(ss[i])
                                
                                normalized_ts = sensor_ts / (1000 * 1000 * 1000) 
                                
                                if normalized_ts < last_sensor:
                                    cpu_time = ts[i]
                                    
                                    base_ts = cpu_time - normalized_ts
                                    
                                ns.append(base_ts + normalized_ts)
                                
                                last_sensor = normalized_ts
    
                        for x in reading_json['ALTITUDE']:
                            xs.append(x)
    
                        for y in reading_json['PRESSURE']:
                            ys.append(y)
    
                        for i in range(0, len(ts)):
                            x = xs[i]
                            y = ys[i]
                            t = ts[i]
                            s = ss[i]
                            n = ns[i]
                            
                            gzf.write(user_hash + '\t' + str(s) + '\t' + str(n) + '\t' + str(t) + '\t' + str(x) + '\t' + str(y) + '\n')
                            
                    index += 100
                
                gzf.flush()
                gzf.close()
                
                temp_file.seek(0)
                        
                report = PurpleRobotReport(generated=timezone.now(), mime_type='application/x-gzip', probe=PROBE_NAME, user_id=user_hash)
                report.save()
                report.report_file.save(user_hash + '-barometer.txt.gz', File(temp_file))
                report.save()

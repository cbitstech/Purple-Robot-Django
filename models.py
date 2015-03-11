import datetime
import gc
import json
import pytz
import string
import time

from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone

class PurpleRobotConfiguration(models.Model):
    name = models.CharField(max_length=1024)
    slug = models.SlugField(max_length=1024, unique=True)
    contents = models.TextField(max_length=1048576)
    added = models.DateTimeField()

class PurpleRobotPayload(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    payload = models.TextField(max_length=8388608)
    process_tags = models.CharField(max_length=1024, null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=1024, db_index=True)

    errors = models.TextField(max_length=65536, null=True, blank=True)

class PurpleRobotEvent(models.Model):
    event = models.CharField(max_length=1024)
    name = models.CharField(max_length=1024, null=True, blank=True, db_index=True)
    logged = models.DateTimeField()
    user_id = models.CharField(max_length=1024, db_index=True)

    payload = models.TextField(max_length=(1024 * 1024 * 8), null=True, blank=True)
    
    def event_name(self):
        if self.name != None:
            return self.name
            
        if self.event == 'java_exception':
            payload = json.loads(self.payload)
            
            tokens = payload['content_object']['stacktrace'].split(':')
            
            self.name = tokens[0]
            self.save()
            
        return self.name

class PurpleRobotReading(models.Model):
    probe = models.CharField(max_length=1024, null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=1024, db_index=True)
    payload = models.TextField(max_length=8388608)
    logged = models.DateTimeField()
    guid = models.CharField(max_length=1024, db_index=True, null=True, blank=True)
    
EXPORT_JOB_STATE_CHOICES = (
    ('pending', 'Pending'),
    ('processing', 'Processing'),
    ('finished', 'Finished'),
    ('error', 'Error'),
)

class PurpleRobotExportJob(models.Model):
    probes = models.TextField(max_length=8196, null=True, blank=True)
    users = models.TextField(max_length=8196, null=True, blank=True)

    start_date = models.DateField()
    end_date = models.DateField()

    export_file = models.FileField(blank=True, upload_to='export_files')
    destination = models.EmailField(null=True, blank=True)
    
    state = models.CharField(max_length=512, choices=EXPORT_JOB_STATE_CHOICES, default='pending')
    
    def export_file_url(self):
    	return reverse('fetch_export_file', args=[str(self.pk)])

@receiver(pre_delete, sender=PurpleRobotExportJob)
def purplerobotexportjob_delete(sender, instance, **kwargs):
    instance.export_file.delete(False)


class PurpleRobotReport(models.Model):
    probe = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.CharField(max_length=1024)
    generated = models.DateTimeField()
    mime_type = models.CharField(max_length=1024)
    report_file = models.FileField(blank=True, upload_to='report_files')

    def __unicode__(self):
        return string.split(self.probe, '.')[-1]

@receiver(pre_delete, sender=PurpleRobotReport)
def purplerobotreport_delete(sender, instance, **kwargs):
    instance.report_file.delete(False)

class PurpleRobotTest(models.Model):
    active = models.BooleanField(default=False)
    slug = models.SlugField(unique=True)
    probe = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.CharField(max_length=1024)
    frequency = models.FloatField(default=1.0)
    report = models.TextField(default='{}')
    
    last_updated = models.DateTimeField()
    
    def updated_ago(self):
        delta = timezone.now() - self.last_updated
        
        return delta.total_seconds()
    
    def update(self, days=1):
        report = json.loads(self.report)
        
        report_end = time.time()
        report_start = report_end - (days * 24 * 60 * 60)
        
        date_start = pytz.utc.localize(datetime.datetime.utcfromtimestamp(report_start))
        date_end = pytz.utc.localize(datetime.datetime.utcfromtimestamp(report_end))
        
        batteries = []
        
        battery_probe = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.BatteryProbe'
        
        battery_readings = PurpleRobotReading.objects.filter(logged__gte=date_start, logged__lte=date_end, probe=battery_probe, user_id=self.user_id).order_by('logged')
        
        for battery_reading in battery_readings:
            payload = json.loads(battery_reading.payload)
            
            reading = [ payload['TIMESTAMP'], payload['level'] ]
            
            batteries.append(reading)

        batteries = [b for b in batteries if (b[0] >= report_start and b[0] <= report_end)]
        batteries.append([report_start, 0])
        batteries.append([report_end, 0])
        batteries.sort(key=lambda reading: reading[0])
        
        report['battery'] = batteries
        
        pending_files = []
        
        health_probe = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.RobotHealthProbe'
        
        health_readings = PurpleRobotReading.objects.filter(logged__gte=date_start, logged__lte=date_end, probe=health_probe, user_id=self.user_id).order_by('logged')
        
        for health_reading in health_readings:
            payload = json.loads(health_reading.payload)
            
            reading = [ payload['TIMESTAMP'], payload['PENDING_COUNT'], payload['ACTIVE_RUNTIME'] ]
            
            pending_files.append(reading)

        pending_files = [p for p in pending_files if (p[0] >= report_start and p[0] <= report_end)]
        pending_files.append([report_start, 0, 0])
        pending_files.append([report_end, 0, 0])
        pending_files.sort(key=lambda reading: reading[0])
            
        report['pending_files'] = pending_files
        
        # gc.collect()
        
        if ('target' in report) == False:
            report['target'] = []

        timestamps = []
        
        start_date = timezone.now() - datetime.timedelta(days)
            
        target_readings = PurpleRobotReading.objects.filter(probe=self.probe, user_id=self.user_id, logged__gte=date_start).order_by('logged')
        
        total_readings = target_readings.count()
        start_index = 0

        while start_index < total_readings:
            end_index = start_index + 100
            
            for reading in target_readings[start_index:end_index]:
                payload = json.loads(reading.payload)
                
                if 'EVENT_TIMESTAMP' in payload:
                    sensor_time = payload['TIMESTAMP']
                
                    for ts in payload['EVENT_TIMESTAMP']:
#                        timestamps.append(sensor_time)
                        timestamps.append(ts)
                        if ts > 1000000000000:
                            ts = ts / 1000
                   
                        if ts >= report_start and ts <= report_end:
                            timestamps.append(ts)
#                       else:
#                           print('THROWING OUT ' + str(ts) + ' < ' + str(original_start) + ' PK: ' + str(reading.pk)) 
                else:
                    ts = payload['TIMESTAMP']
                    
                    if ts >= report_start and ts <= report_end:
                        timestamps.append(ts)
                        
            start_index = end_index
                    
        timestamps.sort()

        start = report_start
        end = start + (60 * 15)
        
        counts = [ [start, 0] ]
        
        count = 0
        
        for timestamp in timestamps:
            if timestamp < report_start:
                pass
            elif timestamp > report_end:
                pass
            elif timestamp >= start and timestamp < end:
                count += 1
            else:
                while timestamp > end:
                    counts.append([start, count])
                    start = end
                    end = start + (60 * 15)
                    count = 0
                    
                count += 1

        counts.append([start, count])
        counts.append([report_end, None])

#        counts = [p for p in counts if p[0] >= original_start]
#        counts.sort(key=lambda reading: reading[0])
        
        report['target'] = counts
        
        self.report = json.dumps(report, indent=1)

        self.last_updated = timezone.now()
        self.save()
    
    def average_frequency(self):
        report = json.loads(self.report)
        
        readings = report['target']
        
        count = 0.0
        
        for reading in readings:
            if reading[1] != None:
                count += reading[1]
        
        first = float(readings[0][0])
        last = float(readings[-1][0])
        
        return float(count / (last - first))
        
    def passes(self):
        return self.average_frequency() > self.frequency

    def max_gap_size(self):
        report = json.loads(self.report)
        
        readings = report['target']
        
        timestamps = []
        
        for reading in readings:
            timestamps.append(reading[0])
        
        if len(timestamps) <= 1:
            return 0
        
        timestamps.sort()
        
        max_gap = 0
        
        for i in range(0, len(timestamps) - 1):
           one = timestamps[i]
           two = timestamps[i + 1]
           
           gap = two - one
           
           if gap > max_gap:
              max_gap = gap
              
        return max_gap
        
    def frequency_graph_json(self, indent=0):
        report = json.loads(self.report)
        
        output = []
        
        timestamps = report['target']
        
        for timestamp in timestamps:
             if len(timestamp) > 1:
                output.append({ 'x': timestamp[0], 'y': timestamp[1] })
             else:
                output.append({ 'x': timestamp[0], 'y': None })
                
        return json.dumps(output, indent=indent)

    def battery_graph_json(self, indent=0):
        report = json.loads(self.report)
    
        now = time.time()
        start = now - (24 * 60 * 60)
        end = start + (60 * 15)
        
        measurements = [ { 'x': start, 'y': None }]
        
        for record in report['battery']:
            timestamp = record[0]
            
            if timestamp < start:
                pass
            elif timestamp > now:
                pass
            else:
                measurements.append({ 'x': timestamp, 'y': record[1] })

        measurements.append({ 'x': now, 'y': None })

        return json.dumps(measurements, indent=indent)

    def pending_files_graph_json(self, indent=0):
        report = json.loads(self.report)
    
        now = time.time()
        start = now - (24 * 60 * 60)
        end = start + (60 * 15)
        
        measurements = [ { 'x': start, 'y': None }]
        
        for record in report['pending_files']:
            timestamp = record[0]
            
            if timestamp < start:
                pass
            elif timestamp > now:
                pass
            else:
                measurements.append({ 'x': timestamp, 'y': record[1] })

        measurements.append({ 'x': now, 'y': None })

        return json.dumps(measurements, indent=indent)
        
    def last_recorded_sample(self):
        report = json.loads(self.report)
        
        readings = report['target']
        
        timestamps = []
        
        for reading in readings:
            timestamps.append(reading[0])
        
        if len(timestamps) > 0:
            return datetime.datetime.fromtimestamp(timestamps[-1])
        
        return None
        
    def probe_name(self):
        return string.replace(self.probe, 'edu.northwestern.cbits.purple_robot_manager.probes.', '')    
        

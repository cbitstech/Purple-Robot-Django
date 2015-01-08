import datetime
import gc
import json
import string
import time

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
    process_tags = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.CharField(max_length=1024)

    errors = models.TextField(max_length=65536, null=True, blank=True)

class PurpleRobotEvent(models.Model):
    event = models.CharField(max_length=1024)
    logged = models.DateTimeField()
    user_id = models.CharField(max_length=1024)

    payload = models.TextField(max_length=(1024 * 1024 * 8), null=True, blank=True)

class PurpleRobotReading(models.Model):
    probe = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.CharField(max_length=1024)
    payload = models.TextField(max_length=8388608)
    logged = models.DateTimeField()

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
        
        start = time.time() - (days * 24 * 60 * 60)
        
        original_start = start
        
        last_battery = 0
        
        if 'last_battery' in report:
            last_battery = report['last_battery']

        if ('battery' in report) == False:
            report['battery'] = []
            
        batteries = report['battery']
        
        battery_probe = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.BatteryProbe'
        
        battery_readings = PurpleRobotReading.objects.filter(pk__gte=last_battery, probe=battery_probe, user_id=self.user_id).order_by('pk')[:250]
        
        for battery_reading in battery_readings:
            payload = json.loads(battery_reading.payload)
            
            reading = [ payload['TIMESTAMP'], payload['level'] ]
            
            batteries.append(reading)
            
            last_battery = battery_reading.pk

        batteries = [b for b in batteries if b[0] >= start]
        batteries.sort(key=lambda reading: reading[0])
        
        report['battery'] = batteries
        report['last_battery'] = last_battery
        
        gc.collect()
            
        last_health = 0
        
        if 'last_health' in report:
            last_health = report['last_health']

        if ('pending_files' in report) == False:
            report['pending_files'] = []
            
        pending_files = report['pending_files']
        
        health_probe = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.RobotHealthProbe'
        
        health_readings = PurpleRobotReading.objects.filter(pk__gte=last_health, probe=health_probe, user_id=self.user_id).order_by('pk')[:250]
        
        for health_reading in health_readings:
            payload = json.loads(health_reading.payload)
            
            reading = [ payload['TIMESTAMP'], payload['PENDING_COUNT'], payload['ACTIVE_RUNTIME'] ]
            
            pending_files.append(reading)
            
            last_health = health_reading.pk

        pending_files = [p for p in pending_files if p[0] >= start]
        pending_files.sort(key=lambda reading: reading[0])
            
        report['pending_files'] = pending_files
        report['last_health'] = last_health
        
        gc.collect()
        
        if ('target' in report) == False:
            report['target'] = []

        now = time.time()
        start = now - (days * 24 * 60 * 60)
        end = start + (60 * 15)
        
        timestamps = []
        
        start_date = datetime.datetime.now() - datetime.timedelta(days)
            
        target_readings = PurpleRobotReading.objects.filter(probe=self.probe, user_id=self.user_id, logged__gte=start_date)
        
        total_readings = target_readings.count()
        start_index = 0
        
        while start_index < total_readings:
            end_index = start_index + 100
            
            for reading in target_readings[start_index:end_index]:
                payload = json.loads(reading.payload)
                
                if 'EVENT_TIMESTAMP' in payload:
                    for ts in payload['EVENT_TIMESTAMP']:
                        if ts > 1000000000000:
                            ts = ts / 1000
                    
                        if ts > start:
                            timestamps.append(ts)
                else:
                    ts = payload['TIMESTAMP']
                    
                    if ts > start:
                        timestamps.append(ts)
                        
            start_index = end_index
                    
        timestamps.sort()
        
        counts = [ [start, None] ]
        
        count = 0
        
        for timestamp in timestamps:
            if timestamp < start:
                pass
            elif timestamp > now:
                pass
            elif timestamp > start and timestamp < end:
                count += 1
            else:
                while timestamp > end:
                    counts.append([start, count])
                    start = end
                    end = start + (60 * 15)
                    count = 0
                    
                count += 1

        counts.append([start, count])
        counts.append([now, None])

        counts = [p for p in counts if p[0] >= original_start]
        counts.sort(key=lambda reading: reading[0])
        
        report['target'] = counts
        
        self.report = json.dumps(report, indent=1)
        
        self.last_updated = datetime.datetime.now()
        self.save()
    
    def average_frequency(self):
        report = json.loads(self.report)
        
        readings = report['target']
        
        timestamps = []
        
        for reading in readings:
            timestamps.append(reading[0])
        
        if len(timestamps) <= 1:
            return 0
        
        timestamps.sort()
        
        first = timestamps[0]
        last = timestamps[-1]
        
        return len(timestamps) / (last - first)
        
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
        

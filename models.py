import datetime
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
    
    def update(self, days=1):
        report = json.loads(self.report)
        
        start = time.time() - (days * 24 * 60 * 60)
        
        # battery
        
        last_battery = 0
        
        if 'last_battery' in report:
            last_battery = report['last_battery']

        if ('battery' in report) == False:
            report['battery'] = []
            
        batteries = report['battery']
        
        battery_probe = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.BatteryProbe'
        
        battery_readings = PurpleRobotReading.objects.filter(pk__gte=last_battery, probe=battery_probe, user_id=self.user_id).order_by('pk')
        
        for battery_reading in battery_readings:
            payload = json.loads(battery_reading.payload)
            
            reading = [ payload['TIMESTAMP'], payload['level'] ]
            
            batteries.append(reading)
            
            last_battery = battery_reading.pk

        batteries = [b for b in batteries if b[0] >= start]
        batteries.sort(key=lambda reading: reading[0])
        
        report['battery'] = batteries
        report['last_battery'] = last_battery
            
        # remaining files

        last_health = 0
        
        if 'last_health' in report:
            last_health = report['last_health']

        if ('pending_files' in report) == False:
            report['pending_files'] = []
            
        pending_files = report['pending_files']
        
        health_probe = 'edu.northwestern.cbits.purple_robot_manager.probes.builtin.RobotHealthProbe'
        
        health_readings = PurpleRobotReading.objects.filter(pk__gte=last_health, probe=health_probe, user_id=self.user_id).order_by('pk')
        
        for health_reading in health_readings:
            payload = json.loads(health_reading.payload)
            
            reading = [ payload['TIMESTAMP'], payload['PENDING_COUNT'], payload['ACTIVE_RUNTIME'] ]
            
            pending_files.append(reading)
            
            last_health = health_reading.pk

        pending_files = [p for p in pending_files if p[0] >= start]
        pending_files.sort(key=lambda reading: reading[0])
            
        report['pending_files'] = pending_files
        report['last_health'] = last_health
        
        # target probe

        last_target = 0
        
        if 'last_target' in report:
            last_target = report['last_target']

        if ('target' in report) == False:
            report['target'] = []
            
        timestamps = report['target']
            
        target_readings = PurpleRobotReading.objects.filter(pk__gte=last_target, probe=self.probe, user_id=self.user_id).order_by('pk')
        
        for reading in target_readings:
            payload = json.loads(reading.payload)
            
            if 'EVENT_TIMESTAMP' in payload:
                for ts in payload['EVENT_TIMESTAMP']:
                    timestamps.append(ts)
            else:
                    timestamps.append(payload['TIMESTAMP'])
                    
            last_target = reading.pk
                    
        timestamps = [t for t in timestamps if t >= start]
        
        timestamps.sort()
        
        report['target'] = timestamps
        report['last_target'] = last_target
        
        self.report = json.dumps(report, indent=1)
        self.save()
    
    def average_frequency(self):
        report = json.loads(self.report)
        
        timestamps = report['target']
        
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
        
        timestamps = report['target']
        
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
    
        now = time.time()
        start = now - (24 * 60 * 60)
        end = start + (60 * 15)
        
        counts = [{ 'x': start, 'y': None }]
        
        count = 0
        
        for timestamp in report['target']:
            if timestamp < start:
                pass
            elif timestamp > now:
                pass
            elif timestamp > start and timestamp < end:
                count += 1
            else:
                while timestamp > end:
                    counts.append({ 'x': start, 'y': count })
                    start = end
                    end = start + (60 * 15)
                    count = 0
                    
                count += 1

        counts.append({ 'x': start, 'y': count })
        counts.append({ 'x': now, 'y': None})
                
        return json.dumps(counts, indent=indent)

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
        
        if ('target' in report) == False:
            report['target'] = []
        
        if len(report['target']) > 0:
            return datetime.datetime.fromtimestamp(report['target'][-1])
        
        return None
        
    def probe_name(self):
        return string.replace(self.probe, 'edu.northwestern.cbits.purple_robot_manager.probes.', '')    
        

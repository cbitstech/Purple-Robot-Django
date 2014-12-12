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
    timestamps = models.TextField(default='[]')
    
    def average_frequency(self):
        timestamps = json.loads(self.timestamps)
        
        if len(timestamps) <= 1:
            return 0
        
        timestamps.sort()
        
        first = timestamps[0]
        last = timestamps[-1]
        
        return len(timestamps) / (last - first)
        
    def passes(self):
    	return self.average_frequency() > self.frequency

    def max_gap_size(self):
        timestamps = json.loads(self.timestamps)
        
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
        times = json.loads(self.timestamps)
        times.sort()
    
        now = time.time()
        start = now - (24 * 60 * 60)
        end = start + (60 * 15)
        
        counts = []
        
        count = 0
        
        for timestamp in times:
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
                
        return json.dumps(counts, indent=indent)
        
    def last_recorded_sample(self):
        times = json.loads(self.timestamps)
        times.sort()
        
        if len(times) > 0:
            return datetime.datetime.fromtimestamp(times[-1])
        
        return None
        
    def probe_name(self):
        return string.replace(self.probe, 'edu.northwestern.cbits.purple_robot_manager.probes.', '')    
        

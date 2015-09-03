import calendar
import datetime
import importlib
import hashlib
import json
import pytz
import string
import time

from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models import Sum
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone
from django.utils.safestring import SafeString
from django.utils.text import slugify

def my_slugify(str_obj):
    return slugify(str_obj.replace('.', ' ')).replace('-', '_')

class PurpleRobotConfiguration(models.Model):
    name = models.CharField(max_length=1024)
    slug = models.CharField(max_length=1024, unique=True, db_index=True)
    contents = models.TextField(max_length=1048576)
    added = models.DateTimeField()

    def __unicode__(self):
        return self.name
    
    def device_count(self):
        identifiers = set()
        
        for group in self.groups.all():
            for device in group.devices.all():
                identifiers.add(device.device_id)
                
        for device in self.devices.all():
            identifiers.add(device.device_id)
            
        return len(identifiers)
        
    def format(self):
        if self.contents.lower().startswith('(begin'):
            return 'Scheme'
            
        return 'JSON';

class PurpleRobotDeviceGroup(models.Model):
    name = models.CharField(max_length=1024)
    group_id = models.SlugField(max_length=256, unique=True)
    description = models.TextField(max_length=1048576, null=True, blank=True)
    configuration = models.ForeignKey(PurpleRobotConfiguration, related_name='groups', null=True, blank=True)

    def __unicode__(self):
        return self.group_id

class PurpleRobotDevice(models.Model):
    name = models.CharField(max_length=1024)
    device_id = models.CharField(max_length=256, unique=True, db_index=True)
    description = models.TextField(max_length=1048576, null=True, blank=True)
    device_group = models.ForeignKey(PurpleRobotDeviceGroup, related_name='devices', null=True, blank=True)
    configuration = models.ForeignKey(PurpleRobotConfiguration, related_name='devices', null=True, blank=True)
    config_last_fetched = models.DateTimeField(null=True, blank=True)
    config_last_user_agent = models.CharField(max_length=1024, null=True, blank=True)
    hash_key = models.CharField(max_length=128, null=True, blank=True)
    
    performance_metadata = models.TextField(max_length=1048576, default='{}')

    def __unicode__(self):
        return self.device_id
    
    def init_hash(self):
        if self.hash_key == None or len(self.hash_key) < 32:
            m = hashlib.md5()
            m.update(self.device_id.encode('utf-8'))
            
            self.hash_key = m.hexdigest()
            self.save()

    def user_hash(self, start=None, end=None):
        self.init_hash()
        
        return self.hash_key
        
    def fetch_reading_count(self, probe):
        perf_data = json.loads(self.performance_metadata)
        
        if ('reading_counts' in perf_data) and (probe in perf_data['reading_counts']):
            return perf_data['reading_counts'][probe]

        if ('reading_counts' in perf_data) == False:
            perf_data['reading_counts'] = {}
            
        if (probe in perf_data['reading_counts']) == False:
            cursor = connection.cursor()
            cursor.execute("SELECT COUNT(logged) FROM \"purple_robot_app_purplerobotreading\" WHERE (\"purple_robot_app_purplerobotreading\".\"probe\" = '%s' AND \"purple_robot_app_purplerobotreading\".\"user_id\" = '%s' );" % (probe, self.hash_key))
            row = cursor.fetchone()
            perf_data['reading_counts'][probe] = int(row[0])

            self.performance_metadata = json.dumps(perf_data, indent=2)
            self.save()

        return perf_data['reading_counts'][probe]
        
    def set_most_recent_reading(self, new_reading):
        perf_data = json.loads(self.performance_metadata)

        old_reading = None
        updated = False
        
        if ('latest_readings' in perf_data) == False:
            perf_data['latest_readings'] = {}
        else:
            old_reading = PurpleRobotReading.objects.filter(pk=perf_data['latest_readings'][new_reading.probe]).first()

        if ('reading_counts' in perf_data) == False:
            perf_data['reading_counts'] = {}
            
        if (new_reading.probe in perf_data['reading_counts']) == False:
            perf_data['reading_counts'][new_reading.probe] = self.fetch_reading_count(new_reading.probe)
            
        perf_data['reading_counts'][new_reading.probe] = perf_data['reading_counts'][new_reading.probe] + 1

        if ('probes' in perf_data) == False:
            perf_data['probes'] = []
            
        if (new_reading.probe in perf_data['probes']) == False:
            perf_data['probes'].append(new_reading.probe)
            updated = True
        
        if old_reading != None and new_reading.logged > old_reading.logged:
            perf_data['latest_readings'][new_reading.probe] = new_reading.pk
            updated = True
            
        if updated:
            self.performance_metadata = json.dumps(perf_data, indent=2)
            self.save()

    def set_most_recent_payload(self, new_payload):
        perf_data = json.loads(self.performance_metadata)

        old_payload = None
        
        if ('latest_payload' in perf_data) == False:
            perf_data['latest_payload'] = -1
        else:
            old_payload = PurpleRobotPayload.objects.filter(pk=perf_data['latest_payload']).first()
            
        if old_payload != None and new_payload.added > old_payload.added:
            perf_data['latest_payload'] = new_payload.pk
            
            self.performance_metadata = json.dumps(perf_data, indent=2)
            self.save()

    def most_recent_payload(self):
        perf_data = json.loads(self.performance_metadata)
        
        if 'latest_payload' in perf_data:
            return PurpleRobotPayload.objects.filter(pk=perf_data['latest_payload']).first()
        else:
            perf_data['latest_payload'] = -1

        payload = PurpleRobotPayload.objects.filter(user_id=self.hash_key).order_by('-added').first()
        
        if payload != None:
            perf_data['latest_payload'] = payload.pk
        else:
            perf_data['latest_payload'] = -1
                    
        self.performance_metadata = json.dumps(perf_data, indent=2)
        self.save()
        
        return payload

        
    def most_recent_reading(self, probe_name):
        perf_data = json.loads(self.performance_metadata)
        
        if 'latest_readings' in perf_data:
            if probe_name in perf_data['latest_readings']:
                return PurpleRobotReading.objects.filter(pk=perf_data['latest_readings'][probe_name]).first()
        else:
            perf_data['latest_readings'] = {}

        reading = PurpleRobotReading.objects.filter(user_id=self.hash_key, probe=probe_name).order_by('-logged').first()
        
        if reading != None:
            perf_data['latest_readings'][probe_name] = reading.pk
        else:
            perf_data['latest_readings'][probe_name] = -1
                    
        self.performance_metadata = json.dumps(perf_data, indent=2)
        self.save()
        
        return reading

    def clear_most_recent_reading(self, probe_name, new_pk=None):
        perf_data = json.loads(self.performance_metadata)
        
        if 'latest_readings' in perf_data:
            if probe_name in perf_data['latest_readings']:
                if new_pk == None:
                    del perf_data['latest_readings'][probe_name]
                else:
                    perf_data['latest_readings'][probe_name] = new_pk
                
                self.performance_metadata = json.dumps(perf_data, indent=2)
                self.save()
        
    def last_upload(self):
        self.init_hash()
        
        payload = self.most_recent_payload()
        
        if payload != None:
            return payload.added
            
        return None
        
    def last_upload_status(self):
        upload = self.last_upload()
        
        now = timezone.now()
        
        diff = now - upload
        
        if diff.days > 0:
            return "danger"
        elif diff.seconds > (8 * 60 * 60):
            return "warning"
            
        return "ok"

    def config_last_fetched_status(self):
        upload = self.config_last_fetched
        
        now = timezone.now()
        
        diff = now - upload
        
        if diff.days > 1:
            return "danger"
        elif diff.days > 0:
            return "warning"
            
        return "ok"

    def battery_history(self, start=None, end=None):
        self.init_hash()
        
        now = timezone.now()
        
        if start == None:
            start = now - datetime.timedelta(days=1)
            
        if end == None:
            end = now
            
        readings = []
        
        for reading in PurpleRobotReading.objects.filter(user_id=self.hash_key, probe='edu.northwestern.cbits.purple_robot_manager.probes.builtin.BatteryProbe', logged__gte=start, logged__lte=end).order_by('logged'):
            data = json.loads(reading.payload)
            
            timestamp = calendar.timegm(reading.logged.timetuple()) 
            
            if len(readings) == 0 or readings[-1]['level'] != data['level'] or (timestamp - readings[-1]['timestamp']) > (30 * 60):
                item = { 'level': data['level'], 'timestamp': timestamp }
            
            readings.append(item)
        
        return readings

    def last_battery(self):
        self.init_hash()

        data = cache.get(self.hash_key + '__last_battery')
        
        if data != None:
            return data['level']
            
        reading = self.most_recent_reading('edu.northwestern.cbits.purple_robot_manager.probes.builtin.BatteryProbe')
        
        if reading != None:
            data = json.loads(reading.payload)
            
            cache.set(self.hash_key + '__last_battery', data, 15 * 60)
            
            return data['level']
            
        return None

    def last_battery_status(self):
        battery = self.last_battery()
        
        if battery <= 25:
            return "danger"
        elif battery <= 33:
            return "warning"
            
        return "ok"

    def status(self):
        statuses = []
        
        severity = self.alert_severity()
        
        if severity > 1:
            return 'danger'

        if severity > 0:
            return 'warning'
            
        return 'ok'

    def pending_history(self, start=None, end=None):
        self.init_hash()
        
        now = timezone.now()
        
        if start == None:
            start = now - datetime.timedelta(days=1)
            
        if end == None:
            end = now
            
        readings = []
        
        for reading in PurpleRobotReading.objects.filter(user_id=self.hash_key, probe='edu.northwestern.cbits.purple_robot_manager.probes.builtin.RobotHealthProbe', logged__gte=start, logged__lte=end).order_by('logged'):
            data = json.loads(reading.payload)
            
            timestamp = calendar.timegm(reading.logged.timetuple()) 
            
            if len(readings) == 0 or readings[-1]['count'] != data['PENDING_COUNT'] or (timestamp - readings[-1]['timestamp']) > (30 * 60):
                item = { 'count': data['PENDING_COUNT'], 'timestamp': timestamp }
            
            readings.append(item)
        
        return readings

    def last_pending_count(self):
        data = self.last_robot_health()
        
        if data != None:
            return data['PENDING_COUNT']
            
        return None

    def triggers(self):
        data = self.last_robot_health()
        
        if data != None:
            return data['TRIGGERS']
            
        return None

    def last_hardware_info(self):
        self.init_hash()
        
        data = cache.get(self.hash_key + '__last_hardware_info')
        
        if data != None:
            return data
        
        reading = self.most_recent_reading('edu.northwestern.cbits.purple_robot_manager.probes.builtin.HardwareInformationProbe')
        
        if reading != None:
            data = json.loads(reading.payload)
            
            cache.set(self.hash_key + '__last_hardware_info', data)
            
        return data

    def last_model(self):
        data = self.last_hardware_info()
            
        if data != None:
            return data['MODEL']
            
        return None

    def last_robot_health(self):
        self.init_hash()
        
        data = cache.get(self.hash_key + '__last_robot_health')
        
        if data != None:
            return data
    
        reading = self.most_recent_reading('edu.northwestern.cbits.purple_robot_manager.probes.builtin.RobotHealthProbe')
        
        if reading != None:
            data = json.loads(reading.payload)
            
            cache.set(self.hash_key + '__last_robot_health', data)
            
        return data
        
    def last_software_info(self):
        self.init_hash()
        
        data = cache.get(self.hash_key + '__last_software_info')
        
        if data != None:
            return data
    
        reading = self.most_recent_reading('edu.northwestern.cbits.purple_robot_manager.probes.builtin.SoftwareInformationProbe')
        
        if reading != None:
            data = json.loads(reading.payload)
            
            cache.set(self.hash_key + '__last_software_info', data)
            
        return data

    def last_platform(self):
        data = self.last_software_info()
        
        if data != None:
            return 'Android ' + data['RELEASE']
            
        return None

    def last_location(self):
        self.init_hash()

        location = cache.get(self.hash_key + '__last_robot_location')
        
        if location != None:
            return location

        reading = self.most_recent_reading('edu.northwestern.cbits.purple_robot_manager.probes.builtin.LocationProbe')
            
        if reading != None:
            data = json.loads(reading.payload)
            
            location = { 'latitude': data['LATITUDE'], 'longitude': data['LONGITUDE'] }
            
            cache.set(self.hash_key + '__last_robot_location', location)

        return location
    
    def probes(self):
        perf_data = json.loads(self.performance_metadata)

        if ('probes' in perf_data):
            return perf_data['probes']

        perf_data['probes'] = []

        probe_readings = PurpleRobotReading.objects.values('probe').distinct()
        
        for probe_reading in probe_readings:
            item = self.most_recent_reading(probe_reading['probe'])
            
            perf_data['probes'].append(item)
        
        self.performance_metadata = json.dumps(perf_data, indent=2)
        self.save()
        
        return perf_data['probes']
        
        
    def last_readings(self, omit_readings=False):
        self.init_hash()

        readings = []
        
        for probe_name in self.probes():
            item = self.most_recent_reading(probe_name)
            
            if item != None:
                reading = {}
            
                reading['name'] = item.probe.split('.')[-1]
                reading['full_probe_name'] = item.probe
                reading['last_update'] = item.logged
            
                if omit_readings == False:
#                    cursor = connection.cursor()
#                    cursor.execute("SELECT COUNT(logged) FROM \"purple_robot_app_purplerobotreading\" WHERE (\"purple_robot_app_purplerobotreading\".\"probe\" = '%s' AND \"purple_robot_app_purplerobotreading\".\"user_id\" = '%s' );" % (item.probe, self.hash_key))
#                    row = cursor.fetchone()
                    reading['num_readings'] = self.fetch_reading_count(probe_name)
#                    reading['num_readings'] = 0
#                    reading['num_readings'] = PurpleRobotReading.objects.filter(user_id=self.hash_key, probe=item.probe).count()
                    reading['status'] = 'TODO'

                    reading['frequency'] = 'Unknown'
                
                    for test in PurpleRobotTest.objects.filter(probe=item.probe, user_id=self.hash_key):
                        reading['frequency'] = test.average_frequency()
            
                readings.append(reading)
        
        readings = sorted(readings, key=lambda k: k['name']) 
        
        return readings
        
    def data_size_history(self, unit='day', count=None):
        now = timezone.localtime(timezone.now())
        
        bin_size = None
        count = 0
        
        if unit == 'day':
            bin_size = datetime.timedelta(days=1)
            end = datetime.datetime(now.year, now.month, now.day, 0, 0, 0, 0, now.tzinfo)
            end = end + bin_size
            count = 7
        elif unit == 'hour':
            bin_size = datetime.timedelta(seconds=(60 * 60))
            end = datetime.datetime(now.year, now.month, now.day, now.hour, 0, 0, 0, now.tzinfo)
            end = end + in_size
            count = 48
        elif unit == 'minute':
            bin_size = datetime.timedelta(seconds=60)
            end = datetime.datetime(now.year, now.month, now.day, now.hour, now.minute, 0, 0, now.tzinfo)
            end = end + datetime.timedelta(seconds=60)
            count = 240
            
        size_history = []
        
        while count > 0:
            start = end - bin_size
            
#            size = 0
#            
#            readings = PurpleRobotReading.objects.filter(user_id=self.hash_key, logged__gte=start, logged__lt=end, size=0)[:250]
#            
#            while readings.count() > 0:
#                for reading in readings:
#                    reading.size = len(reading.payload)
#                    reading.save()
#                
#                readings = PurpleRobotReading.objects.filter(user_id=self.hash_key, logged__gte=start, logged__lt=end, size=0)[:250]
                
            size = PurpleRobotReading.objects.filter(user_id=self.hash_key, logged__gte=start, logged__lt=end).aggregate(Sum('size'))
            
            start_ts = time.mktime(start.timetuple())
            end_ts = time.mktime(end.timetuple())
            
            total_size = size['size__sum']
            
            if total_size == None:
                total_size = 0
            
            history_point = { 'size': total_size, 'timestamp':  ((start_ts + end_ts) / 2) }
            
            size_history.append(history_point)
            
            end = start
            count -= 1
            
            
        return reversed(size_history)

    def events(self, start=None, end=None):
        self.init_hash()
        
        now = timezone.now()
        
        if start == None:
            start = now - datetime.timedelta(days=7)
            
        if end == None:
            end = now
            
        return PurpleRobotEvent.objects.filter(user_id=self.hash_key, logged__gte=start, logged__lte=end).order_by('-logged')
        
    def alerts(self):
        self.init_hash()
        
        return PurpleRobotAlert.objects.filter(dismissed=None, user_id=self.hash_key)
        
    def alert_count(self):
        return self.alerts().count()
        
    def alert_severity(self):
        severity = 0
        
        for alert in self.alerts():
            if alert.severity > severity:
                severity = alert.severity
                
        return severity
        
    def visualization_for_probe(self, probe_name):
        formatter_name = my_slugify(probe_name).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')
    
        try:
            formatter = importlib.import_module('purple_robot_app.formatters.' + formatter_name)
        except ImportError:
            formatter = importlib.import_module('purple_robot_app.formatters.probe')
            
        readings = PurpleRobotReading.objects.filter(user_id=self.user_hash, probe=probe_name).order_by('-logged')[:500]
        
        return formatter.visualize(probe_name, readings)

class PurpleRobotPayload(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    payload = models.TextField(max_length=8388608)
    process_tags = models.CharField(max_length=1024, null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=1024, db_index=True)

    errors = models.TextField(max_length=65536, null=True, blank=True)
    
    def ingest_readings(self):
        tags = self.process_tags
        
        tag = 'extracted_readings'
    
        items = json.loads(self.payload)
    
        device = PurpleRobotDevice.objects.filter(hash_key=self.user_id).first()

        if device != None:
            device.set_most_recent_payload(self)

        for item in items:
            try:
                reading = PurpleRobotReading(probe=item['PROBE'], user_id=self.user_id)
                reading.payload = json.dumps(item, indent=2)
                reading.logged = datetime.datetime.utcfromtimestamp(item['TIMESTAMP']).replace(tzinfo=pytz.utc)
                reading.guid = item['GUID']
                reading.size = len(reading.payload)

                reading.save()
            
                if device != None:
                    device.set_most_recent_reading(reading)
            except KeyError:
                if tags is None or len(tags) == 0:
                    tags = 'ingest_error'
                else:
                    tags += ' ingest_error'
    
        if tags is None or tags.find(tag) == -1:
            if tags is None or len(tags) == 0:
                tags = tag
            else:
                tags += ' ' + tag
            
            self.process_tags = tags
        
            self.save()
    

class PurpleRobotEvent(models.Model):
    event = models.CharField(max_length=1024)
    name = models.CharField(max_length=1024, null=True, blank=True, db_index=True)
    logged = models.DateTimeField()
    user_id = models.CharField(max_length=1024, db_index=True)

    payload = models.TextField(max_length=(1024 * 1024 * 8), null=True, blank=True)
    
    def event_name(self):
        if self.name is None:
            return self.name
            
        if self.event == 'java_exception':
            payload = json.loads(self.payload)
            
            tokens = payload['content_object']['stacktrace'].split(':')
            
            self.name = tokens[0]
            self.save()
            
        return self.name
        
    def description(self):
        payload = json.loads(self.payload)
        
        if self.event == 'pr_script_log_message':
            return payload['message']
        elif self.event == 'set_user_id':
            return SafeString(payload['old_id'] + ' &rarr; ' + payload['new_id'])
        elif self.event == 'java_exception':
            return payload['stacktrace'].split('\n')[0]
        elif self.event == 'broadcast_message':
            return payload['message']
        
        return self.event + ' (' + str(self.pk) + ')'

class PurpleRobotReading(models.Model):
    probe = models.CharField(max_length=1024, null=True, blank=True, db_index=True)
    user_id = models.CharField(max_length=1024, db_index=True)
    payload = models.TextField(max_length=8388608)
    logged = models.DateTimeField(db_index=True)
    guid = models.CharField(max_length=1024, db_index=True, null=True, blank=True)
    size = models.IntegerField(default=0)
    
    attachment = models.FileField(upload_to='reading_attachments', null=True, blank=True)
    
    class Meta:
        index_together = [
            ['probe', 'user_id'],
            ['logged', 'user_id'],
            ['probe', 'logged', 'user_id'],
        ]

    def probe_name(self):
        return self.probe.replace('edu.northwestern.cbits.purple_robot_manager.probes.', '')
        
    def update_guid(self):
        if self.guid != None:
            return
            
        reading_json = json.loads(self.payload)
        
        self.guid = reading_json['GUID']
        self.save()
        
    def fetch_summary(self):
        probe_name = my_slugify(self.probe).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')
    
        try:
            formatter = importlib.import_module('purple_robot_app.formatters.' + probe_name)
        except ImportError:
            formatter = importlib.import_module('purple_robot_app.formatters.probe')
        
        return formatter.format(probe_name, self.payload)
        
    def payload_value(self):
        return json.loads(self.payload)

@receiver(pre_delete, sender=PurpleRobotReading)
def purplerobotreport_delete(sender, instance, **kwargs):
    instance.attachment.delete(False)
    
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
        
        battery_readings = PurpleRobotReading.objects.filter(logged__gte=date_start, \
                                                             logged__lte=date_end, \
                                                             probe=battery_probe, \
                                                             user_id=self.user_id).order_by('logged')
        
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
        
        health_readings = PurpleRobotReading.objects.filter(logged__gte=date_start, \
                                                            logged__lte=date_end, \
                                                            probe=health_probe, \
                                                            user_id=self.user_id).order_by('logged')
        
        for health_reading in health_readings:
            payload = json.loads(health_reading.payload)
            
            reading = [ payload['TIMESTAMP'], payload['PENDING_COUNT'], payload['ACTIVE_RUNTIME'] ]
            
            pending_files.append(reading)

        pending_files = [p for p in pending_files if (p[0] >= report_start and p[0] <= report_end)]
        pending_files.append([report_start, 0, 0])
        pending_files.append([report_end, 0, 0])
        pending_files.sort(key=lambda reading: reading[0])
            
        report['pending_files'] = pending_files
        
        if ('target' in report) == False:
            report['target'] = []

        timestamps = []
            
        target_readings = PurpleRobotReading.objects.filter(probe=self.probe, user_id=self.user_id, logged__gte=date_start).order_by('logged')
        
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
                   
                        if ts >= report_start and ts <= report_end:
                            timestamps.append(ts)
                elif 'SENSOR_TIMESTAMP' in payload:
                    sensor_time = payload['TIMESTAMP']
                
                    for ts in payload['SENSOR_TIMESTAMP']:
                        if ts > 1000000000000:
                            ts = ts / 1000
                   
                        if ts >= report_start and ts <= report_end:
                            timestamps.append(ts)
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
            if timestamp < report_start or timestamp > report_end:
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

        report['target'] = counts
        
        self.report = json.dumps(report, indent=1)

        self.last_updated = timezone.now()
        self.save()
        
    
    def average_frequency(self):
        report = json.loads(self.report)
        
        try:
            readings = report['target']
        
            count = 0.0
        
            for reading in readings:
                if reading[1] is not None:
                    count += reading[1]
        
            first = float(readings[0][0])
            last = float(readings[-1][0])
        
            return float(count / (last - first))
        except KeyError:
            return -1
        
    def passes(self):
        return self.average_frequency() > self.frequency

    def max_gap_size(self):
        report = json.loads(self.report)
        
        if 'target' in report:
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
        
        return -1
        
    def frequency_graph_json(self, indent=0):
        report = json.loads(self.report)
        
        output = []
        
        if 'target' in report:
            timestamps = report['target']
        
            for timestamp in timestamps:
                if len(timestamp) > 1:
                    output.append({ 'x': timestamp[0], 'y': timestamp[1] })
                else:
                    output.append({ 'x': timestamp[0], 'y': None })
                
            return json.dumps(output, indent=indent)
            
        return '[]'

    def battery_graph_json(self, indent=0):
        report = json.loads(self.report)
    
        now = time.time()
        start = now - (24 * 60 * 60)
        
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
        
        if 'target' in report:
            readings = report['target']
        
            timestamps = []
        
            for reading in readings:
                timestamps.append(reading[0])
        
            if len(timestamps) > 0:
                return datetime.datetime.fromtimestamp(timestamps[-1])
        
        return None
        
    def probe_name(self):
        return string.replace(self.probe, 'edu.northwestern.cbits.purple_robot_manager.probes.', '')    
        

class PurpleRobotAlert(models.Model):
    severity = models.IntegerField(default=0)
    message = models.CharField(max_length=2048)
    tags = models.CharField(max_length=2048, null=True, blank=True)
    
    action_url = models.URLField(max_length=1024, null=True, blank=True)
    
    probe = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.CharField(max_length=1024, null=True, blank=True)
    generated = models.DateTimeField()
    dismissed = models.DateTimeField(null=True, blank=True)
    
    manually_dismissed = models.BooleanField(default=False)

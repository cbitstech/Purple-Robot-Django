import datetime
import os

from sexpdata import *

from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDevice, PurpleRobotConfiguration, PurpleRobotReading
from purple_robot_app.management.commands.pr_check_status import log_alert, cancel_alert

TAG = 'expected_probe_missing'
START_DAYS = 7

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

def enabled_probes(contents):
    probes = []
    
    if isinstance(contents, Symbol):
        pass
    elif isinstance(contents, basestring):
        pass
    elif isinstance(contents, (int, float)):
        pass
    elif isinstance(contents, Quoted):
        return enabled_probes(contents.value())
    elif car(contents) == Symbol('pr-update-probe'):
        probe_name = None
        probe_enabled = False
        
        for item in cdr(contents):
            if isinstance(item, Quoted):
                item = item.value()
                
            for child in item:
                if car(child) == 'name':
                    probe_name = cdr(child)
                elif car(child) == 'enabled':
                    probe_enabled = cdr(child)
                
        if probe_name != None and probe_enabled and (probe_name in probes) == False:
            probes.append(probe_name)
    else:
        for item in contents:
            found_probes = enabled_probes(item)
            
            for found in found_probes:
                if (found in probes) == False:
                    probes.append(found)
    
    return probes

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/expected_probe_missing_check.lock', os.R_OK):
            t = os.path.getmtime('/tmp/expected_probe_missing_check.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 60 * 60 * 4:
                print('expected_probe_missing_check: Stale lock - removing...')
                os.remove('/tmp/expected_probe_missing_check.lock')
            else:
                return
    
        touch('/tmp/expected_probe_missing_check.lock')

        start = timezone.now() - datetime.timedelta(days=START_DAYS)
        
        for device in PurpleRobotDevice.objects.all().order_by('device_id'):
            config = None
            
            default = PurpleRobotConfiguration.objects.filter(slug='default').first()
            
            if device.configuration != None:
                config = device.configuration
            elif device.device_group.configuration != None:
                config = device.device_group.configuration
            elif config == None:
                config = default
            
            if config == None:
                log_alert(message='No configuration associated with ' + device.device_id + '.', severity=2, tags=TAG, user_id=device.hash_key)
            else:
                config_probes = enabled_probes(loads(config.contents, true='#t', false='#f'))
                
                missing_probes = []
                
                for probe in config_probes:
                    found = device.most_recent_reading(probe)
                    
                    if found == None or found.logged < start:
                        missing_probes.append(probe.split('.')[-1])
                        
#                        if found == None:
#                            print(device.device_id + ' ' + str(config) + ': ' + probe)

                        
                if len(missing_probes) == 0:
                    cancel_alert(tags=TAG, user_id=device.hash_key)
                else:
                    log_alert(message='Missing data from ' + str(len(missing_probes)) + ' probe(s). Absent probes: ' + ', '.join(missing_probes), severity=2, tags=TAG, user_id=device.hash_key)

        os.remove('/tmp/expected_probe_missing_check.lock')

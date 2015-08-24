import datetime
import json
import importlib
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from purple_robot_app.models import PurpleRobotReading, PurpleRobotPayload

def my_slugify(str_obj):
    return slugify(str_obj.replace('.', ' ')).replace('-', '_')

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            settings.PURPLE_ROBOT_FLAT_MIRROR
        except AttributeError:
            return

        open('/tmp/extract_into_database.lock', 'wa').close() 

        if os.access('/tmp/extract_into_database.lock', os.R_OK):
            t = os.path.getmtime('/tmp/extract_into_database.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 120:
                print('extract_into_database: Stale lock - removing...')
                os.remove('/tmp/extract_into_database.lock')
            else:
                return
    
        touch('/tmp/extract_into_database.lock')

        tag = 'extracted_into_database'
        skip_tag = 'extracted_into_database_skip'
        
        # payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).order_by('added')[:100]
        payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).order_by('-added')[:100]
        
        while payloads.count() > 0:
            for payload in payloads:
                print('PAYLOAD ' + str(payload.added) + ' / ' + str(payload.pk))
                
                items = json.loads(payload.payload)
                
                has_all_extractors = True
                missing_extractors = []

                for item in items:
                    probe_name = my_slugify(item['PROBE']).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')
                    
                    try:
                        probe = importlib.import_module('purple_robot_app.management.commands.extractors.' + probe_name)
                    except ImportError:
                        has_all_extractors = False
                        missing_extractors.append(probe_name)
                        
                if has_all_extractors:
                    for item in items:
                        probe_name = my_slugify(item['PROBE']).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')
                    
                        probe = importlib.import_module('purple_robot_app.management.commands.extractors.' + probe_name)
                    
                        if probe.exists(settings.PURPLE_ROBOT_FLAT_MIRROR, payload.user_id, item) == False:
                            # print('PROBE: ' + probe_name)                
                            probe.insert(settings.PURPLE_ROBOT_FLAT_MIRROR, payload.user_id, item)

                    tags = payload.process_tags
                
                    if tags is None or tags.find(tag) == -1:
                        if tags is None or len(tags) == 0:
                            tags = tag
                        else:
                            tags += ' ' + tag
                        
                        payload.process_tags = tags
                    
                        payload.save()
                else:
                    tags = payload.process_tags
                    
                    if tags is None or tags.find(skip_tag) == -1:
                        if tags is None or len(tags) == 0:
                            tags = skip_tag
                        else:
                            tags += ' ' + skip_tag
                        
                        payload.process_tags = tags
                    
                        payload.save()
                
                if len(missing_extractors) > 0:
                    print('MISSING EXTRACTORS: ' + str(missing_extractors))
                
            payloads = PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).order_by('-added')[:100]
            
        os.remove('/tmp/extract_into_database.lock')

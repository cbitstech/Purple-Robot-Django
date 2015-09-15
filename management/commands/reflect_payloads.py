import datetime
import hashlib
import json
import requests
import os
import sys
import time

from requests.exceptions import ConnectionError, ReadTimeout

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction

from purple_robot_app.models import PurpleRobotPayload, PurpleRobotReading

PRINT_PROGRESS = False

# Via http://stackoverflow.com/questions/1158076/implement-touch-using-python

def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            settings.PR_REDIRECT_ENDPOINT_MAP
        except AttributeError:
            print 'PR_REDIRECT_ENDPOINT_MAP not defined in settings.py. Exiting...'
            
            return

        if os.access('/tmp/reflected_payload.lock', os.R_OK):
            t = os.path.getmtime('/tmp/reflected_payload.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 120:
                print('reflect_payloads: Stale lock - removing...')
                os.remove('/tmp/reflected_payload.lock')
            else:
                return
    
        touch('/tmp/reflected_payload.lock')
        
        tag = 'reflected_payload'

        requests.packages.urllib3.disable_warnings()
        
        reflected_payloads = []
        
        for config in settings.PR_REDIRECT_ENDPOINT_MAP:
            payloads = PurpleRobotPayload.objects.filter(user_id=config['hash']).exclude(process_tags__contains=tag)[:50]
        
            if payloads.count() > 0:
                if PRINT_PROGRESS:
                    print('')
            
                for pr_payload in payloads:
                    payload = {}
                    payload['Payload'] = pr_payload.payload
                    payload['Operation'] = 'SubmitProbes'

                    m = hashlib.md5()
                    m.update(config['new_id'].encode('utf-8'))
                    payload['UserHash'] = m.hexdigest()
        
                    m = hashlib.md5()
                    m.update((payload['UserHash'] + payload['Operation'] + payload['Payload']).encode('utf-8'))
                    payload['Checksum'] = m.hexdigest()

                    data = { 'json': json.dumps(payload, indent=2) }
                
                    files = {}
                
                    if 'media_url' in pr_payload.payload:
                        readings = json.loads(pr_payload.payload)
                    
                        for reading in readings:
                            if 'media_url' in reading:
                                pr_reading = PurpleRobotReading.objects.filter(guid=reading['GUID']).first()
                            
                                if pr_reading != None and pr_reading.attachment != None:
                                    reading_json = json.loads(pr_reading.payload)
                                
                                    filename = pr_reading.attachment.name.split('/')[-1]
                                    files[pr_reading.guid] = (filename, pr_reading.attachment, reading_json['media_content_type'],)
                                    
                    try:
                        response = requests.post(config['endpoint'], data=data, verify=False, timeout=120.0, files=files)
                
                        response_obj = json.loads(response.text)
                
                        if response_obj['Status'] == 'success':
                            reflected_payloads.append(pr_payload.pk)
                        
                            touch('/tmp/reflected_payload.lock')
                    except ValueError:
                        # Missing attachment error - continue on...
                        
                        reflected_payloads.append(pr_payload.pk)
                    
                        touch('/tmp/reflected_payload.lock')
                    except ConnectionError:
                        pass
                    except ReadTimeout:
                        pass

        for pk in reflected_payloads:
            pr_payload = PurpleRobotPayload.objects.get(pk=pk)
            
            tags = pr_payload.process_tags

            if tags is None or tags.find(tag) == -1:
                if tags is None or len(tags) == 0:
                    tags = tag
                else:
                    tags += ' ' + tag
    
                pr_payload.process_tags = tags

                pr_payload.save()
                
        os.remove('/tmp/reflected_payload.lock')
        

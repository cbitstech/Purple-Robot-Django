import hashlib
import json
import requests
import os
import sys
import time

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotPayload

ENDPOINT_MAP = {
    '073adb668d74a6aaa7d452eb9f804c99': {
        'endpoint': 'http://omar.cbitstech.net/pr/',
        'new_id': 'cjkarr@gmail.com'
    },
    'e1c80488853d86ab9d6decfe30d8930f': {
        'endpoint': 'http://omar.cbitstech.net/pr/',
        'new_id': 'g2'
    },
    'd1d0518f47d0c65397526c041635770f': {
        'endpoint': 'http://omar.cbitstech.net/pr/',
        'new_id': 'galaxia'
    }
}

PRINT_PROGRESS = False

class Command(BaseCommand):
    def handle(self, *args, **options):
        sys.stdout.flush()

        if os.access('/tmp/reflected_payload.lock', os.R_OK):
            return

        sys.stdout.flush()
    
        open('/tmp/reflected_payload.lock', 'wa').close() 
        
        sys.stdout.flush()
        
        tag = 'reflected_payload'

        requests.packages.urllib3.disable_warnings()
        
        for orig_hash, config in ENDPOINT_MAP.iteritems():
            payloads = PurpleRobotPayload.objects.filter(user_id=orig_hash).exclude(process_tags__contains=tag).order_by('-pk')[:100]
            
            while payloads.count() > 0:
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
                    
                    try:
                        requests.post(config['endpoint'], data=data, verify=False, timeout=5.0)

                        tags = pr_payload.process_tags
                
                        if tags is None or tags.find(tag) == -1:
                            if tags is None or len(tags) == 0:
                                tags = tag
                            else:
                                tags += ' ' + tag
                        
                            pr_payload.process_tags = tags
                    
                            pr_payload.save()
                        if PRINT_PROGRESS:
                            sys.stdout.write('.')
                            sys.stdout.flush()
                    except:
                        if PRINT_PROGRESS:
                            sys.stdout.write('-')
                            sys.stdout.flush()
                        
                payloads = PurpleRobotPayload.objects.filter(user_id=orig_hash).exclude(process_tags__contains=tag).order_by('-pk')[:100]
                
        os.remove('/tmp/reflected_payload.lock')
        

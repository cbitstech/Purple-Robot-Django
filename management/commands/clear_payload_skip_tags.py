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

SKIP_TAG = 'extracted_into_database_skip'


def touch(fname, mode=0o666, dir_fd=None, **kwargs):
    flags = os.O_CREAT | os.O_APPEND
    
    with os.fdopen(os.open(fname, flags, mode)) as f:
        os.utime(fname, None)

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/clear_payload_skip_tags.lock', os.R_OK):
            t = os.path.getmtime('/tmp/clear_payload_skip_tags.lock')
            created = datetime.datetime.fromtimestamp(t)
            
            if (datetime.datetime.now() - created).total_seconds() > 300:
                print('clear_payload_skip_tags: Stale lock - removing...')
                os.remove('/tmp/clear_payload_skip_tags.lock')
            else:
                return
    
        touch('/tmp/clear_payload_skip_tags.lock')
        
        requests.packages.urllib3.disable_warnings()
        
        reflected_payloads = []
        
        payloads = list(PurpleRobotPayload.objects.filter(process_tags__contains=SKIP_TAG).order_by('-added')[:250])
        
        count = 0
        
        while len(payloads) > 0 and count < 20:
            count += 1
            
            for payload in payloads:
                print('0: ' + payload.process_tags + ' - ' + str(payload.added))
                payload.process_tags = payload.process_tags.replace(SKIP_TAG, '')
            
                while payload.process_tags.find('  ') != -1:
                    payload.process_tags = payload.process_tags.replace('  ', ' ')
                
                payload.process_tags = payload.process_tags.strip()

                print('1: ' + payload.process_tags)
                
                touch('/tmp/clear_payload_skip_tags.lock')

                payload.save()

            payloads = list(PurpleRobotPayload.objects.filter(process_tags__contains=SKIP_TAG).order_by('-added')[:250])
                
        os.remove('/tmp/clear_payload_skip_tags.lock')
        

import hashlib
import json
import requests

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotPayload

ENDPOINT_MAP = {
    '93fe1dcad472a18492184f16f02f6ad4': {
        'endpoint': 'https://pri02.cbits.northwestern.edu/prImporter',
        'new_id': 'LIVEWELL0009'
    }
}


class Command(BaseCommand):
    def handle(self, *args, **options):
        tag = 'reflected_payload'

        requests.packages.urllib3.disable_warnings()
        
        for orig_hash, config in ENDPOINT_MAP.iteritems():
            for pr_payload in PurpleRobotPayload.objects.filter(user_id=orig_hash).exclude(process_tags__contains=tag).order_by('-pk'):
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
            
                requests.post(config['endpoint'], data=data, verify=False)

                tags = pr_payload.process_tags
                
                if tags is None or tags.find(tag) == -1:
                    if tags is None or len(tags) == 0:
                        tags = tag
                    else:
                        tags += ' ' + tag
                        
                    pr_payload.process_tags = tags
                    
                    pr_payload.save()

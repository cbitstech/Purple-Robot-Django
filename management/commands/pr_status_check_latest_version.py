import datetime
import json
import requests

from BeautifulSoup import BeautifulSoup

from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDevice, PurpleRobotReading, my_slugify
from purple_robot_app.management.commands.pr_check_status import log_alert, cancel_alert

TAG = 'running_latest_version'

class Command(BaseCommand):
    def handle(self, *args, **options):
        play_url = 'https://play.google.com/store/apps/details?id=edu.northwestern.cbits.purple_robot_manager'
        
        r = requests.get(play_url)
        
        soup = BeautifulSoup(r.text)
        
        if soup != None:
            changelog = ''
            
            changes = soup.findAll('div', { 'class': 'recent-change' })
            
            for change in changes:
                if len(changelog) > 0:
                    changelog += '\n'
                    
                changelog += change.contents[0].strip()
                
            version_html = soup.find('div', { 'class': 'content', 'itemprop': 'softwareVersion' })
            
            version = version_html.contents[0].strip()
            
            version_code = None
            version_code_html = soup.findAll('button', { 'class': 'dropdown-child' })
            
            for div in version_code_html:
                if div.contents[0].strip() == 'Latest Version':
                    version_code = float(div['data-dropdown-value'])

            for device in PurpleRobotDevice.objects.filter(mute_alerts=False):
                device_version = device.config_last_user_agent
                
                if device_version == None:
                    log_alert(message='Unable to determine installed version.', severity=1, tags=TAG, user_id=device.hash_key)
                elif device_version.endswith(str(version)):
                    cancel_alert(tags=TAG, user_id=device.hash_key)
                else:
                    log_alert(message='Running an older version on Purple Robot: ' + device_version + '.', severity=1, tags=TAG, user_id=device.hash_key)
        else:
            print('Unable to fetch Play Store metadata.')

        

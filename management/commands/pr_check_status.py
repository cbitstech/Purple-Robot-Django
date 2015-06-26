import os

from django.core.management import call_command, find_management_module, find_commands, load_command_class
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db.models import Q
from django.utils import timezone

from purple_robot_app.models import PurpleRobotAlert

def fetch_query(message=None, severity=None, tags=None, user_id=None, probe=None, dismissed=False):
    q = Q(dismissed=None)
    
    if dismissed:
        q = Q(dismissed__lte=timezone.now())
    
    if message != None:
        q = q & Q(message=message)
    
    if severity != None:
        q = q & Q(severity=severity)
        
    if tags != None:
        q = q & Q(tags__contains=tags)
        
    if user_id != None:
        q = q & Q(user_id=user_id)
        
    if probe != None:
        q = q & Q(probe=probe)
        
    return q

def log_alert(message=None, severity=None, tags=None, user_id=None, probe=None):
    q = fetch_query(None, None, tags, user_id, probe)
    
    now = timezone.now()
    
    alerts = PurpleRobotAlert.objects.filter(q)
    
    if alerts.count() > 0:
        for alert in alerts:
            if message != None:
                alert.message = message
                
            if severity != None:
                alert.severity = severity
                
            alert.save()
    else:
        alert = PurpleRobotAlert(message=message, severity=severity, tags=tags, probe=probe, user_id=user_id, generated=now)
        alert.save()


def cancel_alert(message=None, severity=None, tags=None, user_id=None, probe=None):
    q = fetch_query(message, severity, tags, user_id, probe)
    
    now = timezone.now()
    
    for alert in PurpleRobotAlert.objects.filter(q):
        alert.dismissed = now
        alert.manually_dismissed = True
        
        alert.save()

class Command(BaseCommand):
    def handle(self, *args, **options):
        if os.access('/tmp/check_status.lock', os.R_OK):
            return
    
        open('/tmp/check_status.lock', 'wa').close() 
        
        command_names = find_commands(find_management_module('purple_robot_app'))
        
        for command_name in command_names:
            if command_name.startswith('pr_status_check_'):
                print('Running: ' + command_name)
                call_command(command_name)

        os.remove('/tmp/check_status.lock')

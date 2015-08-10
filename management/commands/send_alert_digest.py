from django.conf import settings
from django.contrib.auth.models import Group
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.template import Context
from django.template.loader import render_to_string

from purple_robot_app.models import PurpleRobotAlert, PurpleRobotDevice

class Command(BaseCommand):
    def handle(self, *args, **options):
        group = Group.objects.filter(name=settings.PURPLE_ROBOT_ADMIN_GROUP).first()
        
        if group != None:
            users = group.user_set.all()
        
            recipient_list = []
        
            for user in users:
                recipient_list.append(user.email)
        
            alerts = PurpleRobotAlert.objects.filter(dismissed=None).order_by('user_id', '-severity')
        
            c = Context()
            c['alerts'] = alerts

            if alerts.count() > 0 and len(recipient_list) > 0:
                from_addr = settings.PURPLE_ROBOT_EMAIL_SENDER
            
                devices = {}
            
                for alert in alerts:
                    device = PurpleRobotDevice.objects.get(hash_key=alert.user_id)
                
                    device_alerts = []
                
                    if device.name in devices:
                        device_alerts = devices[device.name]
                    else:
                        devices[device.name] = device_alerts
                    
                    device_alerts.append(alert)
                
                c['devices'] = devices

                message = render_to_string('email_admin_alert_content.txt', c)
                subject = render_to_string('email_admin_alert_subject.txt', c)

                send_mail(subject, message, from_addr, recipient_list, fail_silently=False)

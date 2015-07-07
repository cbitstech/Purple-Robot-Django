from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group

from purple_robot_app.models import PurpleRobotAlert, PurpleRobotDevice

class Command(BaseCommand):
    def handle(self, *args, **options):
        group = Group.objects.get(name="Monitors")
        users = group.user_set.all()
        recipient_list = []
        for user in users:
            recipient_list.append(user.email)
        
        alerts = PurpleRobotAlert.objects.filter(dismissed=None).order_by('user_id', '-severity')
        
        if len(alerts) > 0 and len(recipient_list) > 0:
            subject, from_email = 'Purple Robot Alert Daily Digest', 'purplerobot@cbitstech.net'
            text_content = "You have " + str(len(alerts)) + " active alert(s) in the Purple Robot dashboard:\n"
            
            devices = []
            count = 1
            for alert in alerts:
                device = PurpleRobotDevice.objects.get(hash_key=alert.user_id)
                
                if device.name in devices:
                    text_content += "{0}. {1} \n".format(count, alert.message)
                else:
                    count = 1
                    text_content += "\n"
                    text_content += device.name + "\n"
                    devices.append(device.name)
                    text_content += "{0}. {1} \n".format(count, alert.message)
                count += 1

            send_mail(subject, text_content, from_email, recipient_list, fail_silently=False)
            
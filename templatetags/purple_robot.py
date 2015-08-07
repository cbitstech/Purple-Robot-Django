import datetime
import pytz

from django import template
from django.conf import settings
from django.core.cache import cache
from django.template.defaultfilters import stringfilter
from django.template.loader import render_to_string
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDeviceGroup, PurpleRobotAlert

register = template.Library()

@register.tag(name="pr_home_custom_console")
def tag_pr_home_custom_console(parser, token):
    return HomeCustomConsoleNode()

class HomeCustomConsoleNode(template.Node):
    def __init__(self):
        pass

    def render(self, context):
        try:
            return settings.PURPLE_ROBOT_HOME_CONSOLE(context)
        except AttributeError:
            pass
        
        return render_to_string('tag_pr_home_custom_console_unknown.html')

@register.tag(name="pr_device_custom_console")
def tag_pr_device_custom_console(parser, token):
    return DeviceCustomConsoleNode()

class DeviceCustomConsoleNode(template.Node):
    def __init__(self):
        pass

    def render(self, context):
        try:
            return settings.PURPLE_ROBOT_DEVICE_CONSOLE(context)
        except AttributeError:
            pass
        
        return render_to_string('tag_pr_device_custom_console_unknown.html')

@register.tag(name="pr_group_table")
def tag_pr_group_table(parser, token):
    try:
        tag_name, group_id = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])

    return GroupTableNode(group_id)

class GroupTableNode(template.Node):
    def __init__(self, group_id):
        self.group_id = template.Variable(group_id)

    def render(self, context):
        group_id = self.group_id.resolve(context)
        
        context['device_group'] = PurpleRobotDeviceGroup.objects.get(group_id=group_id)
        context['device_group_devices'] = list(context['device_group'].devices.all())
        
        return render_to_string('tag_pr_group_table.html', context)

@register.tag(name="pr_timestamp_ago")
def tag_pr_timestamp_ago(parser, token):
    try:
        tag_name, timestamp = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])
        
    return TimestampAgoNode(timestamp)

class TimestampAgoNode(template.Node):
    def __init__(self, timestamp):
        self.timestamp = template.Variable(timestamp)

    def render(self, context):
        timestamp = self.timestamp.resolve(context)
        
        date_obj = datetime.datetime.fromtimestamp(int(timestamp) / 1000, pytz.utc)
        
        if date_obj == None:
            return 'None'
        
        now = timezone.now()
        
        diff = now - date_obj
        
        ago_str = 'Unknown'
        
        if diff.days > 0:
            ago_str = str(diff.days) + 'd'
        else:
            minutes = diff.seconds / 60
            
            if minutes >= 60:
                ago_str = str(minutes / 60) + 'h'
            else:
                ago_str = str(minutes) + 'm'
        
        context['ago'] = ago_str
        context['date'] = date_obj
        
        return render_to_string('tag_pr_date_ago.html', context)
        

@register.tag(name="pr_date_ago")
def tag_pr_date_ago(parser, token):
    try:
        tag_name, date_obj = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])

    return DateAgoNode(date_obj)

class DateAgoNode(template.Node):
    def __init__(self, date_obj):
        self.date_obj = template.Variable(date_obj)

    def render(self, context):
        date_obj = self.date_obj.resolve(context)
        
        if date_obj == None:
            return 'None'
        
        now = timezone.now()
        
        diff = now - date_obj
        
        ago_str = 'Unknown'
        
        if diff.days > 0:
            ago_str = str(diff.days) + 'd'
        else:
            minutes = diff.seconds / 60
            
            if minutes >= 60:
                ago_str = str(minutes / 60) + 'h'
            else:
                ago_str = str(minutes) + 'm'
        
        context['ago'] = ago_str
        context['date'] = date_obj
        
        return render_to_string('tag_pr_date_ago.html', context)
        

@register.tag(name="pr_frequency")
def tag_pr_frequency(parser, token):
    try:
        tag_name, frequency = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])

    return FrequencyNode(frequency)

class FrequencyNode(template.Node):
    def __init__(self, frequency):
        self.frequency = template.Variable(frequency)

    def render(self, context):
        frequency = self.frequency.resolve(context)
        
        if frequency == None:
            return 'None'
        elif frequency == 'Unknown':
            return frequency

        value = "{:10.3f}".format(frequency) + " Hz"
        tooltip = "{:10.3f}".format(frequency) + " samples per second"
        
        if frequency < 1.0:
            frequency *= 60
            
            if frequency > 1.0:
                tooltip = "{:10.3f}".format(frequency) + " samples per minute"
            else:
                frequency *= 60
            
                if frequency > 1.0:
                    tooltip = "{:10.3f}".format(frequency) + " samples per hour"
                else:
                    frequency *= 24
            
                    if frequency > 1.0:
                        tooltip = "{:10.3f}".format(frequency) + " samples per day"
                    else:
                        frequency *= 7
            
                        tooltip = "{:10.3f}".format(frequency) + " samples per week"

        context['value'] = value
        context['tooltip'] = tooltip
        
        return render_to_string('tag_pr_frequency.html', context)
#        
#        return render_to_string('tag_pr_date_ago.html', context)
        
        

@register.tag(name="pr_device_alerts")
def tag_pr_device_alerts(parser, token):
    try:
        tag_name, user_id = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError("%r tag requires a single argument" % token.contents.split()[0])

    return DeviceAlertsNode(user_id)

class DeviceAlertsNode(template.Node):
    def __init__(self, user_id):
        self.user_id = template.Variable(user_id)

    def render(self, context):
        user_id = self.user_id.resolve(context)
        
        alerts = PurpleRobotAlert.objects.filter(user_id=user_id, dismissed=None).order_by('-severity')
        
        tooltip = 'No alerts.'
        
        severity = 0
        
        if alerts.count() > 0:
            tooltip = ''
            
            for alert in alerts:
                if len(tooltip) > 0:
                    tooltip += '\n'
                
                tooltip += alert.message
                
                if alert.severity > severity:
                    severity = alert.severity
                    
        if severity > 1:
            context['class'] = 'text-danger'
        elif severity > 1:
            context['class'] = 'text-warning'
        else:
            context['class'] = ''

        context['value'] = alerts.count()
        context['tooltip'] = tooltip
        
        return render_to_string('tag_pr_device_alerts.html', context)
#        
#        return render_to_string('tag_pr_date_ago.html', context)
        
        

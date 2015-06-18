import datetime
import pytz

from django import template
from django.conf import settings
from django.template.defaultfilters import stringfilter
from django.template.loader import render_to_string
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDeviceGroup

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
        
        

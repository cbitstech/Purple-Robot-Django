from django.contrib import admin

from purple_robot_app.models import PurpleRobotConfiguration, PurpleRobotPayload, \
                                    PurpleRobotEvent, PurpleRobotReading, \
                                    PurpleRobotReport, PurpleRobotTest, \
                                    PurpleRobotExportJob, PurpleRobotDeviceGroup, \
                                    PurpleRobotDevice, PurpleRobotAlert

class PurpleRobotConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'added')
    list_filter = ['added',]
    search_fields = ['name', 'slug', 'contents']

admin.site.register(PurpleRobotConfiguration, PurpleRobotConfigurationAdmin)

class PurpleRobotPayloadAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'added', 'process_tags',)
    list_filter = ['added', 'user_id']
    search_fields = ['payload', 'errors', 'process_tags']

admin.site.register(PurpleRobotPayload, PurpleRobotPayloadAdmin)

class PurpleRobotEventAdmin(admin.ModelAdmin):
    list_display = ('event', 'event_name', 'logged', 'user_id')
    list_filter = ['event', 'logged', 'user_id']
    search_fields = ['event', 'user_id', 'payload']

admin.site.register(PurpleRobotEvent, PurpleRobotEventAdmin)

class PurpleRobotReadingAdmin(admin.ModelAdmin):
    list_display = ('probe_name', 'user_id', 'guid', 'logged', 'size', 'attachment',)
    list_filter = ['probe', 'user_id', 'logged']
    search_fields = ['probe', 'user_id', 'payload']

admin.site.register(PurpleRobotReading, PurpleRobotReadingAdmin)

class PurpleRobotReportAdmin(admin.ModelAdmin):
    list_display = ('probe', 'user_id', 'generated', 'mime_type')
    list_filter = ['probe', 'user_id', 'generated', 'mime_type']

admin.site.register(PurpleRobotReport, PurpleRobotReportAdmin)

class PurpleRobotTestAdmin(admin.ModelAdmin):
    list_display = ('probe', 'user_id', 'slug', 'frequency', 'last_updated', 'active')
    list_filter = ['probe', 'user_id', 'last_updated', 'active']
    
admin.site.register(PurpleRobotTest, PurpleRobotTestAdmin)

class PurpleRobotExportJobAdmin(admin.ModelAdmin):
    list_display = ('start_date', 'end_date', 'destination', 'state')
    list_filter = ['start_date', 'end_date', 'state']
    
admin.site.register(PurpleRobotExportJob, PurpleRobotExportJobAdmin)

class PurpleRobotDeviceGroupAdmin(admin.ModelAdmin):
    list_display = ('group_id', 'configuration',)
    
admin.site.register(PurpleRobotDeviceGroup, PurpleRobotDeviceGroupAdmin)

class PurpleRobotDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'name', 'configuration', 'config_last_fetched', 'config_last_user_agent', 'hash_key')
    list_filter = ['device_group', 'configuration']
    
admin.site.register(PurpleRobotDevice, PurpleRobotDeviceAdmin)

class PurpleRobotAlertAdmin(admin.ModelAdmin):
    list_display = ('message', 'severity', 'tags', 'action_url', 'probe', 'user_id', 'generated', 'dismissed', 'manually_dismissed')
    list_filter = ['severity', 'user_id', 'generated', 'dismissed', 'manually_dismissed']
    search_fields = ['message', 'tags']
    
admin.site.register(PurpleRobotAlert, PurpleRobotAlertAdmin)

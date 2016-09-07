# pylint: disable=line-too-long, unused-argument

from django.contrib import admin

from .models import PurpleRobotConfiguration, PurpleRobotPayload, \
                                    PurpleRobotEvent, PurpleRobotReading, \
                                    PurpleRobotReport, PurpleRobotTest, \
                                    PurpleRobotExportJob, PurpleRobotDeviceGroup, \
                                    PurpleRobotDevice, PurpleRobotAlert, \
                                    PurpleRobotDeviceNote


class PurpleRobotConfigurationAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'added')
    list_filter = ['added', ]
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
    list_display = ('name', 'group_id', 'configuration',)

admin.site.register(PurpleRobotDeviceGroup, PurpleRobotDeviceGroupAdmin)


def clear_performance_metadata(modeladmin, request, queryset):
    for device in queryset:
        device.performance_metadata = '{}'
        device.save()

clear_performance_metadata.description = 'Reset cached metadata'


def mute_alerts(modeladmin, request, queryset):
    for device in queryset:
        device.mute_alerts = True
        device.save()

mute_alerts.description = 'Mute alerts'


def unmute_alerts(modeladmin, request, queryset):
    for device in queryset:
        device.mute_alerts = False
        device.save()

unmute_alerts.description = 'Unmute alerts'


def mark_testing(modeladmin, request, queryset):
    for device in queryset:
        device.test_device = True
        device.save()

mark_testing.description = 'Mark as test device'


def unmark_testing(modeladmin, request, queryset):
    for device in queryset:
        device.test_device = False
        device.save()

unmark_testing.description = 'Mark as regular device'


class PurpleRobotDeviceAdmin(admin.ModelAdmin):
    list_display = ('device_id', 'name', 'device_group', 'configuration', 'config_last_fetched', 'config_last_user_agent', 'hash_key', 'mute_alerts', 'test_device', )  # 'earliest_reading_date', 'latest_reading_date',)
    list_filter = ['device_group', 'test_device', 'configuration', 'mute_alerts']
    search_fields = ['device_id', 'name', 'hash_key']

    actions = [clear_performance_metadata, mute_alerts, unmute_alerts, mark_testing, unmark_testing]

admin.site.register(PurpleRobotDevice, PurpleRobotDeviceAdmin)


class PurpleRobotDeviceNoteAdmin(admin.ModelAdmin):
    list_display = ('device', 'added',)
    list_filter = ['added']
    search_fields = ['note']

admin.site.register(PurpleRobotDeviceNote, PurpleRobotDeviceNoteAdmin)


class PurpleRobotAlertAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'probe', 'tags', 'message', 'severity', 'generated', 'dismissed', 'manually_dismissed',)

    list_filter = ['tags', 'probe', 'severity', 'generated', 'dismissed', 'manually_dismissed']
    search_fields = ['tags', 'message']

admin.site.register(PurpleRobotAlert, PurpleRobotAlertAdmin)

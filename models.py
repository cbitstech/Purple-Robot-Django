import string
from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

class PurpleRobotConfiguration(models.Model):
    name = models.CharField(max_length=1024)
    slug = models.SlugField(max_length=1024, unique=True)
    contents = models.TextField(max_length=1048576)
    added = models.DateTimeField()

class PurpleRobotPayload(models.Model):
    added = models.DateTimeField(auto_now_add=True)
    payload = models.TextField(max_length=8388608)
    process_tags = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.CharField(max_length=1024)

    errors = models.TextField(max_length=65536, null=True, blank=True)

class PurpleRobotEvent(models.Model):
    event = models.CharField(max_length=1024)
    logged = models.DateTimeField()
    user_id = models.CharField(max_length=1024)

    payload = models.TextField(max_length=(1024 * 1024 * 8), null=True, blank=True)

class PurpleRobotReading(models.Model):
    probe = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.CharField(max_length=1024)
    payload = models.TextField(max_length=8388608)
    logged = models.DateTimeField()

class PurpleRobotReport(models.Model):
    probe = models.CharField(max_length=1024, null=True, blank=True)
    user_id = models.CharField(max_length=1024)
    generated = models.DateTimeField()
    mime_type = models.CharField(max_length=1024)
    report_file = models.FileField(blank=True, upload_to='report_files')

    def __unicode__(self):
        return string.split(self.probe, '.')[-1]

@receiver(pre_delete, sender=PurpleRobotReport)
def purplerobotreport_delete(sender, instance, **kwargs):
    instance.report_file.delete(False)

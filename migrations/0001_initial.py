# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='PurpleRobotAlert',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('severity', models.IntegerField(default=0)),
                ('message', models.CharField(max_length=2048)),
                ('tags', models.CharField(max_length=2048, null=True, blank=True)),
                ('action_url', models.URLField(max_length=1024, null=True, blank=True)),
                ('probe', models.CharField(max_length=1024, null=True, blank=True)),
                ('user_id', models.CharField(max_length=1024, null=True, blank=True)),
                ('generated', models.DateTimeField()),
                ('dismissed', models.DateTimeField(null=True, blank=True)),
                ('manually_dismissed', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotConfiguration',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('slug', models.SlugField(unique=True, max_length=1024)),
                ('contents', models.TextField(max_length=1048576)),
                ('added', models.DateTimeField()),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotDevice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('device_id', models.CharField(unique=True, max_length=256, db_index=True)),
                ('description', models.TextField(max_length=1048576, null=True, blank=True)),
                ('config_last_fetched', models.DateTimeField(null=True, blank=True)),
                ('config_last_user_agent', models.CharField(max_length=1024, null=True, blank=True)),
                ('hash_key', models.CharField(max_length=128, null=True, blank=True)),
                ('first_reading_timestamp', models.BigIntegerField(default=0)),
                ('last_reading_timestamp', models.BigIntegerField(default=0)),
                ('mute_alerts', models.BooleanField(default=False)),
                ('test_device', models.BooleanField(default=False)),
                ('performance_metadata', models.TextField(default=b'{}', max_length=1048576)),
                ('configuration', models.ForeignKey(related_name='devices', blank=True, to='purple_robot.PurpleRobotConfiguration', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotDeviceGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=1024)),
                ('group_id', models.SlugField(unique=True, max_length=256)),
                ('description', models.TextField(max_length=1048576, null=True, blank=True)),
                ('configuration', models.ForeignKey(related_name='groups', blank=True, to='purple_robot.PurpleRobotConfiguration', null=True)),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotDeviceNote',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('note', models.TextField(max_length=1024)),
                ('added', models.DateTimeField()),
                ('device', models.ForeignKey(related_name='notes', to='purple_robot.PurpleRobotDevice')),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotEvent',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('event', models.CharField(max_length=1024)),
                ('name', models.CharField(db_index=True, max_length=1024, null=True, blank=True)),
                ('logged', models.DateTimeField(db_index=True)),
                ('user_id', models.CharField(max_length=1024, db_index=True)),
                ('payload', models.TextField(max_length=8388608, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotExportJob',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('probes', models.TextField(max_length=8196, null=True, blank=True)),
                ('users', models.TextField(max_length=8196, null=True, blank=True)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('export_file', models.FileField(upload_to=b'export_files', blank=True)),
                ('destination', models.EmailField(max_length=254, null=True, blank=True)),
                ('state', models.CharField(default=b'pending', max_length=512, choices=[(b'pending', b'Pending'), (b'processing', b'Processing'), (b'finished', b'Finished'), (b'error', b'Error')])),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotPayload',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('added', models.DateTimeField(auto_now_add=True)),
                ('payload', models.TextField(max_length=8388608)),
                ('process_tags', models.CharField(db_index=True, max_length=1024, null=True, blank=True)),
                ('user_id', models.CharField(max_length=1024, db_index=True)),
                ('errors', models.TextField(max_length=65536, null=True, blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotReading',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('probe', models.CharField(db_index=True, max_length=1024, null=True, blank=True)),
                ('user_id', models.CharField(max_length=1024, db_index=True)),
                ('payload', models.TextField(max_length=8388608)),
                ('logged', models.DateTimeField(db_index=True)),
                ('guid', models.CharField(db_index=True, max_length=1024, null=True, blank=True)),
                ('size', models.IntegerField(default=0, db_index=True)),
                ('attachment', models.FileField(null=True, upload_to=b'reading_attachments', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotReport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('probe', models.CharField(max_length=1024, null=True, blank=True)),
                ('user_id', models.CharField(max_length=1024)),
                ('generated', models.DateTimeField()),
                ('mime_type', models.CharField(max_length=1024)),
                ('report_file', models.FileField(upload_to=b'report_files', blank=True)),
            ],
        ),
        migrations.CreateModel(
            name='PurpleRobotTest',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=False)),
                ('slug', models.SlugField(unique=True)),
                ('probe', models.CharField(max_length=1024, null=True, blank=True)),
                ('user_id', models.CharField(max_length=1024)),
                ('frequency', models.FloatField(default=1.0)),
                ('report', models.TextField(default=b'{}')),
                ('last_updated', models.DateTimeField()),
            ],
        ),
        migrations.AlterIndexTogether(
            name='purplerobotreading',
            index_together=set([('probe', 'logged', 'user_id'), ('logged', 'user_id'), ('probe', 'user_id')]),
        ),
        migrations.AddField(
            model_name='purplerobotdevice',
            name='device_group',
            field=models.ForeignKey(related_name='devices', blank=True, to='purple_robot.PurpleRobotDeviceGroup', null=True),
        ),
    ]

# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'PurpleRobotDeviceGroup'
        db.create_table(u'purple_robot_app_purplerobotdevicegroup', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group_id', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=256)),
        ))
        db.send_create_signal(u'purple_robot_app', ['PurpleRobotDeviceGroup'])

        # Adding model 'PurpleRobotDevice'
        db.create_table(u'purple_robot_app_purplerobotdevice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('device_id', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=256)),
            ('device_group', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='devices', null=True, to=orm['purple_robot_app.PurpleRobotDeviceGroup'])),
            ('description', self.gf('django.db.models.fields.TextField')(max_length=1048576, null=True, blank=True)),
            ('configuration', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='devices', null=True, to=orm['purple_robot_app.PurpleRobotConfiguration'])),
            ('config_last_fetched', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('config_last_user_agent', self.gf('django.db.models.fields.CharField')(max_length=1024, null=True, blank=True)),
            ('hash_key', self.gf('django.db.models.fields.CharField')(max_length=128, null=True, blank=True)),
        ))
        db.send_create_signal(u'purple_robot_app', ['PurpleRobotDevice'])


    def backwards(self, orm):
        # Deleting model 'PurpleRobotDeviceGroup'
        db.delete_table(u'purple_robot_app_purplerobotdevicegroup')

        # Deleting model 'PurpleRobotDevice'
        db.delete_table(u'purple_robot_app_purplerobotdevice')


    models = {
        u'purple_robot_app.purplerobotconfiguration': {
            'Meta': {'object_name': 'PurpleRobotConfiguration'},
            'added': ('django.db.models.fields.DateTimeField', [], {}),
            'contents': ('django.db.models.fields.TextField', [], {'max_length': '1048576'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '1024'})
        },
        u'purple_robot_app.purplerobotdevice': {
            'Meta': {'object_name': 'PurpleRobotDevice'},
            'config_last_fetched': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'config_last_user_agent': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'configuration': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'devices'", 'null': 'True', 'to': u"orm['purple_robot_app.PurpleRobotConfiguration']"}),
            'description': ('django.db.models.fields.TextField', [], {'max_length': '1048576', 'null': 'True', 'blank': 'True'}),
            'device_group': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'devices'", 'null': 'True', 'to': u"orm['purple_robot_app.PurpleRobotDeviceGroup']"}),
            'device_id': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '256'}),
            'hash_key': ('django.db.models.fields.CharField', [], {'max_length': '128', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'purple_robot_app.purplerobotdevicegroup': {
            'Meta': {'object_name': 'PurpleRobotDeviceGroup'},
            'group_id': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '256'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'purple_robot_app.purplerobotevent': {
            'Meta': {'object_name': 'PurpleRobotEvent'},
            'event': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logged': ('django.db.models.fields.DateTimeField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {'max_length': '8388608', 'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'db_index': 'True'})
        },
        u'purple_robot_app.purplerobotexportjob': {
            'Meta': {'object_name': 'PurpleRobotExportJob'},
            'destination': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'end_date': ('django.db.models.fields.DateField', [], {}),
            'export_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'probes': ('django.db.models.fields.TextField', [], {'max_length': '8196', 'null': 'True', 'blank': 'True'}),
            'start_date': ('django.db.models.fields.DateField', [], {}),
            'state': ('django.db.models.fields.CharField', [], {'default': "'pending'", 'max_length': '512'}),
            'users': ('django.db.models.fields.TextField', [], {'max_length': '8196', 'null': 'True', 'blank': 'True'})
        },
        u'purple_robot_app.purplerobotpayload': {
            'Meta': {'object_name': 'PurpleRobotPayload'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'errors': ('django.db.models.fields.TextField', [], {'max_length': '65536', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {'max_length': '8388608'}),
            'process_tags': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'db_index': 'True'})
        },
        u'purple_robot_app.purplerobotreading': {
            'Meta': {'object_name': 'PurpleRobotReading'},
            'guid': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logged': ('django.db.models.fields.DateTimeField', [], {}),
            'payload': ('django.db.models.fields.TextField', [], {'max_length': '8388608'}),
            'probe': ('django.db.models.fields.CharField', [], {'db_index': 'True', 'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'db_index': 'True'})
        },
        u'purple_robot_app.purplerobotreport': {
            'Meta': {'object_name': 'PurpleRobotReport'},
            'generated': ('django.db.models.fields.DateTimeField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mime_type': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'probe': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'report_file': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'purple_robot_app.purplerobottest': {
            'Meta': {'object_name': 'PurpleRobotTest'},
            'active': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'frequency': ('django.db.models.fields.FloatField', [], {'default': '1.0'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_updated': ('django.db.models.fields.DateTimeField', [], {}),
            'probe': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'report': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        }
    }

    complete_apps = ['purple_robot_app']
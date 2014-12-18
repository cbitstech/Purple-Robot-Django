# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Deleting field 'PurpleRobotTest.timestamps'
        db.delete_column(u'purple_robot_app_purplerobottest', 'timestamps')

        # Adding field 'PurpleRobotTest.report'
        db.add_column(u'purple_robot_app_purplerobottest', 'report',
                      self.gf('django.db.models.fields.TextField')(default='{}'),
                      keep_default=False)

        # Adding field 'PurpleRobotTest.last_reading_id'
        db.add_column(u'purple_robot_app_purplerobottest', 'last_reading_id',
                      self.gf('django.db.models.fields.BigIntegerField')(default=0),
                      keep_default=False)


    def backwards(self, orm):

        # User chose to not deal with backwards NULL issues for 'PurpleRobotTest.timestamps'
        raise RuntimeError("Cannot reverse this migration. 'PurpleRobotTest.timestamps' and its values cannot be restored.")
        
        # The following code is provided here to aid in writing a correct migration        # Adding field 'PurpleRobotTest.timestamps'
        db.add_column(u'purple_robot_app_purplerobottest', 'timestamps',
                      self.gf('django.db.models.fields.TextField')(),
                      keep_default=False)

        # Deleting field 'PurpleRobotTest.report'
        db.delete_column(u'purple_robot_app_purplerobottest', 'report')

        # Deleting field 'PurpleRobotTest.last_reading_id'
        db.delete_column(u'purple_robot_app_purplerobottest', 'last_reading_id')


    models = {
        u'purple_robot_app.purplerobotconfiguration': {
            'Meta': {'object_name': 'PurpleRobotConfiguration'},
            'added': ('django.db.models.fields.DateTimeField', [], {}),
            'contents': ('django.db.models.fields.TextField', [], {'max_length': '1048576'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '1024'})
        },
        u'purple_robot_app.purplerobotevent': {
            'Meta': {'object_name': 'PurpleRobotEvent'},
            'event': ('django.db.models.fields.CharField', [], {'max_length': '1024'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logged': ('django.db.models.fields.DateTimeField', [], {}),
            'payload': ('django.db.models.fields.TextField', [], {'max_length': '8388608', 'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'purple_robot_app.purplerobotpayload': {
            'Meta': {'object_name': 'PurpleRobotPayload'},
            'added': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'errors': ('django.db.models.fields.TextField', [], {'max_length': '65536', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'payload': ('django.db.models.fields.TextField', [], {'max_length': '8388608'}),
            'process_tags': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        },
        u'purple_robot_app.purplerobotreading': {
            'Meta': {'object_name': 'PurpleRobotReading'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'logged': ('django.db.models.fields.DateTimeField', [], {}),
            'payload': ('django.db.models.fields.TextField', [], {'max_length': '8388608'}),
            'probe': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
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
            'last_reading_id': ('django.db.models.fields.BigIntegerField', [], {'default': '0'}),
            'probe': ('django.db.models.fields.CharField', [], {'max_length': '1024', 'null': 'True', 'blank': 'True'}),
            'report': ('django.db.models.fields.TextField', [], {'default': "'{}'"}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'user_id': ('django.db.models.fields.CharField', [], {'max_length': '1024'})
        }
    }

    complete_apps = ['purple_robot_app']
# pylint: disable=line-too-long, invalid-name

from django.conf.urls import patterns, url

from purple_robot_app.views import ingest_payload_print, log_event, pr_home, pr_by_probe, \
                                   pr_by_user, test_report, test_details_json, tests_by_user, \
                                   create_export_job, fetch_export_file, tests_all, ingest_payload, pr_config, \
                                   pr_device, pr_add_group, pr_add_device, pr_configurations, pr_configuration, \
                                   pr_device_probe, pr_add_note, pr_remove_device, pr_move_device, pr_status, \
                                   pr_users

urlpatterns = patterns('',
                       url(r'^config$', pr_config, name='pr_config'),
                       url(r'^configurations$', pr_configurations, name='pr_configurations'),
                       url(r'^configuration/(?P<config_id>.+)$', pr_configuration, name='pr_configuration'),
                       url(r'^print$', ingest_payload_print, name='ingest_payload_print'),
                       url(r'^log$', log_event, name='log_event'),
                       url(r'^home$', pr_home, name='pr_home'),
                       url(r'^add_group$', pr_add_group, name='pr_add_group'),
                       url(r'^move_device$', pr_move_device, name='pr_move_device'),
                       url(r'^group/(?P<group_id>.+)/remove_device/(?P<device_id>.+)$', pr_remove_device, name='pr_remove_device'),
                       url(r'^group/(?P<group_id>.+)/add_device$', pr_add_device, name='pr_add_device'),
                       url(r'^device/(?P<device_id>.+)/(?P<probe_name>.+)$', pr_device_probe, name='pr_device_probe'),
                       url(r'^device/(?P<device_id>.+)$', pr_device, name='pr_device'),
                       url(r'^probes$', pr_by_probe, name='pr_by_probe'),
                       url(r'^user$', pr_by_user, name='pr_by_user'),
                       url(r'^status$', pr_status, name='pr_status'),
                       url(r'^test/(?P<slug>.+)$', test_report, name='test_report'),
                       url(r'^tests/(?P<slug>.+)/detail.json$', test_details_json, name='test_details_json'),
                       url(r'^tests/(?P<user_id>.+)$', tests_by_user, name='tests_by_user'),
                       url(r'^export$', create_export_job, name='create_export_job'),
                       url(r'^export_files/(?P<job_pk>.+)$', fetch_export_file, name='fetch_export_file'),
                       url(r'^tests/$', tests_all, name='tests_all'),
                       url(r'^add_note.json$', pr_add_note, name='pr_add_note'),
                       url(r'^users$', pr_users, name='pr_users'),
                       url(r'^$', ingest_payload, name='ingest_payload'), )

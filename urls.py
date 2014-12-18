from django.conf.urls import patterns, include, url
from django.contrib.sitemaps import *
from django.views.generic import RedirectView
from django.views.decorators.cache import cache_page

from views import *

urlpatterns = patterns('',
#    url(r'^(?P<config>.+).scm$', pr_configuration, name='pr_configuration'),
    url(r'^print$', ingest_payload_print, name='ingest_payload_print'),
    url(r'^log$', log_event, name='log_event'),
    url(r'^home$', pr_home, name='pr_home'),
    url(r'^probes$', pr_by_probe, name='pr_by_probe'),
    url(r'^user$', pr_by_user, name='pr_by_user'),
    url(r'^test/(?P<slug>.+)$', test_report, name='test_report'),
    url(r'^tests/(?P<user_id>.+)$', tests_by_user, name='tests_by_user'),
#    url(r'^test$', test_payload, name='test_payload'),
    url(r'^$', ingest_payload, name='ingest_payload'),
)

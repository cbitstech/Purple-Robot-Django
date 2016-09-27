# pylint: disable=line-too-long, no-member

import datetime
import gzip
import json
import tempfile

from django.core.files import File
from django.core.mail import send_mail
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.template import Context
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.crypto import get_random_string

from django.conf import settings
from ...models import PurpleRobotExportJob, PurpleRobotReading


class Command(BaseCommand):
    def handle(self, *args, **options):
        processing = PurpleRobotExportJob.objects.filter(state='processing')
        pending = PurpleRobotExportJob.objects.filter(state='pending')
        
        now = timezone.now()

        if processing.count() > 0:
            pass  # Do nothing - already compiling a job...
        elif pending.count() < 1:
            pass  # No work to do...
        else:
            job = pending.order_by('pk')[0]

            job.state = 'processing'
            job.save()

            hashes = job.users.strip().split()
            probes = job.probes.strip().split()

            start = datetime.datetime(job.start_date.year, job.start_date.month, job.start_date.day, 0, 0, 0, 0, tzinfo=now.tzinfo)
            end = datetime.datetime(job.end_date.year, job.end_date.month, job.end_date.day, 23, 59, 59, 999999, tzinfo=now.tzinfo)

            q_probes = None

            temp_file = tempfile.TemporaryFile()

            for probe in probes:
                if q_probes is None:
                    q_probes = Q(probe=probe)
                else:
                    q_probes = (q_probes | Q(probe=probe))

            gzf = gzip.GzipFile(mode='wb', fileobj=temp_file)
            gzf.write('User ID\tProbe\tLogged\tStart\tEnd\tDuration\tPayload\n')

            for user_hash in hashes:
                readings = None

                if q_probes is not None:
                    readings = PurpleRobotReading.objects.filter(q_probes, user_id=user_hash, logged__gte=start, logged__lte=end).order_by('logged')
                else:
                    readings = PurpleRobotReading.objects.filter(user_id=user_hash, logged__gte=start, logged__lte=end).order_by('logged')

                count = readings.count()

                for i in range(0, (count / 500) + 1):
                    page_start = i * 500
                    page_end = page_start + 499

                    for reading in readings[page_start:page_end]:
                        payload = json.loads(reading.payload)
                        
                        if 'FEATURE_VALUE' in payload and 'start' in payload['FEATURE_VALUE'] and 'end' in payload['FEATURE_VALUE'] and 'duration' in payload['FEATURE_VALUE']:
                            range_start = payload['FEATURE_VALUE']['start']
                            range_end = payload['FEATURE_VALUE']['end']
                            duration = payload['FEATURE_VALUE']['duration']
                            
                            gzf.write(user_hash + '\t' + reading.probe + '\t' + str(reading.logged) + '\t' + str(range_start) + '\t' + str(range_end) + '\t' + str(duration) + '\t' + json.dumps(payload) + '\n')
                        
                        
                        else:
                            gzf.write(user_hash + '\t' + reading.probe + '\t' + str(reading.logged) + '\t\t\t\t' + json.dumps(payload) + '\n')

            gzf.flush()
            gzf.close()

            temp_file.seek(0)

            job.export_file.save('export_' + job.start_date.isoformat() + '_' +
                                 job.end_date.isoformat() + '_' +
                                 get_random_string(16).lower() + '.txt.gz',
                                 File(temp_file))

            job.state = 'finished'
            job.save()

            if job.destination is not None and job.destination != '':
                context = Context()
                context['job'] = job
                context['prefix'] = settings.URL_PREFIX

                message = render_to_string('export_email.txt', context)

                send_mail('Your Purple Robot data is available', message, 'Purple Robot <' + settings.ADMINS[0][1] + '>', [job.destination], fail_silently=False)

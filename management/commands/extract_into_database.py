# pylint: disable=line-too-long, no-member

import datetime
import json
import importlib
import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.utils.text import slugify

from ...models import PurpleRobotPayload
from ...performance import append_performance_sample

EXTRACTORS = {}


def my_slugify(str_obj):
    return slugify(str_obj.replace('.', ' ')).replace('-', '_')


def touch(fname, mode=0o666):
    flags = os.O_CREAT | os.O_APPEND

    if os.fdopen(os.open(fname, flags, mode)) is not None:
        os.utime(fname, None)


class Command(BaseCommand):
    def handle(self, *args, **options):
        try:
            settings.PURPLE_ROBOT_FLAT_MIRROR
        except AttributeError:
            return

        if os.access('/tmp/extract_into_database.lock', os.R_OK):
            timestamp = os.path.getmtime('/tmp/extract_into_database.lock')
            created = datetime.datetime.fromtimestamp(timestamp)

            if (datetime.datetime.now() - created).total_seconds() > 60 * 60 * 8:
                print 'extract_into_database: Stale lock - removing...'
                os.remove('/tmp/extract_into_database.lock')
            else:
                return

        touch('/tmp/extract_into_database.lock')

        tag = 'extracted_into_database'
        skip_tag = 'extracted_into_database_skip'

        start = timezone.now()
        payloads = list(PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).order_by('-added')[:50])
        end = timezone.now()

        query_time = (end - start).total_seconds()

        extractor_times = {}
        extractor_counts = {}

        local_db = 0.0
        remote_db = 0.0
        local_app = 0.0

        while len(payloads) > 0:
            touch('/tmp/extract_into_database.lock')

            extractor_times = {}
            extractor_counts = {}

            local_db = query_time
            remote_db = 0.0
            local_app = 0.0

            start = timezone.now()

            for payload in payloads:
                cpu_start = datetime.datetime.now()

                items = json.loads(payload.payload)

                has_all_extractors = True
                missing_extractors = []

                for item in items:
                    if 'PROBE' in item and 'GUID' in item:
                        probe_name = my_slugify(item['PROBE']).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')

                        found = False

                        if (probe_name in EXTRACTORS) is True:
                            if EXTRACTORS[probe_name] is not None:
                                found = True
                            else:
                                found = False
                        else:
                            EXTRACTORS[probe_name] = None

                            for app in settings.INSTALLED_APPS:
                                try:
                                    probe = importlib.import_module(app + '.management.commands.extractors.' + probe_name)

                                    EXTRACTORS[probe_name] = probe

                                    found = True
                                except ImportError:
                                    pass

                        if found is False:
                            has_all_extractors = False

                            if (probe_name in missing_extractors) == False:
                                missing_extractors.append(probe_name)
                    else:
                        has_all_extractors = False
                        missing_extractors.append('Unknown Probe')

                if has_all_extractors:
                    for item in items:
                        if 'PROBE' in item and 'GUID' in item:
                            probe_name = my_slugify(item['PROBE']).replace('edu_northwestern_cbits_purple_robot_manager_probes_', '')

                            probe = EXTRACTORS[probe_name]

                            write_start = datetime.datetime.now()
                            local_app += (write_start - cpu_start).total_seconds()

                            exists = True
                            
                            disable_checks = False
                            
                            try:
                                disable_checks = settings.PURPLE_ROBOT_DISABLE_DATA_CHECKS
                            except:
                                pass

                            if disable_checks:
                                exists = False
                            else:
                                exists = probe.exists(settings.PURPLE_ROBOT_FLAT_MIRROR, payload.user_id, item)

                            cpu_start = datetime.datetime.now()
                            remote_db += (cpu_start - write_start).total_seconds()

                            if EXTRACTORS[probe_name] is not None and exists is False:
                                write_start = datetime.datetime.now()
                                local_app += (write_start - cpu_start).total_seconds()

                                EXTRACTORS[probe_name].insert(settings.PURPLE_ROBOT_FLAT_MIRROR, payload.user_id, item, check_exists=(disable_checks is False))

                                cpu_start = datetime.datetime.now()
                                remote_db += (cpu_start - write_start).total_seconds()

                                duration = 0.0

                                if probe_name in extractor_times:
                                    duration = extractor_times[probe_name]

                                duration += (cpu_start - write_start).total_seconds()

                                extractor_times[probe_name] = duration

                                count = 0.0

                                if probe_name in extractor_counts:
                                    count = extractor_counts[probe_name]

                                count += 1

                                extractor_counts[probe_name] = count

                    tags = payload.process_tags

                    if tags is None or tags.find(tag) == -1:
                        if tags is None or len(tags) == 0:
                            tags = tag
                        else:
                            tags += ' ' + tag

                        payload.process_tags = tags

                        read_start = datetime.datetime.now()
                        local_app += (read_start - cpu_start).total_seconds()

                        payload.save()

                        cpu_start = datetime.datetime.now()
                        local_db += (cpu_start - read_start).total_seconds()
                else:
                    tags = payload.process_tags

                    if tags is None or tags.find(skip_tag) == -1:
                        if tags is None or len(tags) == 0:
                            tags = skip_tag
                        else:
                            tags += ' ' + skip_tag

                        payload.process_tags = tags

                        read_start = datetime.datetime.now()
                        local_app += (read_start - cpu_start).total_seconds()

                        payload.save()

                        cpu_start = datetime.datetime.now()
                        local_db += (cpu_start - read_start).total_seconds()

                if len(missing_extractors) > 0:
                    print 'MISSING EXTRACTORS: ' + str(missing_extractors)

            end = timezone.now()

            perf_values = {}
            perf_values['num_mirrored'] = len(payloads)
            perf_values['query_time'] = query_time
            perf_values['local_db'] = local_db
            perf_values['remote_db'] = remote_db
            perf_values['local_app'] = local_app
            perf_values['extraction_time'] = (end - start).total_seconds()

            append_performance_sample('system', 'reading_mirror_performance', end, perf_values)

            start = timezone.now()
            payloads = list(PurpleRobotPayload.objects.exclude(process_tags__contains=tag).exclude(process_tags__contains=skip_tag).order_by('-added')[:50])
            end = timezone.now()
            query_time = (end - start).total_seconds()

        os.remove('/tmp/extract_into_database.lock')

# pylint: disable=line-too-long, no-member, unused-argument, bare-except

import arrow
import datetime
import hashlib
import json
import numpy
import pytz
import sys

from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.core.context_processors import csrf
from django.core.urlresolvers import reverse
from django.http import HttpResponse, UnreadablePostError
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt

from purple_robot_app.forms import ExportJobForm
from purple_robot_app.models import PurpleRobotPayload, PurpleRobotTest, PurpleRobotEvent, \
                                    PurpleRobotReport, PurpleRobotExportJob, PurpleRobotReading, \
                                    PurpleRobotConfiguration, PurpleRobotDevice, PurpleRobotDeviceGroup, \
                                    PurpleRobotDeviceNote

from purple_robot_app.performance import fetch_performance_samples, fetch_performance_users


@never_cache
def pr_config(request):
    config = None

    try:
        device_id = request.GET['user_id']

        device = PurpleRobotDevice.objects.get(device_id=device_id)

        if device.configuration is not None:
            config = device.configuration
        elif device.device_group.configuration is not None:
            config = device.device_group.configuration

        device.config_last_fetched = datetime.datetime.now()

        try:
            device.config_last_user_agent = request.META['HTTP_USER_AGENT']
        except KeyError:
            device.config_last_user_agent = 'Unknown'

        device.save()
    except:
        pass

    if config is None:
        config = get_object_or_404(PurpleRobotConfiguration, slug='default')

    content_type = 'application/json'

    if config.contents.strip().lower().startswith('(begin'):
        content_type = 'text/x-scheme'

    return HttpResponse(config.contents, content_type=content_type)


@csrf_exempt
@never_cache
def ingest_payload(request):
    result = {}
    result['Status'] = 'error'
    result['Payload'] = "{}"

    if request.method == 'POST':
        try:
            json_str = request.POST['json']

            json_obj = json.loads(json_str)

            payload_str = json_obj['Payload']

            md5_hash = hashlib.md5()
            md5_hash.update((json_obj['UserHash'] + json_obj['Operation'] + json_obj['Payload']).encode('utf-8'))

            checksum_str = md5_hash.hexdigest()

            result = {}
            result['Status'] = 'error'
            result['Payload'] = "{}"

            if checksum_str == json_obj['Checksum']:
                result['Status'] = 'success'

                try:
                    payload_json = json.loads(payload_str)

                    payload = PurpleRobotPayload(payload=json.dumps(payload_json, indent=2, ensure_ascii=False), user_id=json_obj['UserHash'])
                    payload.save()

                    md5_hash = hashlib.md5()
                    md5_hash.update(result['Status'] + result['Payload'])

                    result['Checksum'] = md5_hash.hexdigest()

                    if 'media_url' in payload_str:
                        payload.ingest_readings()
                        for key, value in request.FILES.iteritems():
                            reading = PurpleRobotReading.objects.filter(guid=key).first()

                            if reading is not None:
                                reading.attachment.save(value.name, value)

                                reading.size = len(reading.payload)
                                reading.size += reading.attachment.size

                                reading.save()
                except ValueError:
                    result['Status'] = 'error'
                    result['Error'] = 'Unable to parse payload.'
            else:
                result['Error'] = 'Source checksum ' + json_obj['Checksum'] + ' doesn\'t match destination checksum ' + checksum_str + '.'
        except UnreadablePostError, error:
            result['Error'] = str(error)
    else:
        result['Error'] = 'GET requests not supported.'

    return HttpResponse(json.dumps(result), content_type='application/json')


@csrf_exempt
@never_cache
def ingest_payload_print(request):
    result = {}
    result['Status'] = 'error'
    result['Payload'] = "{}"

    try:
        json_str = request.POST['json']

        json_obj = json.loads(json_str)

        md5_hash = hashlib.md5()
        md5_hash.update((json_obj['UserHash'] + json_obj['Operation'] + json_obj['Payload']).encode('utf-8'))

        checksum_str = md5_hash.hexdigest()

        result = {}
        result['Status'] = 'error'
        result['Payload'] = "{}"

        if checksum_str == json_obj['Checksum']:
            result['Status'] = 'success'

            md5_hash = hashlib.md5()
            md5_hash.update(result['Status'] + result['Payload'])

            result['Checksum'] = md5_hash.hexdigest()
        else:
            result['Error'] = 'Source checksum ' + json_obj['Checksum'] + ' doesn\'t match destination checksum ' + checksum_str + '.'
    except:
        error = sys.exc_info()[0]
        result['Error'] = str(error)

    return HttpResponse(json.dumps(result), content_type='application/json')


@csrf_exempt
@never_cache
def log_event(request):
    try:
        here_tz = pytz.timezone(settings.TIME_ZONE)
        payload = json.loads(request.POST['json'])

        logged = here_tz.localize(datetime.datetime.fromtimestamp(int(payload['timestamp'])))

        try:
            if len(payload['user_id'].strip()) == 0:
                payload['user_id'] = '-'
        except KeyError:
            payload['user_id'] = '-'

        event = PurpleRobotEvent(payload=json.dumps(payload, indent=2))
        event.logged = logged
        event.event = payload['event_type']
        event.user_id = payload['user_id']

        try:
            event.save()
        except pytz.AmbiguousTimeError:
            pass

        return HttpResponse(json.dumps({'result': 'success'}), content_type='application/json')
    except UnreadablePostError:
        return HttpResponse(json.dumps({'result': 'error', 'message': 'Unreadable POST request'}), content_type='application/json')

    return HttpResponse(json.dumps({'result': 'error', 'message': 'Unknown error'}), content_type='application/json')


@staff_member_required
@never_cache
def test_report(request, slug):
    context = RequestContext(request)

    context['test'] = get_object_or_404(PurpleRobotTest, slug=slug)

    return render_to_response('purple_robot_test.html', context)


@staff_member_required
@never_cache
def tests_by_user(request, user_id):
    context = RequestContext(request)

    context['tests'] = PurpleRobotTest.objects.filter(user_id=user_id)
    context['user_id'] = user_id

    context['success'] = True

    for test in context['tests']:
        if test.active and test.passes() == False:
            context['success'] = False

    return render_to_response('purple_robot_tests.html', context)


@staff_member_required
@never_cache
def tests_all(request):
    context = RequestContext(request)

    context['tests'] = PurpleRobotTest.objects.order_by('-last_updated')
    context['user_id'] = 'All'

    context['success'] = True

    for test in context['tests']:
        if test.active and test.passes() == False:
            context['success'] = False

    return render_to_response('purple_robot_tests.html', context)


@staff_member_required
@never_cache
def pr_home(request):
    context = RequestContext(request)

    context['device_groups'] = PurpleRobotDeviceGroup.objects.all()
    context['unattached_devices'] = PurpleRobotDevice.objects.filter(device_group=None)

    return render_to_response('purple_robot_home.html', context)


@staff_member_required
@never_cache
def pr_device(request, device_id):
    context = RequestContext(request)

    context['device'] = PurpleRobotDevice.objects.get(device_id=device_id)

    context.update(csrf(request))

    try:
        context['pr_show_device_id_header'] = settings.PURPLE_ROBOT_SHOW_DEVICE_ID_HEADER
    except KeyError:
        context['pr_show_device_id_header'] = True

    try:
        context['pr_show_notes'] = settings.PURPLE_ROBOT_SHOW_NOTES
    except KeyError:
        context['pr_show_notes'] = True

    return render_to_response('purple_robot_device.html', context)


@staff_member_required
@never_cache
def pr_device_probe(request, device_id, probe_name):
    context = RequestContext(request)

    context['device'] = PurpleRobotDevice.objects.get(device_id=device_id)
    context['probe_name'] = probe_name
    context['short_name'] = probe_name.split('.')[-1]
    context['last_reading'] = PurpleRobotReading.objects.filter(user_id=context['device'].user_hash, probe=probe_name).order_by('-logged').first()
    context['test'] = PurpleRobotTest.objects.filter(user_id=context['device'].user_hash, probe=probe_name).first()
    context['last_readings'] = PurpleRobotReading.objects.filter(user_id=context['device'].user_hash, probe=probe_name).order_by('-logged')[:500]
    context['visualization'] = context['device'].visualization_for_probe(probe_name)

    try:
        context['pr_show_device_id_header'] = settings.PURPLE_ROBOT_SHOW_DEVICE_ID_HEADER
    except KeyError:
        context['pr_show_device_id_header'] = True

    try:
        context['pr_show_notes'] = settings.PURPLE_ROBOT_SHOW_NOTES
    except KeyError:
        context['pr_show_notes'] = True

    return render_to_response('purple_robot_device_probe.html', context)


@staff_member_required
@never_cache
def pr_by_probe(request):
    return render_to_response('purple_robot_probe.html')


@staff_member_required
@never_cache
def pr_by_user(request):
    users = {}

    hashes = PurpleRobotReport.objects.order_by().values('user_id').distinct()

    for user_hash in hashes:
        user_id = user_hash['user_id']

        user_dict = {}

        for report in PurpleRobotReport.objects.filter(user_id=user_id).order_by('-generated'):
            key = str(report) + '-' + report.mime_type

            if (key in user_dict) is False:
                user_dict[key] = report

        users[user_id] = user_dict

    context = RequestContext(request)
    context['users'] = users

    return render_to_response('purple_robot_user.html', context)


@staff_member_required
@never_cache
def test_details_json(request, slug):
    results = []

    test = PurpleRobotTest.objects.get(slug=slug)

    cpu_frequency = {'color': 'rgba(0,0,128,0.25)', 'data': [], 'name': 'CPU Timestamps'}
    sensor_frequency = {'color': 'rgba(128,0,0,0.75)', 'data': [], 'name': 'Sensor Timestamps'}

    if request.method == 'GET':
        timestamp = float(request.GET['timestamp'])

        sample_date = datetime.datetime.utcfromtimestamp(timestamp)

        delta = datetime.timedelta(seconds=450)

        start = sample_date - delta
        end = sample_date + delta

        readings = PurpleRobotReading.objects.filter(probe=test.probe, user_id=test.user_id, logged__gte=start, logged__lte=end).order_by('logged')

        sensor_stamps = []
        cpu_stamps = []

        for reading in readings:
            payload = json.loads(reading.payload)

            if 'SENSOR_TIMESTAMP' in payload:
                for timestamp in payload['SENSOR_TIMESTAMP']:
                    if payload['PROBE'] == 'edu.northwestern.cbits.purple_robot_manager.probes.devices.PebbleProbe':
                        sensor_stamps.append(float(timestamp) / 1000)
                    else:
                        sensor_stamps.append(float(timestamp) / 1000000000)

            if 'EVENT_TIMESTAMP' in payload:
                for timestamp in payload['EVENT_TIMESTAMP']:
                    cpu_stamps.append(timestamp)
            else:
                cpu_stamps.append(payload['TIMESTAMP'])

        if len(cpu_stamps) > 0:
            cpu_stamps.sort()

            start_cpu = cpu_stamps[0]

            index = start_cpu
            count = 0
            cpu_data = []

            for timestamp in cpu_stamps:
                if timestamp < index + 1:
                    count += 1
                else:
                    while timestamp > index + 1:
                        cpu_data.append({'x': index, 'y': count})
                        index += 1
                        count = 0

            cpu_frequency['data'] = cpu_data

        if len(sensor_stamps) > 0:
            sensor_stamps.sort()
            start_sensor = sensor_stamps[0]

            new_sensor_stamps = []

            for timestamp in sensor_stamps:
                new_sensor_stamps.append(timestamp - start_sensor + start_cpu)

            sensor_stamps = new_sensor_stamps

            index = start_cpu
            count = 0
            sensor_data = []

            for timestamp in sensor_stamps:
                if timestamp < index + 1:
                    count += 1
                else:
                    while timestamp > index + 1:
                        sensor_data.append({'x': index, 'y': count})
                        index += 1
                        count = 0

            sensor_frequency['data'] = sensor_data

    results.append(sensor_frequency)
    results.append(cpu_frequency)

    return HttpResponse(json.dumps(results), content_type='application/json')


@staff_member_required
@never_cache
def fetch_export_file(request, job_pk):
    job = PurpleRobotExportJob.objects.get(pk=int(job_pk))

    return redirect(job.export_file.url)


@staff_member_required
@never_cache
def create_export_job(request):
    context = RequestContext(request)

    context['form'] = ExportJobForm()

    if request.method == 'POST':
        form = ExportJobForm(request.POST)

        if form.is_valid():
            job = PurpleRobotExportJob(destination=form.cleaned_data.get('destination'),
                                       start_date=form.cleaned_data.get('start_date'),
                                       end_date=form.cleaned_data.get('end_date'))

            probes = ''

            for probe in form.cleaned_data.get('probes'):
                if len(probes) > 0:
                    probes += '\n'

                probes += probe

            job.probes = probes

            hashes = ''

            for user_hash in form.cleaned_data.get('hashes'):
                if len(user_hash) > 0:
                    hashes += '\n'

                hashes += user_hash

            job.users = hashes

            job.save()

            context['message'] = 'Export job queued successfully.'
        else:
            context['form'] = form

    return render_to_response('purple_robot_export.html', context)


@staff_member_required
@never_cache
def pr_add_group(request):
    if request.method == 'POST':
        group_id = request.POST['group_id']
        group_name = request.POST['group_name']

        if group_id is None or len(group_id.strip()) == 0 or group_name is None or len(group_id.strip()) == 0:
            request.session['pr_messages'] = ['Please provide a non-empty group name and identifier.']
        elif PurpleRobotDeviceGroup.objects.filter(group_id=group_id).count() == 0:
            group = PurpleRobotDeviceGroup(group_id=group_id, name=group_name)

            group.save()
        else:
            request.session['pr_messages'] = ['Unable to create group. A group already exists with identifier "' + group_id + '".']

    return redirect(reverse('pr_home'))


@staff_member_required
@never_cache
def pr_add_device(request, group_id):
    group = PurpleRobotDeviceGroup.objects.filter(group_id=group_id).first()

    if group is not None:
        if request.method == 'POST':
            device_id = request.POST['device_id']
            device_name = request.POST['device_name']

            if device_id is None or len(device_id.strip()) == 0 or device_name is None or len(device_name.strip()) == 0:
                request.session['pr_messages'] = ['Please provide a non-empty device name and identifier.']
            elif PurpleRobotDevice.objects.filter(device_id=device_id).count() == 0:
                device = PurpleRobotDevice(device_id=device_id, name=device_name, device_group=group)

                perf_data = json.loads(device.performance_metadata)

                perf_data['latest_readings'] = {}
                perf_data['latest_readings']['edu.northwestern.cbits.purple_robot_manager.probes.builtin.RobotHealthProbe'] = -1
                perf_data['latest_readings']['edu.northwestern.cbits.purple_robot_manager.probes.builtin.BatteryProbe'] = -1
                perf_data['latest_readings']['edu.northwestern.cbits.purple_robot_manager.probes.builtin.SoftwareInformationProbe'] = -1
                perf_data['latest_readings']['edu.northwestern.cbits.purple_robot_manager.probes.builtin.HardwareInformationProbe'] = -1

                device.performance_metadata = json.dumps(perf_data, indent=2)

                device.save()
            else:
                request.session['pr_messages'] = ['Unable to create device. A device already exists with identifier "' + device_id + '".']
    else:
        request.session['pr_messages'] = ['Unable to locate group with identifier "' + group_id + '" and create new device.']

    response = redirect(reverse('pr_home'))

    return response


@staff_member_required
@never_cache
def pr_remove_device(request, group_id, device_id):
    group = PurpleRobotDeviceGroup.objects.filter(pk=int(group_id)).first()

    device = group.devices.filter(pk=int(device_id)).first()

    if device is not None:
        group.devices.remove(device)
        group.save()

    return redirect(reverse('pr_home'))


@staff_member_required
@never_cache
def pr_configurations(request):
    context = RequestContext(request)
    context.update(csrf(request))

    context['configurations'] = PurpleRobotConfiguration.objects.all()

    return render_to_response('purple_robot_configurations.html', context)


@staff_member_required
@never_cache
def pr_configuration(request, config_id):
    context = RequestContext(request)
    context.update(csrf(request))

    context['config'] = get_object_or_404(PurpleRobotConfiguration, slug=config_id)

    return render_to_response('purple_robot_configuration.html', context)


@staff_member_required
@never_cache
def pr_move_device(request):
    group = PurpleRobotDeviceGroup.objects.filter(pk=int(request.POST['field_new_group'])).first()

    device = PurpleRobotDevice.objects.filter(pk=int(request.POST['field_device_id'])).first()

    if device is not None:
        device.device_group = group
        device.save()

    return redirect(reverse('pr_home'))


@staff_member_required
@never_cache
def pr_add_note(request):
    response = {'result': 'error', 'message': 'No note provided or other error. See server logs.'}

    if request.method == 'POST':
        device_id = request.POST['device_id']
        note_contents = request.POST['note_contents']

        device = PurpleRobotDevice.objects.filter(device_id=device_id).first()

        if device is not None:
            PurpleRobotDeviceNote(device=device, added=timezone.now(), note=note_contents).save()
            response['message'] = 'Note added. Reloading page...'
            response['result'] = 'success'
        else:
            response['message'] = 'Note not added. Device does not exist.'

    return HttpResponse(json.dumps(response, indent=2), content_type='application/json')


@never_cache
def pr_status(request):
    context = RequestContext(request)
    context.update(csrf(request))

    context['server_performance'] = fetch_performance_samples('system', 'server_performance')

    context['ingest_performance'] = fetch_performance_samples('system', 'reading_ingestion_performance')
    context['mirror_performance'] = fetch_performance_samples('system', 'reading_mirror_performance')
    context['pending_ingest'] = fetch_performance_samples('system', 'pending_ingest_payloads')
    context['pending_mirror'] = fetch_performance_samples('system', 'pending_mirror_payloads')

    context['skipped_ingest'] = fetch_performance_samples('system', 'skipped_ingest_payloads')
    context['skipped_mirror'] = fetch_performance_samples('system', 'skipped_mirror_payloads')
    context['uploads_today'] = fetch_performance_samples('system', 'uploads_today')
    context['uploads_hour'] = fetch_performance_samples('system', 'uploads_hour')

    context['pending_mirror_ages'] = fetch_performance_samples('system', 'pending_mirror_ages')
    context['pending_ingest_ages'] = fetch_performance_samples('system', 'pending_ingest_ages')

    context['payload_uploads'] = fetch_performance_samples('system', 'payload_uploads')[-1]['counts']

    context['timezone'] = settings.TIME_ZONE

    here_tz = pytz.timezone(settings.TIME_ZONE)
    now = arrow.get(timezone.now().astimezone(here_tz))

    start_today = now.replace(hour=0, minute=0, second=0, microsecond=0).datetime
    start_hour = now.datetime - datetime.timedelta(hours=1)

    week_ago = timezone.now() - datetime.timedelta(days=7)

    upload_seconds = (arrow.get(context['uploads_today'][-1]['sample_date']).datetime.astimezone(here_tz) - start_today).total_seconds()

    context['now'] = now
    context['start_today'] = start_today
    context['start_hour'] = start_hour

    context['upload_count'] = '-'
    context['upload_rate'] = '-'

    if len(context['uploads_today']) > 0:
        context['upload_count'] = context['uploads_today'][-1]['count']
        context['upload_rate'] = context['uploads_today'][-1]['count'] / upload_seconds
        context['upload_seconds'] = upload_seconds
        context['uploads_today'] = arrow.get(context['uploads_today'][-1]['sample_date']).datetime.astimezone(here_tz)  # c['uploads_today'][-1]['sample_date']

    upload_seconds = (arrow.get(context['uploads_hour'][-1]['sample_date']).datetime.astimezone(here_tz) - start_hour).total_seconds()

    context['upload_hour_count'] = '-'
    context['upload_hour_rate'] = '-'

    if len(context['uploads_hour']) > 0:
        context['upload_hour_count'] = context['uploads_hour'][-1]['count']
        context['upload_hour_rate'] = context['uploads_hour'][-1]['count'] / upload_seconds
        context['upload_hour_seconds'] = upload_seconds
        context['uploads_hour'] = arrow.get(context['uploads_hour'][-1]['sample_date']).datetime.astimezone(here_tz)  # c['uploads_hour'][-1]['sample_date']

    active_count = 0
    inactive_count = 0

    for device in PurpleRobotDevice.objects.all():
        last_reading = device.most_recent_reading('edu.northwestern.cbits.purple_robot_manager.probes.builtin.RobotHealthProbe')

        if last_reading is not None and last_reading.logged > week_ago:
            active_count += 1
        else:
            inactive_count += 1

    context['active_devices'] = active_count
    context['inactive_devices'] = inactive_count

    day_items = []
    hour_items = []

    for item in context['ingest_performance']:
        if arrow.get(item['sample_date']).datetime >= start_today:
            day_items.append(item['num_extracted'] / (item['extraction_time'] + item['query_time']))

        if arrow.get(item['sample_date']).datetime >= start_hour:
            hour_items.append(item['num_extracted'] / (item['extraction_time'] + item['query_time']))

    context['ingest_average_day'] = numpy.mean(day_items)
    context['ingest_average_hour'] = numpy.mean(hour_items)

    day_items = []
    hour_items = []

    for item in context['mirror_performance']:
        if arrow.get(item['sample_date']).datetime >= start_today:
            day_items.append(item['num_mirrored'] / (item['extraction_time'] + item['query_time']))

        if arrow.get(item['sample_date']).datetime >= start_hour:
            hour_items.append(item['num_mirrored'] / (item['extraction_time'] + item['query_time']))

    if len(day_items) > 0:
        context['mirror_average_day'] = numpy.mean(day_items)

    if len(hour_items) > 0:
        context['mirror_average_hour'] = numpy.mean(hour_items)

    return render_to_response('purple_robot_status.html', context)


@staff_member_required
@never_cache
def pr_users(request):
    context = RequestContext(request)
    context.update(csrf(request))

    context['groups'] = PurpleRobotDeviceGroup.objects.all().order_by('group_id')
    context['unaffiliated'] = PurpleRobotDevice.objects.filter(device_group=None).order_by('device_id')

    phantoms = fetch_performance_users()

    for device in PurpleRobotDevice.objects.all():
        if device.hash_key is not None and device.hash_key in phantoms:
            del phantoms[device.hash_key]

    context['phantoms'] = phantoms

    return render_to_response('purple_robot_users.html', context)

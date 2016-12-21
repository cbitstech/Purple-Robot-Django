import datetime
import hashlib
import json
import pytz

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

from forms import ExportJobForm
from models import PurpleRobotPayload, PurpleRobotTest, PurpleRobotEvent, \
                   PurpleRobotReport, PurpleRobotExportJob, PurpleRobotReading, \
                   PurpleRobotConfiguration, PurpleRobotDevice, PurpleRobotDeviceGroup, \
                   PurpleRobotDeviceNote

@never_cache
def config(request):
    config = None
    
    try:
        device_id = request.GET['user_id']
        
        device = PurpleRobotDevice.objects.get(device_id=device_id)
        
        if device.configuration != None:
            config = device.configuration
        elif device.device_group.configuration != None:
            config = device.device_group.configuration
            
        device.config_last_fetched = datetime.datetime.now()
        
        try:
            device.config_last_user_agent = request.META['HTTP_USER_AGENT']
        except KeyError:
            device.config_last_user_agent = 'Unknown'
        
        device.save()
    except:
        pass
        
    if config == None:
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
           
            m = hashlib.md5()
            m.update((json_obj['UserHash'] + json_obj['Operation'] + json_obj['Payload']).encode('utf-8'))
        
            checksum_str = m.hexdigest()
        
            result = {}
            result['Status'] = 'error'
            result['Payload'] = "{}"
        
            if checksum_str == json_obj['Checksum']:
                result['Status'] = 'success'
            
                payload_json = json.loads(payload_str)
            
                payload = PurpleRobotPayload(payload=json.dumps(payload_json, indent=2, ensure_ascii=False), user_id=json_obj['UserHash'])
                payload.save()
        
                m = hashlib.md5()
                m.update(result['Status'] + result['Payload'])
        
                result['Checksum'] = m.hexdigest()
            
                if 'media_url' in payload_str:
                    payload.ingest_readings()
                    for k, v in request.FILES.iteritems():
                        reading = PurpleRobotReading.objects.filter(guid=k).first()
                        
                        if reading != None:
                            reading.attachment.save(v.name, v)
            else:
                result['Error'] = 'Source checksum ' + json_obj['Checksum'] + ' doesn\'t match destination checksum ' + checksum_str + '.'
        except Exception, e:
            result['Error'] = str(e)
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
        
        # payload_str = json_obj['Payload']
           
        m = hashlib.md5()
        m.update((json_obj['UserHash'] + json_obj['Operation'] + json_obj['Payload']).encode('utf-8'))
        
        checksum_str = m.hexdigest()
        
        result = {}
        result['Status'] = 'error'
        result['Payload'] = "{}"
        
        if checksum_str == json_obj['Checksum']:
            result['Status'] = 'success'
        
            # payload_json = json.loads(payload_str)
            # print('PAYLOAD: ' + json.dumps(payload_json, indent=2, ensure_ascii=False))
        
            m = hashlib.md5()
            m.update(result['Status'] + result['Payload'])
        
            result['Checksum'] = m.hexdigest()
        else:
            result['Error'] = 'Source checksum ' + json_obj['Checksum'] + ' doesn\'t match destination checksum ' + checksum_str + '.'
    except Exception, e:
        result['Error'] = str(e)
        
    return HttpResponse(json.dumps(result), content_type='application/json')

@csrf_exempt
@never_cache
def log_event(request):
    try:
        payload = json.loads(request.POST['json'])

        tz = pytz.timezone(settings.TIME_ZONE)
        logged = tz.localize(datetime.datetime.fromtimestamp(int(payload['timestamp'])))
    
        if PurpleRobotEvent.objects.filter(logged=logged, event=payload['event_type']).count() == 0:
            try:
                if len(payload['user_id'].strip()) == 0:
                    payload['user_id'] = '-'
            except KeyError:
                payload['user_id'] = '-'
        
            event = PurpleRobotEvent(payload=json.dumps(payload, indent=2))
            event.logged = logged
            event.event = payload['event_type']
            event.user_id = payload['user_id']
        
            event.save()
    
        return HttpResponse(json.dumps({ 'result': 'success' }), content_type='application/json')
    except UnreadablePostError:
        return HttpResponse(json.dumps({ 'result': 'error', 'message': 'Unreadable POST request' }), content_type='application/json')

    return HttpResponse(json.dumps({ 'result': 'error', 'message': 'Unknown error' }), content_type='application/json')

@staff_member_required
@never_cache
def test_report(request, slug):
    c = RequestContext(request)
    
    c['test'] = get_object_or_404(PurpleRobotTest, slug=slug)
    
    return render_to_response('purple_robot_test.html', c)

@staff_member_required
@never_cache
def tests_by_user(request, user_id):
    c = RequestContext(request)
    
    c['tests'] = PurpleRobotTest.objects.filter(user_id=user_id)
    c['user_id'] = user_id
    
    c['success'] = True
    
    for test in c['tests']:
        if test.active and test.passes() == False:
            c['success'] = False        
    
    return render_to_response('purple_robot_tests.html', c)

@staff_member_required
@never_cache
def tests_all(request):
    c = RequestContext(request)
    
    c['tests'] = PurpleRobotTest.objects.order_by('-last_updated')
    c['user_id'] = 'All'
    
    c['success'] = True
    
    for test in c['tests']:
        if test.active and test.passes() == False:
            c['success'] = False        
    
    return render_to_response('purple_robot_tests.html', c)

@staff_member_required
@never_cache
def pr_home(request):
    c = RequestContext(request)
    
    c['device_groups'] = PurpleRobotDeviceGroup.objects.all()
    c['unattached_devices'] = PurpleRobotDevice.objects.filter(device_group=None)

    return render_to_response('purple_robot_home.html', c)

@staff_member_required
@never_cache
def pr_device(request, device_id):
    c = RequestContext(request)
    
    c['device'] = PurpleRobotDevice.objects.get(device_id=device_id)

    c.update(csrf(request))

    return render_to_response('purple_robot_device.html', c)

@staff_member_required
@never_cache
def pr_device_probe(request, device_id, probe_name):
    c = RequestContext(request)
    
    c['device'] = PurpleRobotDevice.objects.get(device_id=device_id)
    c['probe_name'] = probe_name
    c['short_name'] = probe_name.split('.')[-1]
    c['last_reading'] = PurpleRobotReading.objects.filter(user_id=c['device'].user_hash, probe=probe_name).order_by('-logged').first()
    c['test'] = PurpleRobotTest.objects.filter(user_id=c['device'].user_hash, probe=probe_name).first()
    c['last_readings'] = PurpleRobotReading.objects.filter(user_id=c['device'].user_hash, probe=probe_name).order_by('-logged')[:500]
    c['visualization'] = c['device'].visualization_for_probe(probe_name)

    return render_to_response('purple_robot_device_probe.html', c)

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
            
            if (key in user_dict) == False:
                user_dict[key] = report
        
        users[user_id] = user_dict

    c = RequestContext(request)
    c['users'] = users

    return render_to_response('purple_robot_user.html', c)


@staff_member_required
@never_cache
def test_details_json(request, slug):
    results = []
    
    test = PurpleRobotTest.objects.get(slug=slug)
    
    cpu_frequency = { 'color': 'rgba(0,0,128,0.25)', 'data': [], 'name': 'CPU Timestamps'}
    sensor_frequency = { 'color': 'rgba(128,0,0,0.75)', 'data': [], 'name': 'Sensor Timestamps'}
    
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
                for ts in payload['SENSOR_TIMESTAMP']:
                    if payload['PROBE'] == 'edu.northwestern.cbits.purple_robot_manager.probes.devices.PebbleProbe':
                        sensor_stamps.append(float(ts) / 1000)
                    else:
                        sensor_stamps.append(float(ts) / 1000000000)

            if 'EVENT_TIMESTAMP' in payload:
                for ts in payload['EVENT_TIMESTAMP']:
                    cpu_stamps.append(ts)
            else:
                cpu_stamps.append(payload['TIMESTAMP'])
                
        if len(cpu_stamps) > 0:
            cpu_stamps.sort()
    
            start_cpu = cpu_stamps[0]
    
            index = start_cpu
            count = 0
            cpu_data = []
            
            for ts in cpu_stamps:
                if ts < index + 1:
                    count += 1
                else:
                    while ts > index + 1:
                        cpu_data.append({ 'x': index, 'y': count })
                        index += 1
                        count = 0
                    
            cpu_frequency['data'] = cpu_data
            
        if len(sensor_stamps) > 0:
            sensor_stamps.sort()
            start_sensor = sensor_stamps[0]
            
            new_sensor_stamps = []
            
            for ts in sensor_stamps:
                new_sensor_stamps.append(ts - start_sensor + start_cpu)
            
            sensor_stamps = new_sensor_stamps

            index = start_cpu
            count = 0
            sensor_data = []
            
            for ts in sensor_stamps:
                if ts < index + 1:
                    count += 1
                else:
                    while ts > index + 1:
                        sensor_data.append({ 'x': index, 'y': count })
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
    c = RequestContext(request)

    c['form'] = ExportJobForm()
    
    if request.method == 'POST':
        form = ExportJobForm(request.POST)
        
        if form.is_valid():
            job = PurpleRobotExportJob(destination=form.cleaned_data.get('destination'), \
                                       start_date=form.cleaned_data.get('start_date'), \
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
            
            c['message'] = 'Export job queued successfully.'
        else:
            c['form'] = form

    return render_to_response('purple_robot_export.html', c)
    
@staff_member_required
@never_cache
def pr_add_group(request):
    if request.method == 'POST':
        group_id = request.POST['group_id']
        group_name = request.POST['group_name']
        
        if group_id == None or len(group_id.strip()) == 0 or group_name == None or len(group_id.strip()) == 0:
            request.session['pr_messages'] = [ 'Please provide a non-empty group name and identifier.' ]
        elif PurpleRobotDeviceGroup.objects.filter(group_id=group_id).count() == 0:
            group = PurpleRobotDeviceGroup(group_id=group_id, name=group_name)
            
            group.save()
        else:
            request.session['pr_messages'] = [ 'Unable to create group. A group already exists with identifier "' + group_id + '".' ]
    
    return redirect(reverse('pr_home'))

@staff_member_required
@never_cache
def pr_add_device(request, group_id):
    group = PurpleRobotDeviceGroup.objects.filter(group_id=group_id).first()

    if group != None:
        if request.method == 'POST':
            device_id = request.POST['device_id']
            device_name = request.POST['device_name']

            if device_id == None or len(device_id.strip()) == 0 or device_name == None or len(device_name.strip()) == 0:
                request.session['pr_messages'] = [ 'Please provide a non-empty device name and identifier.' ]
            elif PurpleRobotDevice.objects.filter(device_id=device_id).count() == 0:
                device = PurpleRobotDevice(device_id=device_id, name=device_name, device_group=group)

                device.save()
            else:
                request.session['pr_messages'] = [ 'Unable to create device. A device already exists with identifier "' + device_id + '".' ]
    else:
        request.session['pr_messages'] = [ 'Unable to locate group with identifier "' + group_id + '" and create new device.' ]
    
    return redirect(reverse('pr_home'))

@staff_member_required
@never_cache
def pr_remove_device(request, group_id, device_id):
    group = PurpleRobotDeviceGroup.objects.filter(pk=int(group_id)).first()
    
    device = group.devices.filter(pk=int(device_id)).first()
    
    if device != None:
        group.devices.remove(device)
        group.save()
    
    return redirect(reverse('pr_home'))

@staff_member_required
@never_cache
def pr_configurations(request):
    c = RequestContext(request)
    c.update(csrf(request))
    
    c['configurations'] = PurpleRobotConfiguration.objects.all()
        
    return render_to_response('purple_robot_configurations.html', c)


@staff_member_required
@never_cache
def pr_configuration(request, config_id):
    c = RequestContext(request)
    c.update(csrf(request))

    c['config'] = get_object_or_404(PurpleRobotConfiguration, slug=config_id)

    return render_to_response('purple_robot_configuration.html', c)
 
@staff_member_required
@never_cache
def pr_move_device(request):
    group = PurpleRobotDeviceGroup.objects.filter(pk=int(request.POST['field_new_group'])).first()
    
    device = PurpleRobotDevice.objects.filter(pk=int(request.POST['field_device_id'])).first()
    
    if device != None:
        device.device_group = group
        device.save()
    
    return redirect(reverse('pr_home'))

@staff_member_required
@never_cache
def pr_add_note(request):
    response = { 'result': 'error', 'message': 'No note provided or other error. See server logs.' }
    
    if request.method == 'POST':
        device_id = request.POST['device_id']
        note_contents = request.POST['note_contents']
        
        device = PurpleRobotDevice.objects.filter(device_id=device_id).first()
        
        if device != None:
            PurpleRobotDeviceNote(device=device, added=timezone.now(), note=note_contents).save()
            response['message'] = 'Note added. Reloading page...'
            response['result'] = 'success'
        else:
            response['message'] = 'Note not added. Device does not exist.'

    return HttpResponse(json.dumps(response, indent=2), content_type='application/json')
    

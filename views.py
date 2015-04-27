import json
import hashlib
import datetime

from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.views.decorators.csrf import csrf_exempt

from forms import ExportJobForm
from models import PurpleRobotPayload, PurpleRobotTest, PurpleRobotEvent, PurpleRobotReport, PurpleRobotExportJob, PurpleRobotReading

@csrf_exempt
def ingest_payload(request):
    result = {}
    result['Status'] = 'error'
    result['Payload'] = "{}"
    
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
        else:
            result['Error'] = 'Source checksum ' + json_obj['Checksum'] + ' doesn\'t match destination checksum ' + checksum_str + '.'
    except Exception, e:
        result['Error'] = str(e)
        
    return HttpResponse(json.dumps(result), content_type='application/json')


@csrf_exempt
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
def log_event(request):
    payload = json.loads(request.POST['json'])
    
    logged = datetime.datetime.fromtimestamp(int(payload['timestamp']))
    
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

@staff_member_required
def test_report(request, slug):
    c = RequestContext(request)
    
    c['test'] = get_object_or_404(PurpleRobotTest, slug=slug)
    
    return render_to_response('purple_robot_test.html', c)

@staff_member_required
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
def pr_home(request):
    return render_to_response('purple_robot_home.html')


@staff_member_required
def pr_by_probe(request):
    return render_to_response('purple_robot_probe.html')


@staff_member_required
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
def fetch_export_file(request, job_pk):
    job = PurpleRobotExportJob.objects.get(pk=int(job_pk))
    
    return redirect(job.export_file.url)

@staff_member_required
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

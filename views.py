import json
import hashlib
import datetime
import pytz
import time
import traceback
import urllib

from dateutil.parser import parse

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import render, render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt

from models import *

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
def test_payload(request):
    result = {}
    result['Status'] = 'error'
    result['Payload'] = "{}"
    
    probes = {}
    timestamps = {}
    
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
            payload_json = json.loads(payload_str)

            result['Status'] = 'success'
            
            user_id = json_obj['UserHash']
            
            now = time.time()
            yesterday = now - (24 * 60 * 60)

            for reading in payload_json:
                probe_name = reading['PROBE']

                test = None

                if probe_name + '-' + user_id in probes:
                    test = probes[probe_name + '-' + user_id]
                else:   
                    query = PurpleRobotTest.objects.filter(user_id=user_id, probe=probe_name, active=True)
                    
                    if query.count() > 0:
                        test = query[0]
                        
                        probes[probe_name + '-' + user_id] = test
                
                if test != None:
                    probe_times = []
                    
                    if (probe_name + '-' + user_id) in timestamps:
                        probe_times = timestamps[probe_name + '-' + user_id]
                    else:
                        probe_times = json.loads(test.timestamps)
                        timestamps[probe_name + '-' + user_id] = probe_times
                    
                    if 'EVENT_TIMESTAMP' in reading:
                       for timestamp in reading['EVENT_TIMESTAMP']:
                           probe_times.append(timestamp)
                    else:
                        probe_times.append(reading['TIMESTAMP'])
                        
            for k,v in probes.iteritems():
                probe = probes[k]
                probe_times = timestamps[k]
                        
                new_timestamps = []
                    
                for timestamp in probe_times:
                    if timestamp > now:
                        timestamp = timestamp / 1000
                            
                    if timestamp > yesterday:
                        new_timestamps.append(timestamp)
                            
                probe.timestamps = json.dumps(new_timestamps, indent=2)
                probe.save()
            
            if result['Status'] != 'success':
                result['Payload'] = "{}"
        
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
def pr_home(request):
    return render_to_response('purple_robot_home.html')


@staff_member_required
def pr_by_probe(request):
    return render_to_response('purple_robot_probe.html')


@staff_member_required
def pr_by_user(request):
    users = {}
    
    hashes = PurpleRobotReport.objects.order_by().values('user_id').distinct()
        
    for hash in hashes:
        user_id = hash['user_id']
        
        user_dict = {}
        
        for report in PurpleRobotReport.objects.filter(user_id=user_id).order_by('-generated'):
            key = str(report) + '-' + report.mime_type
            
            if (key in user_dict) == False:
                user_dict[key] = report
        
        users[user_id] = user_dict

    c = RequestContext(request)
    c['users'] = users

    return render_to_response('purple_robot_user.html', c)


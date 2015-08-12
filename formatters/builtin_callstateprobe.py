import math
import json

from django.template.loader import render_to_string

def format(probe_name, json_payload):
    item = json.loads(json_payload)
    state = item['CALL_STATE']
    
    return state

def visualize(probe_name, readings):
    report = []
    
    for reading in readings:
        payload = json.loads(reading.payload)
        
        timestamp = payload['TIMESTAMP']
        call_state = payload['CALL_STATE']
        
        if call_state == "Off-Hook":
            call_state = 2
        elif call_state == "Ringing":
            call_state = 1
        elif call_state == "Idle":
            call_state = 0
            
        rep_dict = {}
        rep_dict["y"] = call_state
        rep_dict["x"] = timestamp
        report.append(rep_dict)
    
    return render_to_string('visualization_callstate.html', { 'probe_name' : probe_name, 'readings' : readings, 'callstate_report' : json.dumps(report) })

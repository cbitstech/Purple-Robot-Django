import json

from django.template.loader import render_to_string

def format(probe_name, json_payload):
    item = json.loads(json_payload)
    
    status = 'Unknown'
    
    if item['status'] == 2:
        status = 'Charging'
    elif item['status'] == 3:
        status = 'Discharging'
    elif item['status'] == 5:
        status = 'Full'
    
    return str(item['level']) + '% (' + status + ')'

def visualize(probe_name, readings):
    return render_to_string('visualization_probe.html', { 'probe_name': probe_name, 'readings': readings })

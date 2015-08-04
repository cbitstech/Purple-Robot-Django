import json

from django.template.loader import render_to_string

def format(probe_name, json_payload):
    item = json.loads(json_payload)
    
    if 'PROBE_DISPLAY_MESSAGE' in item:
        return item['PROBE_DISPLAY_MESSAGE']
        
    return probe_name + ': TODO'

def visualize(probe_name, readings):
    return render_to_string('visualization_probe.html', { 'probe_name': probe_name, 'readings': readings })

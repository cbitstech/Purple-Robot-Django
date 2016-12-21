# pylint: disable=line-too-long, unused-argument

import json

from django.template.loader import render_to_string


def format_reading(probe_name, json_payload):
    item = json.loads(json_payload)
    status = item['DEVICE_ACTIVE']

    if item['DEVICE_ACTIVE'] is True:
        status = "Active"
    elif item['DEVICE_ACTIVE'] is False:
        status = "Inactive"

    return status


def visualize(probe_name, readings):
    report = []

    for reading in readings:
        payload = json.loads(reading.payload)

        timestamp = payload['TIMESTAMP']
        device_active = payload['DEVICE_ACTIVE']

        if device_active is True:
            device_active = 1
        elif device_active is False:
            device_active = 0

        rep_dict = {}
        rep_dict["y"] = device_active
        rep_dict["x"] = timestamp
        report.append(rep_dict)

    return render_to_string('visualization_device.html', {'probe_name': probe_name, 'readings': readings, 'device_report': json.dumps(report)})

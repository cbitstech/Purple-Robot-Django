# pylint: disable=line-too-long, unused-argument

import json

from django.template.loader import render_to_string


def format_reading(probe_name, json_payload):
    item = json.loads(json_payload)
    status = item['SCREEN_ACTIVE']

    if item['SCREEN_ACTIVE'] is True:
        status = "Active"
    elif item['SCREEN_ACTIVE'] is False:
        status = "Inactive"

    return status


def visualize(probe_name, readings):
    report = []

    for reading in readings:
        payload = json.loads(reading.payload)

        timestamp = payload['TIMESTAMP']
        screen_active = payload['SCREEN_ACTIVE']

        if screen_active is True:
            screen_active = 1
        elif screen_active is False:
            screen_active = 0

        rep_dict = {}
        rep_dict["y"] = screen_active
        rep_dict["x"] = timestamp
        report.append(rep_dict)

    return render_to_string('visualization_screen.html', {'probe_name': probe_name, 'readings': readings, 'screen_report': json.dumps(report)})

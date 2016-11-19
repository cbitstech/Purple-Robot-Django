# pylint: disable=line-too-long, unused-argument

import math
import json

from django.template.loader import render_to_string


def format_reading(probe_name, json_payload):
    item = json.loads(json_payload)

    provider = item['PROVIDER']

    if item['PROVIDER'] == 'fused':
        provider = 'Fused Provider'

    return provider + ': ' + str(item['LATITUDE']) + ', ' + str(item['LONGITUDE'])


def visualize(probe_name, readings):
    point_counter = {}

    for reading in readings:
        payload = json.loads(reading.payload)

        longitude = payload['LONGITUDE']
        latitude = payload['LATITUDE']

        key = str(round(longitude, 5)) + ',' + str(round(latitude, 5))

        points = []

        try:
            points = point_counter[key]
        except KeyError:
            pass

        points.append(payload)

        point_counter[key] = points

    report = []

    for key in point_counter.keys():
        count = len(point_counter[key])
        latitude = round(point_counter[key][0]['LATITUDE'], 5)
        longitude = round(point_counter[key][0]['LONGITUDE'], 5)

        report_item = {}

        report_item['count'] = 1 + math.log(count, 100)
        report_item['lat'] = latitude
        report_item['lng'] = longitude

        report.append(report_item)

    return render_to_string('visualization_fusedlocationprobe.html', {'probe_name': probe_name, 'readings': readings, 'heat_report':  json.dumps(report, indent=2)})

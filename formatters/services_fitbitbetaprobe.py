# pylint: disable=line-too-long, unused-argument

import json

from django.template.loader import render_to_string


def format_reading(probe_name, json_payload):
    item = json.loads(json_payload)

    heart = '?'
    steps = '?'
    distance = '?'
    calories = '?'
    floors = '?'
    elevation = '?'

    if 'HEART' in item:
        heart = str(len(item['HEART']))

    if 'STEPS' in item:
        steps = str(len(item['STEPS']))

    if 'DISTANCE' in item:
        distance = str(len(item['DISTANCE']))

    if 'CALORIES' in item:
        calories = str(len(item['CALORIES']))

    if 'FLOORS' in item:
        floors = str(len(item['FLOORS']))

    if 'ELEVATION' in item:
        elevation = str(len(item['ELEVATION']))

    return 'Heart: ' + heart + ' Elevation: ' + elevation + ' Distance: ' + distance + ' Steps: ' + steps + ' Floors: ' + floors + ' Calories: ' + calories


def visualize(probe_name, readings):
    heart = []
    steps = []
    distance = []
    calories = []
    floors = []
    elevation = []

    for reading in readings:
        item = json.loads(reading.payload)

        if 'HEART' in item:
            for i in range(0, len(item['HEART'])):
                plot = {'x': item['HEART_TIMESTAMPS'][i] / 1000, 'y': item['HEART'][i]}

                heart.append(plot)

        if 'STEPS' in item:
            for i in range(0, len(item['STEPS'])):
                plot = {'x': item['STEP_TIMESTAMPS'][i] / 1000, 'y': item['STEPS'][i]}

                steps.append(plot)

        if 'FLOORS' in item:
            for i in range(0, len(item['FLOORS'])):
                plot = {'x': item['FLOORS_TIMESTAMPS'][i] / 1000, 'y': item['FLOORS'][i]}

                floors.append(plot)

        if 'ELEVATION' in item:
            for i in range(0, len(item['ELEVATION'])):
                plot = {'x': item['ELEVATION_TIMESTAMPS'][i] / 1000, 'y': item['ELEVATION'][i]}

                elevation.append(plot)

        if 'CALORIES' in item:
            for i in range(0, len(item['CALORIES'])):
                plot = {'x': item['CALORIES_TIMESTAMPS'][i] / 1000, 'y': item['CALORIES'][i]}

                calories.append(plot)

        if 'DISTANCE' in item:
            for i in range(0, len(item['DISTANCE'])):
                plot = {'x': item['DISTANCE_TIMESTAMPS'][i] / 1000, 'y': item['DISTANCE'][i]}

                distance.append(plot)

    heart.sort(key=lambda o: o['x'])
    steps.sort(key=lambda o: o['x'])
    floors.sort(key=lambda o: o['x'])
    elevation.sort(key=lambda o: o['x'])
    calories.sort(key=lambda o: o['x'])
    distance.sort(key=lambda o: o['x'])

    return render_to_string('visualization_fitbit.html', {'probe_name': probe_name, 'distance': json.dumps(distance), 'heart': json.dumps(heart), 'steps': json.dumps(steps), 'floors': json.dumps(floors), 'elevation': json.dumps(elevation), 'calories': json.dumps(calories)})

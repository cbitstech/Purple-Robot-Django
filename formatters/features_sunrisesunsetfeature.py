import datetime
import json

from django.template.loader import render_to_string

def format(probe_name, json_payload):
    item = json.loads(json_payload)

    timestamp = datetime.datetime.fromtimestamp(item["TIMESTAMP"])
    sunrise = datetime.datetime.fromtimestamp((item["SUNRISE"]/1000))
    sunset = datetime.datetime.fromtimestamp((item["SUNSET"]/1000))
    
    day_duration = (item["DAY_DURATION"]/1000)/3600.0
    
    if item["IS_DAY"] == True:
        sunlight_hrs = (timestamp - sunrise).seconds / 3600.0
        return "{0} -> {1}, Daylight hours: {2:.1f} - Hours after sunrise: {3:.1f}".format(str(sunrise)[10:], str(sunset)[10:], day_duration, sunlight_hrs)
    else:
        night_hrs = (timestamp - sunset).seconds / 3600.0
        return "{0} -> {1}, Daylight hours: {2:.1f} - Hours after sunset: {3:.1f}".format(str(sunrise)[10:], str(sunset)[10:], day_duration, night_hrs)
    
def visualize(probe_name, readings):
    sun_report = []
    daylight_report = []
    
    for reading in readings:
        payload = json.loads(reading.payload)
        
        timestamp = payload["TIMESTAMP"]
        sunrise = datetime.datetime.fromtimestamp((payload["SUNRISE"]/1000))
        sunset = datetime.datetime.fromtimestamp((payload["SUNSET"]/1000))
        day_duration = (payload["DAY_DURATION"]/1000)/3600
        
        sun_ref = 0
        if payload["IS_DAY"] == True:
            sun_ref = (datetime.datetime.fromtimestamp(timestamp) - sunrise).seconds / 3600.0
        else:
            sun_ref = -(datetime.datetime.fromtimestamp(timestamp) - sunset).seconds / 3600.0
        
        sun_dict = {}
        sun_dict["y"] = sun_ref
        sun_dict["x"] = timestamp
        sun_report.append(sun_dict)
        
        daylight_dict = {}
        daylight_dict["y"] = day_duration
        daylight_dict["x"] = timestamp
        daylight_report.append(daylight_dict)
        
    return render_to_string(
        'visualization_sunrisesunset.html', 
        { 
            'probe_name' : probe_name, 
            'readings' : readings, 
            'sun_report' : json.dumps(sun_report),
            'daylight_report' : json.dumps(daylight_report)
         }
    )

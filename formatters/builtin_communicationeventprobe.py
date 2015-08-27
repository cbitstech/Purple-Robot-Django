import datetime
import json

from django.template.loader import render_to_string

def format(probe_name, json_payload):
    item = json.loads(json_payload)
    
    comm_type = item["COMMUNICATION_TYPE"]
    comm_direction = item["COMMUNICATION_DIRECTION"]
    comm_timestamp = datetime.datetime.fromtimestamp((item["COMM_TIMESTAMP"]/1000))
    
    if comm_type == "PHONE":
        duration = item["DURATION"]
        return "{0} - {1}: {2} - Duration: {3}".format(comm_timestamp, comm_direction.capitalize(), comm_type.capitalize(), duration)
    else:
        return "{0} - {1}: {2}".format(comm_timestamp, comm_direction.capitalize(), comm_type)

def visualize(probe_name, readings):  
    phone_out_report = []
    phone_in_report = []
    sms_out_report = []
    sms_in_report = []
    
    comm_subtype = 0
    
    for reading in readings:
        payload = json.loads(reading.payload)
        
        timestamp = (payload["COMM_TIMESTAMP"])/1000
        comm_type = payload["COMMUNICATION_TYPE"]
        comm_direct = payload["COMMUNICATION_DIRECTION"]
        
        subtype_dict = {}
        subtype_dict["x"] = timestamp
        
        if comm_type == "PHONE" and comm_direct == "OUTGOING":
            comm_type = 1
            comm_subtype = 3
            subtype_dict["y"] = comm_subtype
            phone_out_report.append(subtype_dict)
            
        elif comm_type == "PHONE" and comm_direct == "INCOMING":
            comm_type = 1
            comm_subtype = 2
            subtype_dict["y"] = comm_subtype
            phone_in_report.append(subtype_dict)
            
        elif comm_type == "SMS" and comm_direct == "OUTGOING":
            comm_type = 0
            comm_subtype = 1
            subtype_dict["y"] = comm_subtype
            sms_out_report.append(subtype_dict)
            
        elif comm_type == "SMS" and comm_direct == "INCOMING":
            comm_type = 0
            comm_subtype = 0
            subtype_dict["y"] = comm_subtype
            sms_in_report.append(subtype_dict)
        
    return render_to_string(
        'visualization_communicationevent.html', 
        { 
            'probe_name' : probe_name, 
            'readings' : readings, 
            'phone_out_report' : json.dumps(phone_out_report),
            'phone_in_report' : json.dumps(phone_in_report),
            'sms_out_report' : json.dumps(sms_out_report),
            'sms_in_report' : json.dumps(sms_in_report)
         }
    )

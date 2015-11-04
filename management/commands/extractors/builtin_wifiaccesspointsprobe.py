import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_wifiaccesspointsprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, current_ssid TEXT, current_bssid TEXT, current_rssi DOUBLE PRECISION, current_link_speed DOUBLE PRECISION, access_point_count BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_wifiaccesspointsprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_wifiaccesspointsprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_wifiaccesspointsprobe(utc_logged);'

CREATE_ACCESS_POINT_TABLE_SQL = 'CREATE TABLE builtin_wifiaccesspointsprobe_accesspoint(id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, ssid TEXT, bssid TEXT, capabilities TEXT, frequency DOUBLE PRECISION, level DOUBLE PRECISION);'
CREATE_ACCESS_POINT_USER_ID_INDEX = 'CREATE INDEX ON builtin_wifiaccesspointsprobe_accesspoint(user_id);'
CREATE_ACCESS_POINT_READING_ID_INDEX = 'CREATE INDEX ON builtin_wifiaccesspointsprobe_accesspoint(reading_id);'
CREATE_ACCESS_POINT_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_wifiaccesspointsprobe_accesspoint(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) == False or access_point_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_wifiaccesspointsprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_wifiaccesspointsprobe\')')
    
    probe_table_exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return probe_table_exists

def access_point_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_wifiaccesspointsprobe_accesspoint\')')
    
    activities_table_exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return activities_table_exists

def insert(connection_str, user_id, reading, check_exists=True):
#    print(json.dumps(reading, indent=2))
    
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    
    if check_exists and probe_table_exists(conn) == False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)
    
    if check_exists and access_point_table_exists(conn) == False:
        cursor.execute(CREATE_ACCESS_POINT_TABLE_SQL)
        cursor.execute(CREATE_ACCESS_POINT_USER_ID_INDEX)
        cursor.execute(CREATE_ACCESS_POINT_READING_ID_INDEX)
        cursor.execute(CREATE_ACCESS_POINT_UTC_LOGGED_INDEX)
        
    conn.commit()
    
    reading_cmd = 'INSERT INTO builtin_wifiaccesspointsprobe(user_id, ' + \
                                                            'guid, ' + \
                                                            'timestamp, ' + \
                                                            'utc_logged, ' + \
                                                            'current_ssid, ' + \
                                                            'current_bssid, ' + \
                                                            'current_rssi, ' + \
                                                            'current_link_speed, ' + \
                                                            'access_point_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    
    current_ssid = None
    current_bssid = None
    current_link_speed = None
    current_rssi = None
    
    if 'CURRENT_SSID' in reading:
        current_ssid = reading['CURRENT_SSID']
        
    if 'CURRENT_BSSID' in reading:
        current_bssid = reading['CURRENT_BSSID']
        
    if 'CURRENT_LINK_SPEED' in reading:
        current_link_speed = reading['CURRENT_LINK_SPEED']

    if 'CURRENT_RSSI' in reading:
        current_rssi = reading['CURRENT_RSSI']
    
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 current_ssid, \
                                 current_bssid, \
                                 current_rssi, \
                                 current_link_speed, \
                                 reading['ACCESS_POINT_COUNT']))
    
    for row in cursor.fetchall():
        reading_id = row[0]
        
        ap_cursor = conn.cursor()
        
        for point in reading['ACCESS_POINTS']:
            point_cmd = 'INSERT INTO builtin_wifiaccesspointsprobe_accesspoint(user_id, ' + \
                                                                              'reading_id, ' + \
                                                                              'utc_logged, ' + \
                                                                              'ssid, ' + \
                                                                              'bssid, ' + \
                                                                              'capabilities, ' + \
                                                                              'frequency, ' + \
                                                                              'level) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'

            ap_cursor.execute(point_cmd, (user_id, \
                                          reading_id, 
                                          datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), 
                                          point['SSID'], 
                                          point['BSSID'], 
                                          point['CAPABILITIES'], 
                                          point['FREQUENCY'], 
                                          point['LEVEL']))

    conn.commit()
        
    cursor.close()
    conn.close()

import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_hardwareinformationprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, product TEXT, bootloader TEXT, brand TEXT, mobile_id TEXT, hardware TEXT, host TEXT, bluetooth_mac TEXT, board TEXT, fingerprint TEXT, device TEXT, model TEXT, wifi_mac TEXT, display TEXT, device_id TEXT, manufacturer TEXT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_hardwareinformationprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_hardwareinformationprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_hardwareinformationprobe(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    
    if probe_table_exists(conn) == False:
        conn.close()
        
        return False
        
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_hardwareinformationprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_hardwareinformationprobe\')')
    
    probe_table_exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return probe_table_exists

def insert(connection_str, user_id, reading):
#    print(json.dumps(reading, indent=2))
    
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    
    if probe_table_exists(conn) == False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)
    
    conn.commit()
    
    reading_cmd = 'INSERT INTO builtin_hardwareinformationprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'product, ' + \
                                                   'bootloader, ' + \
                                                   'brand, ' + \
                                                   'mobile_id, ' + \
                                                   'hardware, ' + \
                                                   'host, ' + \
                                                   'bluetooth_mac, ' + \
                                                   'board, ' + \
                                                   'fingerprint, ' + \
                                                   'device, ' + \
                                                   'model, ' + \
                                                   'wifi_mac, ' + \
                                                   'display, ' + \
                                                   'device_id, ' + \
                                                   'manufacturer) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    
    mobile_id = None
    bluetooth_mac = None
    
    if 'MOBILE_ID' in reading:
        mobile_id = reading['MOBILE_ID']

    if 'BLUETOOTH_MAC' in reading:
        bluetooth_mac = reading['BLUETOOTH_MAC']
    
    wifi_mac = None
    
    if 'WIFI_MAC' in reading:
        wifi_mac = reading['WIFI_MAC']
        
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 reading['PRODUCT'], \
                                 reading['BOOTLOADER'], \
                                 reading['BRAND'], \
                                 mobile_id, \
                                 reading['HARDWARE'], \
                                 reading['HOST'], \
                                 bluetooth_mac, \
                                 reading['BOARD'], \
                                 reading['FINGERPRINT'], \
                                 reading['DEVICE'], \
                                 reading['MODEL'], \
                                 wifi_mac, \
                                 reading['DISPLAY'], \
                                 reading['ID'], \
                                 reading['MANUFACTURER']))

    conn.commit()
        
    cursor.close()
    conn.close()

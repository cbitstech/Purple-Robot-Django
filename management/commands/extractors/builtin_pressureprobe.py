import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_pressureprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp DOUBLE PRECISION, utc_logged TIMESTAMP, sensor_vendor TEXT, sensor_name TEXT, sensor_power DOUBLE PRECISION, sensor_type BIGINT, sensor_version BIGINT, sensor_resolution DOUBLE PRECISION, sensor_maximum_range DOUBLE PRECISION);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_pressureprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_pressureprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_pressureprobe(utc_logged);'

CREATE_READING_TABLE_SQL = 'CREATE TABLE builtin_pressureprobe_reading(id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, sensor_timestamp DOUBLE PRECISION, sensor_timestamp_utc TIMESTAMP, event_timestamp DOUBLE PRECISION, event_timestamp_utc TIMESTAMP, normalized_timestamp DOUBLE PRECISION, normalized_timestamp_utc TIMESTAMP, pressure DOUBLE PRECISION, altitude DOUBLE PRECISION, accuracy DOUBLE PRECISION);'
CREATE_READING_USER_ID_INDEX = 'CREATE INDEX ON builtin_pressureprobe_reading(user_id);'
CREATE_READING_READING_ID_INDEX = 'CREATE INDEX ON builtin_pressureprobe_reading(reading_id);'
CREATE_READING_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_pressureprobe_reading(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    
    if probe_table_exists(conn) == False:
        conn.close()
        return False
    
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_pressureprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_pressureprobe\')')
    
    exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return exists

def reading_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_pressureprobe_reading\')')
    
    exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return exists

def insert(connection_str, user_id, reading, check_exists=True):
#    print(json.dumps(reading, indent=2))
    
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    
    if check_exists and probe_table_exists(conn) == False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)
    
    if check_exists and reading_table_exists(conn) == False:
        cursor.execute(CREATE_READING_TABLE_SQL)
        cursor.execute(CREATE_READING_USER_ID_INDEX)
        cursor.execute(CREATE_READING_READING_ID_INDEX)
        cursor.execute(CREATE_READING_UTC_LOGGED_INDEX)
        
    conn.commit()
    
    reading_cmd = 'INSERT INTO builtin_pressureprobe(user_id, ' + \
                                                     'guid, ' + \
                                                     'timestamp, ' + \
                                                     'utc_logged, ' + \
                                                     'sensor_vendor, ' + \
                                                     'sensor_name, ' + \
                                                     'sensor_power, ' + \
                                                     'sensor_type, ' + \
                                                     'sensor_version, ' + \
                                                     'sensor_resolution, ' + \
                                                     'sensor_maximum_range) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 reading['SENSOR']['VENDOR'], \
                                 reading['SENSOR']['NAME'], \
                                 reading['SENSOR']['POWER'], \
                                 reading['SENSOR']['TYPE'], \
                                 reading['SENSOR']['VERSION'], \
                                 reading['SENSOR']['RESOLUTION'], \
                                 reading['SENSOR']['MAXIMUM_RANGE']))
    
    for row in cursor.fetchall():
        reading_id = row[0]
        
        readings_len = len(reading['EVENT_TIMESTAMP'])
        
        has_sensor = ('SENSOR_TIMESTAMP' in reading)
        has_normalized = ('NORMALIZED_TIMESTAMP' in reading)
        
        reading_cursor = conn.cursor()
        
        for i in range(0, readings_len):
            reading_cmd = 'INSERT INTO builtin_pressureprobe_reading(user_id, ' + \
                                                                     'reading_id, ' + \
                                                                     'utc_logged, ' + \
                                                                     'event_timestamp, ' + \
                                                                     'event_timestamp_utc, ' + \
                                                                     'sensor_timestamp, ' + \
                                                                     'sensor_timestamp_utc, ' + \
                                                                     'normalized_timestamp, ' + \
                                                                     'normalized_timestamp_utc, ' + \
                                                                     'pressure, ' + \
                                                                     'altitude, ' + \
                                                                     'accuracy) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
                                                                     
            values = [ user_id, reading_id, datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc) ]
            
            values.append(reading['EVENT_TIMESTAMP'][i])
            values.append(datetime.datetime.fromtimestamp(reading['EVENT_TIMESTAMP'][i], tz=pytz.utc))
            
            if has_sensor:
                values.append(reading['SENSOR_TIMESTAMP'][i])
                
                try:
                    values.append(datetime.datetime.fromtimestamp((reading['SENSOR_TIMESTAMP'][i] / 1000), tz=pytz.utc))
                except ValueError:
                    values.append(datetime.datetime.fromtimestamp((reading['SENSOR_TIMESTAMP'][i] / (1000 * 1000 * 1000)), tz=pytz.utc))
            else:
                values.append(None)
                values.append(None)

            if has_normalized:
                values.append(reading['NORMALIZED_TIMESTAMP'][i])
                values.append(datetime.datetime.fromtimestamp(reading['NORMALIZED_TIMESTAMP'][i], tz=pytz.utc))
            else:
                values.append(None)
                values.append(None)
            
            values.append(reading['PRESSURE'][i])
            values.append(reading['ALTITUDE'][i])
            values.append(reading['ACCURACY'][i])
            
            reading_cursor.execute(reading_cmd, values)

    conn.commit()
        
    cursor.close()
    conn.close()

import datetime
import json
import msgpack
import psycopg2
import pytz

from purple_robot_app.models import PurpleRobotReading

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE sensors_lightsensorprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp DOUBLE PRECISION, utc_logged TIMESTAMP, sensor_vendor TEXT, sensor_name TEXT, sensor_power DOUBLE PRECISION, sensor_type BIGINT, sensor_version BIGINT, sensor_resolution DOUBLE PRECISION, sensor_maximum_range DOUBLE PRECISION);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON sensors_lightsensorprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON sensors_lightsensorprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON sensors_lightsensorprobe(utc_logged);'

CREATE_READING_TABLE_SQL = 'CREATE TABLE sensors_lightsensorprobe_reading(id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, sensor_timestamp DOUBLE PRECISION, sensor_timestamp_utc TIMESTAMP, event_timestamp DOUBLE PRECISION, event_timestamp_utc TIMESTAMP, normalized_timestamp DOUBLE PRECISION, normalized_timestamp_utc TIMESTAMP, lux DOUBLE PRECISION, accuracy DOUBLE PRECISION);'
CREATE_READING_USER_ID_INDEX = 'CREATE INDEX ON sensors_lightsensorprobe_reading(user_id);'
CREATE_READING_READING_ID_INDEX = 'CREATE INDEX ON sensors_lightsensorprobe_reading(reading_id);'
CREATE_READING_UTC_LOGGED_INDEX = 'CREATE INDEX ON sensors_lightsensorprobe_reading(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()

    if probe_table_exists(conn) == False:
        conn.close()
        return False

    if reading_table_exists(conn) == False:
        conn.close()
        return False

    cursor.execute('SELECT id FROM sensors_lightsensorprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'sensors_lightsensorprobe\')')
    
    exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return exists

def reading_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'sensors_lightsensorprobe_reading\')')
    
    exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return exists

def insert(connection_str, user_id, reading):
#    print(json.dumps(reading, indent=2))
    
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    
    if probe_table_exists(conn) == False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)
    
    if reading_table_exists(conn) == False:
        cursor.execute(CREATE_READING_TABLE_SQL)
        cursor.execute(CREATE_READING_USER_ID_INDEX)
        cursor.execute(CREATE_READING_READING_ID_INDEX)
        cursor.execute(CREATE_READING_UTC_LOGGED_INDEX)
        
    conn.commit()
    
    reading_cmd = 'INSERT INTO sensors_lightsensorprobe(user_id, ' + \
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
        
        reading_cursor = conn.cursor()

        pr_reading = PurpleRobotReading.objects.filter(guid=reading['GUID']).first()
        
        if pr_reading != None and pr_reading.attachment != None:
            reading_cmd = 'INSERT INTO sensors_lightsensorprobe_reading(user_id, ' + \
                                                                     'reading_id, ' + \
                                                                     'utc_logged, ' + \
                                                                     'event_timestamp, ' + \
                                                                     'event_timestamp_utc, ' + \
                                                                     'sensor_timestamp, ' + \
                                                                     'sensor_timestamp_utc, ' + \
                                                                     'normalized_timestamp, ' + \
                                                                     'normalized_timestamp_utc, ' + \
                                                                     'lux, ' + \
                                                                     'accuracy) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);'
                                                                     
            readings_file = None
            
            try:
                readings_file = pr_reading.attachment
            except ValueError:
                readings_file = None
                
            if readings_file != None:
                try:
                    content = list(msgpack.Unpacker(readings_file))
            
                    if len(content) == 6:
                        time_buffer = content[1]
                        sensor_time_buffer = content[2]
                        normal_time_buffer = content[3]
                        accuracy_buffer = content[4]
                        lux_buffer = content[5]
            
                        for i in range(0, len(time_buffer)):
                            values = [ user_id, reading_id, datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc) ]
                
                            values.append(time_buffer[i])
                            values.append(datetime.datetime.fromtimestamp(time_buffer[i], tz=pytz.utc))
        
                            values.append(sensor_time_buffer[i])
                            try:
                                values.append(datetime.datetime.fromtimestamp((sensor_time_buffer[i] / 1000), tz=pytz.utc))
                            except ValueError:
                                values.append(datetime.datetime.fromtimestamp((sensor_time_buffer[i] / (1000 * 1000 * 1000)), tz=pytz.utc))

                            values.append(normal_time_buffer[i])
                            values.append(datetime.datetime.fromtimestamp(normal_time_buffer[i], tz=pytz.utc))
                            values.append(lux_buffer[i])
                            values.append(accuracy_buffer[i])
        
                            reading_cursor.execute(reading_cmd, values)
                except ValueError:
                    pass

    conn.commit()
        
    cursor.close()
    conn.close()

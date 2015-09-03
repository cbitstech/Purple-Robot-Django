import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_fusedlocationprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, altitude DOUBLE PRECISION, accuracy DOUBLE PRECISION, provider TEXT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_fusedlocationprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_fusedlocationprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_fusedlocationprobe(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_fusedlocationprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_fusedlocationprobe\')')
    
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
    
    reading_cmd = 'INSERT INTO builtin_fusedlocationprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'latitude, ' + \
                                                   'longitude, ' + \
                                                   'altitude, ' + \
                                                   'accuracy, ' + \
                                                   'provider) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
                                                   
    latitude = None
    longitude = None
    timestamp = None
    provider = None
    accuracy = None
    
    if 'LATITUDE' in reading:
        latitude = reading['LATITUDE']

    if 'LONGITUDE' in reading:
        longitude = reading['LONGITUDE']

    if 'TIMESTAMP' in reading:
        timestamp = reading['TIMESTAMP']
    
    if 'PROVIDER' in reading:
        provider = reading['PROVIDER']

    if 'ACCURACY' in reading:
        accuracy = reading['ACCURACY']
    
    if timestamp != None:
        values = [ user_id, reading['GUID'], timestamp, datetime.datetime.fromtimestamp(timestamp, tz=pytz.utc), latitude, longitude ]
    else:
        values = [ user_id, reading['GUID'], None, None, latitude, longitude ]
    
    if 'ALTITUDE' in reading:
        values.append(reading['ALTITUDE'])
    else:
        values.append(None)
    
    values.append(accuracy)
    values.append(provider)
    
    cursor.execute(reading_cmd, values)

    conn.commit()
        
    cursor.close()
    conn.close()

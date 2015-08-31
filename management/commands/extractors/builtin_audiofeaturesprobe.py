import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_audiofeaturesprobe (' + \
    'id SERIAL PRIMARY KEY, ' + \
    'user_id TEXT, ' + \
    'guid TEXT, ' + \
    'timestamp BIGINT, ' + \
    'utc_logged TIMESTAMP, ' + \
    'samples_recorded BIGINT, ' + \
    'sample_rate BIGINT, ' + \
    'sample_buffer_size BIGINT, ' + \
    'power DOUBLE PRECISION, ' + \
    'frequency DOUBLE PRECISION, ' + \
    'normalized_avg_magnitude DOUBLE PRECISION);'

CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_audiofeaturesprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_audiofeaturesprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_audiofeaturesprobe(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_audiofeaturesprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_audiofeaturesprobe\')')
    
    exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return exists

def insert(connection_str, user_id, reading):
#     print(json.dumps(reading, indent=2))
    
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    
    if probe_table_exists(conn) == False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)
    
        
    conn.commit()
    
    reading_cmd = 'INSERT INTO builtin_audiofeaturesprobe(user_id, ' + \
                                                         'guid, ' + \
                                                         'timestamp, ' + \
                                                         'utc_logged, ' + \
                                                         'samples_recorded, ' + \
                                                         'sample_rate, ' + \
                                                         'sample_buffer_size, ' + \
                                                         'power, ' + \
                                                         'frequency, ' + \
                                                         'normalized_avg_magnitude) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    
    data = (user_id, \
            reading['GUID'], \
            reading['TIMESTAMP'], \
            datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
            reading['SAMPLES_RECORDED'], \
            reading['SAMPLE_RATE'], \
            reading['SAMPLE_BUFFER_SIZE'], \
            reading['POWER'], \
            reading['FREQUENCY'], \
            reading['NORMALIZED_AVG_MAGNITUDE'])
    
    cursor.execute(reading_cmd, data)
    
    conn.commit()
        
    cursor.close()
    conn.close()
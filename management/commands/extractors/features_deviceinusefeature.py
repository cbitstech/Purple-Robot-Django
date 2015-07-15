import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE features_deviceinusefeature(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, device_active BOOLEAN);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON features_deviceinusefeature(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON features_deviceinusefeature(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON features_deviceinusefeature(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    
    if probe_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM features_deviceinusefeature WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'features_deviceinusefeature\')')
    
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
    
    reading_cmd = 'INSERT INTO features_deviceinusefeature(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'device_active) VALUES (%s, %s, %s, %s, %s) RETURNING id;'
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 reading['DEVICE_ACTIVE']))
    conn.commit()
        
    cursor.close()
    conn.close()

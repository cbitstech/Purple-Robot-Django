import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_communicationeventprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, name TEXT, number TEXT, communication_type TEXT, communication_direction TEXT, comm_timestamp BIGINT, comm_timestamp_ts TIMESTAMP);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_communicationeventprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_communicationeventprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_communicationeventprobe(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    
    if probe_table_exists(conn) == False:
        conn.close()
        
        return False
        
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_communicationeventprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_communicationeventprobe\')')
    
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
    
    reading_cmd = 'INSERT INTO builtin_communicationeventprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'name, ' + \
                                                   'number, ' + \
                                                   'communication_type, ' + \
                                                   'communication_direction, ' + \
                                                   'comm_timestamp, ' + \
                                                   'comm_timestamp_ts) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'

    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 reading['NAME'], \
                                 reading['NUMBER'], \
                                 reading['COMMUNICATION_TYPE'], \
                                 reading['COMMUNICATION_DIRECTION'], \
                                 reading['COMM_TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp((reading['COMM_TIMESTAMP'] / 1000), tz=pytz.utc)))

    conn.commit()
        
    cursor.close()
    conn.close()

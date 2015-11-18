import datetime
import json
import msgpack
import psycopg2
import pytz

from purple_robot_app.models import PurpleRobotReading

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE media_audiocaptureprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp DOUBLE PRECISION, utc_logged TIMESTAMP, media_content_type TEXT, media_url TEXT, recording_duration BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON media_audiocaptureprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON media_audiocaptureprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON media_audiocaptureprobe(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()

    if probe_table_exists(conn) == False:
        conn.close()
        return False

    cursor.execute('SELECT id FROM media_audiocaptureprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'media_audiocaptureprobe\')')
    
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
        
    conn.commit()
    
    reading_cmd = 'INSERT INTO media_audiocaptureprobe(user_id, ' + \
                                                      'guid, ' + \
                                                      'timestamp, ' + \
                                                      'utc_logged, ' + \
                                                      'media_content_type, ' + \
                                                      'media_url, ' + \
                                                      'recording_duration) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 reading['media_content_type'], \
                                 reading['media_url'], \
                                 reading['RECORDING_DURATION']))
    conn.commit()
        
    cursor.close()
    conn.close()

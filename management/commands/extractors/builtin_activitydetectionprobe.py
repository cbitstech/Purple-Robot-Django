import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_activitydetectionprobe (id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, activity_count BIGINT, most_probable_activity TEXT, most_probable_confidence BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_activitydetectionprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_activitydetectionprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_activitydetectionprobe(utc_logged);'

CREATE_ACTIVITY_TABLE_SQL = 'CREATE TABLE builtin_activitydetectionprobe_activity (id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, activity TEXT, confidence BIGINT);'
CREATE_ACTIVITY_USER_ID_INDEX = 'CREATE INDEX ON builtin_activitydetectionprobe_activity(user_id);'
CREATE_ACTIVITY_READING_ID_INDEX = 'CREATE INDEX ON builtin_activitydetectionprobe_activity(reading_id);'
CREATE_ACTIVITY_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_activitydetectionprobe_activity(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) == False or activity_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_activitydetectionprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_activitydetectionprobe\')')
    
    probe_table_exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return probe_table_exists

def activity_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_activitydetectionprobe_activity\')')
    
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
    
    if check_exists and activity_table_exists(conn) == False:
        cursor.execute(CREATE_ACTIVITY_TABLE_SQL)
        cursor.execute(CREATE_ACTIVITY_USER_ID_INDEX)
        cursor.execute(CREATE_ACTIVITY_READING_ID_INDEX)
        cursor.execute(CREATE_ACTIVITY_UTC_LOGGED_INDEX)
        
    conn.commit()
    
    reading_cmd = 'INSERT INTO builtin_activitydetectionprobe(user_id, guid, timestamp, utc_logged, activity_count, most_probable_activity, most_probable_confidence) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    
    cursor.execute(reading_cmd, (user_id, reading['GUID'], reading['TIMESTAMP'], datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), reading['ACTIVITY_COUNT'], reading['MOST_PROBABLE_ACTIVITY'], reading['MOST_PROBABLE_CONFIDENCE']))
    
    for row in cursor.fetchall():
        reading_id = row[0]
        
        for activity in reading['ACTIVITIES']:
            activity_cmd = 'INSERT INTO builtin_activitydetectionprobe_activity(user_id, reading_id, utc_logged, activity, confidence) VALUES (%s, %s, %s, %s, %s);'
    
            cursor.execute(activity_cmd, (user_id, reading_id, datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), activity['ACTIVITY_TYPE'], activity['ACTIVITY_CONFIDENCE']))
    
    conn.commit()
        
    cursor.close()
    conn.close()

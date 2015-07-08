import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_runningsoftwareprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, running_task_count BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe(utc_logged);'

CREATE_TASK_TABLE_SQL = 'CREATE TABLE builtin_runningsoftwareprobe_runningtask(id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, package_name TEXT, package_category TEXT, task_stack_index BIGINT);'
CREATE_TASK_USER_ID_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe_runningtask(user_id);'
CREATE_TASK_READING_ID_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe_runningtask(reading_id);'
CREATE_TASK_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe_runningtask(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_runningsoftwareprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_runningsoftwareprobe\')')
    
    exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return exists

def task_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_runningsoftwareprobe_runningtask\')')
    
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
    
    if task_table_exists(conn) == False:
        cursor.execute(CREATE_TASK_TABLE_SQL)
        cursor.execute(CREATE_TASK_USER_ID_INDEX)
        cursor.execute(CREATE_TASK_READING_ID_INDEX)
        cursor.execute(CREATE_TASK_UTC_LOGGED_INDEX)
        
    conn.commit()
    
    reading_cmd = 'INSERT INTO builtin_runningsoftwareprobe(user_id, ' + \
                                                           'guid, ' + \
                                                           'timestamp, ' + \
                                                           'utc_logged, ' + \
                                                           'running_task_count) VALUES (%s, %s, %s, %s, %s) RETURNING id;'
    
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 reading['RUNNING_TASK_COUNT']))
    
    for row in cursor.fetchall():
        reading_id = row[0]
        
        task_cursor = conn.cursor()
        
        for task in reading['RUNNING_TASKS']:
            task_cmd = 'INSERT INTO builtin_runningsoftwareprobe_runningtask(user_id, ' + \
                                                                            'reading_id, ' + \
                                                                            'utc_logged, ' + \
                                                                            'package_name, ' + \
                                                                            'package_category, ' + \
                                                                            'task_stack_index) VALUES (%s, %s, %s, %s, %s, %s);'

            task_cursor.execute(task_cmd, (user_id, \
                                           reading_id, 
                                           datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), 
                                           task['PACKAGE_NAME'], 
                                           task['PACKAGE_CATEGORY'], 
                                           task['TASK_STACK_INDEX']))
        task_cursor.close()

    conn.commit()
        
    cursor.close()
    conn.close()

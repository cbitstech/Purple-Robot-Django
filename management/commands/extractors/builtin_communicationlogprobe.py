import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_communicationlogprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, call_total_count BIGINT,  call_incoming_count BIGINT,  call_outgoing_count BIGINT,  call_missed_count BIGINT, recent_caller TEXT, recent_number TEXT, recent_time BIGINT, recent_time_utc TIMESTAMP,  sms_outgoing_count BIGINT,  sms_incoming_count BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_communicationlogprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_communicationlogprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_communicationlogprobe(utc_logged);'

CREATE_CALL_TABLE_SQL = 'CREATE TABLE builtin_communicationlogprobe_call (id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, number_name TEXT, number_label TEXT, call_duration BIGINT, number_type BIGINT, call_timestamp BIGINT, call_timestamp_utc TIMESTAMP);'
CREATE_CALL_USER_ID_INDEX = 'CREATE INDEX ON builtin_communicationlogprobe_call(user_id);'
CREATE_CALL_READING_ID_INDEX = 'CREATE INDEX ON builtin_communicationlogprobe_call(reading_id);'
CREATE_CALL_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_communicationlogprobe_call(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_communicationlogprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_communicationlogprobe\')')
    
    probe_table_exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return probe_table_exists

def call_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_communicationlogprobe_call\')')
    
    activities_table_exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return activities_table_exists

def insert(connection_str, user_id, reading):
#    print(json.dumps(reading, indent=2))
    
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    
    if probe_table_exists(conn) == False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)
    
    if call_table_exists(conn) == False:
        cursor.execute(CREATE_CALL_TABLE_SQL)
        cursor.execute(CREATE_CALL_USER_ID_INDEX)
        cursor.execute(CREATE_CALL_READING_ID_INDEX)
        cursor.execute(CREATE_CALL_UTC_LOGGED_INDEX)
        
    conn.commit()
    
    reading_cmd = 'INSERT INTO builtin_communicationlogprobe(user_id, ' + \
                                                            'guid, ' + \
                                                            'timestamp, ' + \
                                                            'utc_logged, ' + \
                                                            'call_total_count, ' + \
                                                            'call_incoming_count, ' + \
                                                            'call_outgoing_count, ' + \
                                                            'call_missed_count, ' + \
                                                            'recent_caller, ' + \
                                                            'recent_number, ' + \
                                                            'recent_time, ' + \
                                                            'recent_time_utc, ' + \
                                                            'sms_outgoing_count, ' + \
                                                            'sms_incoming_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
                                                            
    recent_caller = None
    recent_number = None
    recent_time = None
    recent_datetime = None
    
    if 'RECENT_CALLER' in reading:
        recent_caller = reading['RECENT_CALLER']
        recent_number = reading['RECENT_NUMBER']
        recent_time = reading['RECENT_TIME']
        recent_datetime = datetime.datetime.fromtimestamp((reading['RECENT_TIME'] / 1000), tz=pytz.utc)
    
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 reading['CALL_TOTAL_COUNT'], \
                                 reading['CALL_INCOMING_COUNT'], \
                                 reading['CALL_OUTGOING_COUNT'], \
                                 reading['CALL_MISSED_COUNT'], \
                                 recent_caller, \
                                 recent_number, \
                                 recent_time, \
                                 recent_datetime, \
                                 reading['SMS_OUTGOING_COUNT'], \
                                 reading['SMS_INCOMING_COUNT']))
    
    for row in cursor.fetchall():
        reading_id = row[0]
        
        for call in reading['PHONE_CALLS']:
            existing_query = 'SELECT id FROM builtin_communicationlogprobe_call WHERE (user_id = %s AND number_name = %s AND call_timestamp = %s);'
            values = (user_id, call['NUMBER_NAME'], call['CALL_TIMESTAMP'])
            
            call_cursor = conn.cursor()
            call_cursor.execute(existing_query, values)
            
            if call_cursor.rowcount == 0:
                call_cmd = 'INSERT INTO builtin_communicationlogprobe_call(user_id, ' + \
                                                                          'reading_id, ' + \
                                                                          'utc_logged, ' + \
                                                                          'number_name, ' + \
                                                                          'number_label, ' + \
                                                                          'call_duration, ' + \
                                                                          'number_type, ' + \
                                                                          'call_timestamp, ' + \
                                                                          'call_timestamp_utc) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);'

                call_cursor.execute(call_cmd, (user_id, \
                                               reading_id, 
                                               datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), 
                                               call['NUMBER_NAME'], 
                                               call['NUMBER_LABEL'], 
                                               call['CALL_DURATION'], 
                                               call['NUMBER_TYPE'], 
                                               call['CALL_TIMESTAMP'], 
                                               datetime.datetime.fromtimestamp((call['CALL_TIMESTAMP'] / 1000), tz=pytz.utc)))

    conn.commit()
        
    cursor.close()
    conn.close()

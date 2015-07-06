import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE features_callhistoryfeature(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, window_size DOUBLE PRECISION, incoming_count DOUBLE PRECISION, outgoing_count DOUBLE PRECISION, total DOUBLE PRECISION, total_duration DOUBLE PRECISION, min_duration DOUBLE PRECISION, max_duration DOUBLE PRECISION, std_deviation DOUBLE PRECISION, avg_duration DOUBLE PRECISION, incoming_ratio DOUBLE PRECISION, ack_ratio DOUBLE PRECISION, new_count DOUBLE PRECISION, ack_count DOUBLE PRECISION, acquiantance_count DOUBLE PRECISION, stranger_count DOUBLE PRECISION, acquiantance_ratio DOUBLE PRECISION);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON features_callhistoryfeature(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON features_callhistoryfeature(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON features_callhistoryfeature(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM features_callhistoryfeature WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'features_callhistoryfeature\')')
    
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
    
    conn.commit()
    
    reading_cmd = 'INSERT INTO features_callhistoryfeature(user_id, ' + \
                                                           'guid, ' + \
                                                           'timestamp, ' + \
                                                           'utc_logged, ' + \
                                                           'window_size, ' + \
                                                           'incoming_count, ' + \
                                                           'outgoing_count, ' + \
                                                           'total, ' + \
                                                           'total_duration, ' + \
                                                           'min_duration, ' + \
                                                           'max_duration, ' + \
                                                           'std_deviation, ' + \
                                                           'avg_duration, ' + \
                                                           'incoming_ratio, ' + \
                                                           'ack_ratio, ' + \
                                                           'new_count, ' + \
                                                           'ack_count, ' + \
                                                           'acquiantance_count, ' + \
                                                           'stranger_count, ' + \
                                                           'acquiantance_ratio) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
                                                           
                                            
    for window in reading['WINDOWS']:
        cursor.execute(reading_cmd, (user_id, \
                                     reading['GUID'], 
                                     reading['TIMESTAMP'], 
                                     datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), 
                                     window['WINDOW_SIZE'], 
                                     window['INCOMING_COUNT'], 
                                     window['OUTGOING_COUNT'], 
                                     window['TOTAL'], 
                                     window['TOTAL_DURATION'], 
                                     window['MIN_DURATION'], 
                                     window['MAX_DURATION'], 
                                     window['STD_DEVIATION'], 
                                     window['AVG_DURATION'], 
                                     window['INCOMING_RATIO'], 
                                     window['ACK_RATIO'], 
                                     window['NEW_COUNT'], 
                                     window['ACK_COUNT'], 
                                     window['ACQUIANTANCE_COUNT'], 
                                     window['STRANGER_COUNT'], 
                                     window['ACQUAINTANCE_RATIO']))

    conn.commit()
        
    cursor.close()
    conn.close()

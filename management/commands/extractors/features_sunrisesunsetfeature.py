import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE features_sunrisesunsetfeature(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, latitude DOUBLE PRECISION, longitude DOUBLE PRECISION, sunrise BIGINT, sunset BIGINT, day_duration BIGINT, sunrise_distance BIGINT, sunset_distance BIGINT, is_day BOOLEAN);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON features_sunrisesunsetfeature(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON features_sunrisesunsetfeature(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON features_sunrisesunsetfeature(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    
    if probe_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM features_sunrisesunsetfeature WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'features_sunrisesunsetfeature\')')
    
    probe_table_exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return probe_table_exists

def insert(connection_str, user_id, reading):
#    print('USER: '+ user_id)
#    print(json.dumps(reading, indent=2))
    
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()
    
    if probe_table_exists(conn) == False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)
    
    conn.commit()
    
    reading_cmd = 'INSERT INTO features_sunrisesunsetfeature(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'latitude, ' + \
                                                   'longitude, ' + \
                                                   'sunrise, ' + \
                                                   'sunset, ' + \
                                                   'day_duration, ' + \
                                                   'sunrise_distance, ' + \
                                                   'sunset_distance, ' + \
                                                   'is_day) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 reading['LATITUDE'], \
                                 reading['LONGITUDE'], \
                                 reading['SUNRISE'], \
                                 reading['SUNSET'], \
                                 reading['DAY_DURATION'], \
                                 reading['SUNRISE_DISTANCE'], \
                                 reading['SUNSET_DISTANCE'], \
                                 reading['IS_DAY']))
    conn.commit()
        
    cursor.close()
    conn.close()

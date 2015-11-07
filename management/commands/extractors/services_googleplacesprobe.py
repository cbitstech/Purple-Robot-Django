import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE services_googleplacesprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, most_likely_place_id TEXT, most_likely_place TEXT, most_likely_place_likelihood DOUBLE PRECISION, places_json TEXT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON services_googleplacesprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON services_googleplacesprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON services_googleplacesprobe(utc_logged);'

def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)
    
    if probe_table_exists(conn) == False:
        conn.close()
        return False

    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM services_googleplacesprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))
    
    exists = (cursor.rowcount > 0)
    
    cursor.close()
    conn.close()
    
    return exists

def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'services_googleplacesprobe\')')
    
    probe_table_exists = (cursor.rowcount > 0)
            
    cursor.close()
    
    return probe_table_exists

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
    
    places_only = {}
    
    for k,v in reading.iteritems():
        if k != 'MOST_LIKELY_PLACE_ID' and k != 'MOST_LIKELY_PLACE' and k != 'MOST_LIKELY_PLACE_LIKELIHOOD' and k != 'GUID' and k != 'TIMESTAMP' and k != 'PROBE':
            places_only[k] = v
    
    reading_cmd = 'INSERT INTO services_googleplacesprobe(user_id, ' + \
                                                  'guid, ' + \
                                                  'timestamp, ' + \
                                                  'utc_logged, ' + \
                                                  'most_likely_place_id, ' + \
                                                  'most_likely_place, ' + \
                                                  'most_likely_place_likelihood, ' + \
                                                  'places_json) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    
    most_likely_id = None
    
    if 'MOST_LIKELY_PLACE_ID' in reading:
    	most_likely_id = reading['MOST_LIKELY_PLACE_ID']

    most_likely_place = None
    
    if 'MOST_LIKELY_PLACE' in reading:
    	most_likely_place = reading['MOST_LIKELY_PLACE']

    most_likely_likelihood = None
    
    if 'MOST_LIKELY_PLACE_LIKELIHOOD' in reading:
    	most_likely_likelihood = reading['MOST_LIKELY_PLACE_LIKELIHOOD']
    	
    cursor.execute(reading_cmd, (user_id, \
                                 reading['GUID'], \
                                 reading['TIMESTAMP'], \
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), \
                                 most_likely_id, \
                                 most_likely_place, \
                                 most_likely_likelihood, \
                                 json.dumps(places_only)))
    conn.commit()
        
    cursor.close()
    conn.close()

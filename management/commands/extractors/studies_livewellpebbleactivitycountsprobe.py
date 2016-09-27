# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE studies_livewellpebbleactivitycountsprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, diff_means DOUBLE PRECISION, battery_level DOUBLE PRECISION, charging BOOLEAN, firmware_version TEXT, num_samples BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON studies_livewellpebbleactivitycountsprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON studies_livewellpebbleactivitycountsprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON studies_livewellpebbleactivitycountsprobe(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM studies_livewellpebbleactivitycountsprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'studies_livewellpebbleactivitycountsprobe\')')

    table_exists = (cursor.rowcount > 0)

    cursor.close()

    return table_exists


def insert(connection_str, user_id, reading, check_exists=True):
    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()

    if check_exists and probe_table_exists(conn) is False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)

    conn.commit()

    reading_cmd = 'INSERT INTO studies_livewellpebbleactivitycountsprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'diff_means, ' + \
                                                   'battery_level, ' + \
                                                   'charging, ' + \
                                                   'firmware_version, ' + \
                                                   'num_samples) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
                                                   
    firmware = None
    
    if 'FIRMWARE_VERSION' in reading:
        firmware = reading['FIRMWARE_VERSION']
        
    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 reading['BUNDLE_DIFF_MEANS'],
                                 reading['BUNDLE_BATTERY_LEVEL'],
                                 reading['BUNDLE_IS_CHARGING'],
                                 firmware,
                                 reading['BUNDLE_NUM_SAMPLES']))

    conn.commit()

    cursor.close()
    conn.close()

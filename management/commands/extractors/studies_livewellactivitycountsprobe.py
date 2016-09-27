# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE studies_livewellactivitycountsprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, sensor_vendor TEXT, sensor_name TEXT, sensor_power DOUBLE PRECISION, sensor_resolution DOUBLE PRECISION, sensor_version BIGINT, sensor_type BIGINT, sensor_maximum_range DOUBLE PRECISION, duration DOUBLE PRECISION, x_delta DOUBLE PRECISION, y_delta DOUBLE PRECISION, z_delta DOUBLE PRECISION, all_delta DOUBLE PRECISION, num_samples DOUBLE PRECISION);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON studies_livewellactivitycountsprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON studies_livewellactivitycountsprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON studies_livewellactivitycountsprobe(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM studies_livewellactivitycountsprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'studies_livewellactivitycountsprobe\')')

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

    reading_cmd = 'INSERT INTO studies_livewellactivitycountsprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'sensor_vendor, ' + \
                                                   'sensor_name, ' + \
                                                   'sensor_power, ' + \
                                                   'sensor_resolution, ' + \
                                                   'sensor_version, ' + \
                                                   'sensor_type, ' + \
                                                   'sensor_maximum_range, ' + \
                                                   'duration, ' + \
                                                   'x_delta, ' + \
                                                   'y_delta, ' + \
                                                   'z_delta, ' + \
                                                   'all_delta, ' + \
                                                   'num_samples) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 reading['SENSOR']['VENDOR'],
                                 reading['SENSOR']['NAME'],
                                 reading['SENSOR']['POWER'],
                                 reading['SENSOR']['RESOLUTION'],
                                 reading['SENSOR']['VERSION'],
                                 reading['SENSOR']['TYPE'],
                                 reading['SENSOR']['MAXIMUM_RANGE'],
                                 reading['BUNDLE_DURATION'],
                                 reading['BUNDLE_X_DELTA'],
                                 reading['BUNDLE_Y_DELTA'],
                                 reading['BUNDLE_Z_DELTA'],
                                 reading['BUNDLE_ALL_DELTA'],
                                 reading['BUNDLE_NUM_SAMPLES']))

    conn.commit()

    cursor.close()
    conn.close()

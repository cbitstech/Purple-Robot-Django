# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE features_weatherundergroundfeature(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, weather TEXT, location TEXT, station_id TEXT, obs_timestamp BIGINT, obs_logged TIMESTAMP, temperature DOUBLE PRECISION, pressure DOUBLE PRECISION, pressure_trend TEXT, wind_speed DOUBLE PRECISION, gust_speed DOUBLE PRECISION, wind_degrees DOUBLE PRECISION, dewpoint DOUBLE PRECISION, visibility DOUBLE PRECISION, wind_dir TEXT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON features_weatherundergroundfeature(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON features_weatherundergroundfeature(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON features_weatherundergroundfeature(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM features_weatherundergroundfeature WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'features_weatherundergroundfeature\')')

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

    reading_cmd = 'INSERT INTO features_weatherundergroundfeature(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'weather, ' + \
                                                   'location, ' + \
                                                   'station_id, ' + \
                                                   'obs_timestamp, ' + \
                                                   'obs_logged, ' + \
                                                   'temperature, ' + \
                                                   'pressure, ' + \
                                                   'pressure_trend, ' + \
                                                   'wind_speed, ' + \
                                                   'gust_speed, ' + \
                                                   'wind_degrees, ' + \
                                                   'dewpoint, ' + \
                                                   'visibility, ' + \
                                                   'wind_dir) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'

    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 reading['WEATHER'],
                                 reading['LOCATION'],
                                 reading['STATION_ID'],
                                 reading['OBS_TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['OBS_TIMESTAMP'], tz=pytz.utc),
                                 reading['TEMPERATURE'],
                                 reading['PRESSURE'],
                                 reading['PRESSURE_TREND'],
                                 reading['WIND_SPEED'],
                                 reading['GUST_SPEED'],
                                 reading['WIND_DEGREES'],
                                 reading['DEWPOINT'],
                                 reading['VISIBILITY'],
                                 reading['WIND_DIR']))
    conn.commit()

    cursor.close()
    conn.close()

# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_softwareinformationprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, sdk_int BIGINT, release TEXT, incremental TEXT, codename TEXT, installed_app_count BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_softwareinformationprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_softwareinformationprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_softwareinformationprobe(utc_logged);'

CREATE_APP_TABLE_SQL = 'CREATE TABLE builtin_softwareinformationprobe_app(id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, name TEXT, package TEXT);'
CREATE_APP_USER_ID_INDEX = 'CREATE INDEX ON builtin_softwareinformationprobe_app(user_id);'
CREATE_APP_READING_ID_INDEX = 'CREATE INDEX ON builtin_softwareinformationprobe_app(reading_id);'
CREATE_APP_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_softwareinformationprobe_app(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_softwareinformationprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_softwareinformationprobe\')')

    table_exists = (cursor.rowcount > 0)

    cursor.close()

    return table_exists


def app_point_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_softwareinformationprobe_app\')')

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

    if check_exists and app_point_table_exists(conn) is False:
        cursor.execute(CREATE_APP_TABLE_SQL)
        cursor.execute(CREATE_APP_USER_ID_INDEX)
        cursor.execute(CREATE_APP_READING_ID_INDEX)
        cursor.execute(CREATE_APP_UTC_LOGGED_INDEX)

    conn.commit()

    reading_cmd = 'INSERT INTO builtin_softwareinformationprobe(user_id, ' + \
                                                            'guid, ' + \
                                                            'timestamp, ' + \
                                                            'utc_logged, ' + \
                                                            'sdk_int, ' + \
                                                            'release, ' + \
                                                            'incremental, ' + \
                                                            'codename, ' + \
                                                            'installed_app_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 reading['SDK_INT'],
                                 reading['RELEASE'],
                                 reading['INCREMENTAL'],
                                 reading['CODENAME'],
                                 reading['INSTALLED_APP_COUNT']))

    for row in cursor.fetchall():
        reading_id = row[0]

        app_cursor = conn.cursor()

        for app in reading['INSTALLED_APPS']:
            app_cmd = 'INSERT INTO builtin_softwareinformationprobe_app(user_id, ' + \
                                                                       'reading_id, ' + \
                                                                       'utc_logged, ' + \
                                                                       'name, ' + \
                                                                       'package) VALUES (%s, %s, %s, %s, %s);'

            app_cursor.execute(app_cmd, (user_id,
                                         reading_id,
                                         datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                         app['APP_NAME'],
                                         app['PACKAGE_NAME']))
        app_cursor.close()

    conn.commit()

    cursor.close()
    conn.close()

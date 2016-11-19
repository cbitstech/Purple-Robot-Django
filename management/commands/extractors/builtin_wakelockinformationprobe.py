# pylint: disable=line-too-long

import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_wakelockinformationprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, full_locks TEXT, full_count BIGINT, bright_locks TEXT, bright_count BIGINT, dim_locks TEXT, dim_count BIGINT, partial_locks TEXT, partial_count BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_wakelockinformationprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_wakelockinformationprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_wakelockinformationprobe(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_wakelockinformationprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_wakelockinformationprobe\')')

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

    reading_cmd = 'INSERT INTO builtin_wakelockinformationprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'full_locks, ' + \
                                                   'full_count, ' + \
                                                   'bright_locks, ' + \
                                                   'bright_count, ' + \
                                                   'dim_locks, ' + \
                                                   'dim_count, ' + \
                                                   'partial_locks, ' + \
                                                   'partial_count) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 json.dumps(reading['FULL_LOCKS']),
                                 reading['FULL_COUNT'],
                                 json.dumps(reading['BRIGHT_LOCKS']),
                                 reading['BRIGHT_COUNT'],
                                 json.dumps(reading['DIM_LOCKS']),
                                 reading['DIM_COUNT'],
                                 json.dumps(reading['PARTIAL_LOCKS']),
                                 reading['PARTIAL_COUNT']))
    conn.commit()

    cursor.close()
    conn.close()

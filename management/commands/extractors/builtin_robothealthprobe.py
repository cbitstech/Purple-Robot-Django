# pylint: disable=line-too-long

import datetime
import json
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_robothealthprobe (' + \
    'id SERIAL PRIMARY KEY, ' + \
    'user_id TEXT, ' + \
    'guid TEXT, ' + \
    'timestamp BIGINT, ' + \
    'utc_logged TIMESTAMP, ' + \
    'last_boot BIGINT, ' + \
    'last_halt BIGINT, ' + \
    'active_runtime BIGINT, ' + \
    'root_total BIGINT, ' + \
    'root_free BIGINT, ' + \
    'external_total BIGINT, ' + \
    'external_free BIGINT, ' + \
    'pending_size BIGINT, ' + \
    'pending_count BIGINT, ' + \
    'clear_time BIGINT, ' + \
    'time_offset_ms BIGINT, ' + \
    'throughput DOUBLE PRECISION, ' + \
    'cpu_usage DOUBLE PRECISION, ' + \
    'measure_time BIGINT, ' + \
    'app_version_code TEXT, ' + \
    'app_version_name TEXT, ' + \
    'json_config TEXT, ' + \
    'scheme_config TEXT);'

CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_robothealthprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_robothealthprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_robothealthprobe(utc_logged);'

CREATE_WARNING_TABLE_SQL = 'CREATE TABLE builtin_robothealthprobe_warning (' + \
    'id SERIAL PRIMARY KEY, ' + \
    'user_id TEXT, ' + \
    'reading_id BIGINT, ' + \
    'utc_logged TIMESTAMP, ' + \
    'warning TEXT);'

CREATE_WARNING_USER_ID_INDEX = 'CREATE INDEX ON builtin_robothealthprobe_warning(user_id);'
CREATE_WARNING_READING_ID_INDEX = 'CREATE INDEX ON builtin_robothealthprobe_warning(reading_id);'
CREATE_WARNING_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_robothealthprobe_warning(utc_logged);'

CREATE_TRIGGER_TABLE_SQL = 'CREATE TABLE builtin_robothealthprobe_trigger (' + \
    'id SERIAL PRIMARY KEY, ' + \
    'user_id TEXT, ' + \
    'reading_id BIGINT, ' + \
    'utc_logged TIMESTAMP, ' + \
    'trigger_json TEXT);'

CREATE_TRIGGER_USER_ID_INDEX = 'CREATE INDEX ON builtin_robothealthprobe_trigger(user_id);'
CREATE_TRIGGER_READING_ID_INDEX = 'CREATE INDEX ON builtin_robothealthprobe_trigger(reading_id);'
CREATE_TRIGGER_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_robothealthprobe_trigger(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False or warning_table_exists(conn) is False or trigger_table_exists(conn) is False or trigger_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_robothealthprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_robothealthprobe\')')

    table_exists = (cursor.rowcount > 0)

    cursor.close()

    return table_exists


def warning_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_robothealthprobe_warning\')')

    table_exists = (cursor.rowcount > 0)

    cursor.close()

    return table_exists


def trigger_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_robothealthprobe_trigger\')')

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

    if check_exists and warning_table_exists(conn) is False:
        cursor.execute(CREATE_WARNING_TABLE_SQL)
        cursor.execute(CREATE_WARNING_USER_ID_INDEX)
        cursor.execute(CREATE_WARNING_READING_ID_INDEX)
        cursor.execute(CREATE_WARNING_UTC_LOGGED_INDEX)

    if check_exists and trigger_table_exists(conn) is False:
        cursor.execute(CREATE_TRIGGER_TABLE_SQL)
        cursor.execute(CREATE_TRIGGER_USER_ID_INDEX)
        cursor.execute(CREATE_TRIGGER_READING_ID_INDEX)
        cursor.execute(CREATE_TRIGGER_UTC_LOGGED_INDEX)

    conn.commit()

    reading_cmd = 'INSERT INTO builtin_robothealthprobe(user_id, ' + \
                                                       'guid, ' + \
                                                       'timestamp, ' + \
                                                       'utc_logged, ' + \
                                                       'last_boot, ' + \
                                                       'last_halt, ' + \
                                                       'active_runtime, ' + \
                                                       'root_total, ' + \
                                                       'root_free, ' + \
                                                       'external_total, ' + \
                                                       'external_free, ' + \
                                                       'pending_size, ' + \
                                                       'pending_count, ' + \
                                                       'clear_time, ' + \
                                                       'time_offset_ms, ' + \
                                                       'throughput, ' +\
                                                       'cpu_usage, ' + \
                                                       'measure_time, ' + \
                                                       'app_version_code, ' + \
                                                       'app_version_name, ' + \
                                                       'json_config, ' + \
                                                       'scheme_config) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    external_total = None

    if 'EXTERNAL_TOTAL'in reading:
        external_total = reading['EXTERNAL_TOTAL']

    external_free = None

    if 'EXTERNAL_FREE'in reading:
        external_free = reading['EXTERNAL_FREE']

    data = (user_id,
            reading['GUID'],
            reading['TIMESTAMP'],
            datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
            reading['LAST_BOOT'],
            reading['LAST_HALT'],
            reading['ACTIVE_RUNTIME'],
            reading['ROOT_TOTAL'],
            reading['ROOT_FREE'],
            external_total,
            external_free,
            reading['PENDING_SIZE'],
            reading['PENDING_COUNT'],
            reading['CLEAR_TIME'],
            reading['TIME_OFFSET_MS'],
            reading['THROUGHPUT'],
            reading['CPU_USAGE'],
            reading['MEASURE_TIME'],
            str(reading['APP_VERSION_CODE']),
            reading['APP_VERSION_NAME'],
            reading['JSON_CONFIG'],
            reading['SCHEME_CONFIG'])

    cursor.execute(reading_cmd, data)

    for row in cursor.fetchall():
        reading_id = row[0]

        for trigger in reading['TRIGGERS']:
            trigger_cmd = 'INSERT INTO builtin_robothealthprobe_trigger(user_id, reading_id, utc_logged, trigger_json) VALUES (%s, %s, %s, %s);'

            cursor.execute(trigger_cmd, (user_id, reading_id, datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), json.dumps(trigger)))

        if 'CHECK_WARNINGS' in reading:
            for warning in reading['CHECK_WARNINGS']:
                warning_cmd = 'INSERT INTO builtin_robothealthprobe_warning(user_id, reading_id, utc_logged, warning) VALUES (%s, %s, %s, %s);'

                cursor.execute(warning_cmd, (user_id, reading_id, datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc), warning))

    conn.commit()

    cursor.close()
    conn.close()

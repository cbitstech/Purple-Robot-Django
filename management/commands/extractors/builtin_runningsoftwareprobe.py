# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_runningsoftwareprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, running_task_count BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe(utc_logged);'

CREATE_TASK_TABLE_SQL = 'CREATE TABLE builtin_runningsoftwareprobe_runningtask(id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, package_name TEXT, package_category TEXT, task_stack_index BIGINT);'
CREATE_TASK_USER_ID_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe_runningtask(user_id);'
CREATE_TASK_READING_ID_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe_runningtask(reading_id);'
CREATE_TASK_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_runningsoftwareprobe_runningtask(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_runningsoftwareprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_runningsoftwareprobe\')')

    table_exists = (cursor.rowcount > 0)

    cursor.close()

    return table_exists


def task_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_runningsoftwareprobe_runningtask\')')

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

    if check_exists and task_table_exists(conn) is False:
        cursor.execute(CREATE_TASK_TABLE_SQL)
        cursor.execute(CREATE_TASK_USER_ID_INDEX)
        cursor.execute(CREATE_TASK_READING_ID_INDEX)
        cursor.execute(CREATE_TASK_UTC_LOGGED_INDEX)

    conn.commit()

    reading_cmd = 'INSERT INTO builtin_runningsoftwareprobe(user_id, ' + \
                                                           'guid, ' + \
                                                           'timestamp, ' + \
                                                           'utc_logged, ' + \
                                                           'running_task_count) VALUES (%s, %s, %s, %s, %s) RETURNING id;'
    running_count = -1

    if 'RUNNING_TASK_COUNT' in reading:
        running_count = reading['RUNNING_TASK_COUNT']

    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 running_count))

    if 'RUNNING_TASKS' in reading:
        for row in cursor.fetchall():
            reading_id = row[0]

            task_cursor = conn.cursor()

            for task in reading['RUNNING_TASKS']:
                task_cmd = 'INSERT INTO builtin_runningsoftwareprobe_runningtask(user_id, ' + \
                                                                                'reading_id, ' + \
                                                                                'utc_logged, ' + \
                                                                                'package_name, ' + \
                                                                                'package_category, ' + \
                                                                                'task_stack_index) VALUES (%s, %s, %s, %s, %s, %s);'
                task_cursor.execute(task_cmd, (user_id,
                                               reading_id,
                                               datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                               task['PACKAGE_NAME'],
                                               task['PACKAGE_CATEGORY'],
                                               task['TASK_STACK_INDEX']))
            task_cursor.close()

    conn.commit()

    cursor.close()
    conn.close()

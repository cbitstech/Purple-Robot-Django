# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_datecalendarprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, month BIGINT, day_of_year BIGINT, week_of_year BIGINT, week_of_month BIGINT, day_of_month BIGINT, day_of_week_in_month BIGINT, day_of_week BIGINT, hour_of_day BIGINT, minute BIGINT, dst_offset BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_datecalendarprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_datecalendarprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_datecalendarprobe(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_datecalendarprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_datecalendarprobe\')')

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

    reading_cmd = 'INSERT INTO builtin_datecalendarprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'month, ' + \
                                                   'day_of_year, ' + \
                                                   'week_of_year, ' + \
                                                   'week_of_month, ' + \
                                                   'day_of_month, ' + \
                                                   'day_of_week_in_month, ' + \
                                                   'day_of_week, ' + \
                                                   'hour_of_day, ' + \
                                                   'minute, ' + \
                                                   'dst_offset) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 reading['MONTH'],
                                 reading['DAY_OF_YEAR'],
                                 reading['WEEK_OF_YEAR'],
                                 reading['WEEK_OF_MONTH'],
                                 reading['DAY_OF_MONTH'],
                                 reading['DAY_OF_WEEK_IN_MONTH'],
                                 reading['DAY_OF_WEEK'],
                                 reading['HOUR_OF_DAY'],
                                 reading['MINUTE'],
                                 reading['DST_OFFSET']))
    conn.commit()

    cursor.close()
    conn.close()

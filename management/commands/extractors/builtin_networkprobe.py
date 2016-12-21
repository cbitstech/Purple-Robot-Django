# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_networkprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, hostname TEXT, interface_name TEXT, ip_address TEXT, interface_display TEXT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_networkprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_networkprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_networkprobe(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_networkprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_networkprobe\')')

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

    reading_cmd = 'INSERT INTO builtin_networkprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'hostname, ' + \
                                                   'interface_name, ' + \
                                                   'ip_address, ' + \
                                                   'interface_display) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'

    interface_name = None

    if 'INTERFACE_NAME' in reading:
        interface_name = reading['INTERFACE_NAME']

    ip_address = None

    if 'IP_ADDRESS' in reading:
        ip_address = reading['IP_ADDRESS']

    hostname = None

    if 'HOSTNAME' in reading:
        hostname = reading['HOSTNAME']

    interface_display = None

    if 'INTERFACE_DISPLAY' in reading:
        interface_display = reading['INTERFACE_DISPLAY']

    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 hostname,
                                 interface_name,
                                 ip_address,
                                 interface_display))
    conn.commit()

    cursor.close()
    conn.close()

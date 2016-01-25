# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_bluetoothdevicesprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, device_count BIGINT);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_bluetoothdevicesprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_bluetoothdevicesprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_bluetoothdevicesprobe(utc_logged);'

CREATE_DEVICE_TABLE_SQL = 'CREATE TABLE builtin_bluetoothdevicesprobe_device(id SERIAL PRIMARY KEY, user_id TEXT, reading_id BIGINT, utc_logged TIMESTAMP, name TEXT, major_class TEXT, minor_class TEXT, bond_state TEXT, address TEXT);'
CREATE_DEVICE_USER_ID_INDEX = 'CREATE INDEX ON builtin_bluetoothdevicesprobe_device(user_id);'
CREATE_DEVICE_READING_ID_INDEX = 'CREATE INDEX ON builtin_bluetoothdevicesprobe_device(reading_id);'
CREATE_DEVICE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_bluetoothdevicesprobe_device(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False or device_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_bluetoothdevicesprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_bluetoothdevicesprobe\')')

    table_exists = (cursor.rowcount > 0)

    cursor.close()

    return table_exists


def device_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_bluetoothdevicesprobe_device\')')

    table_exists = (cursor.rowcount > 0)

    cursor.close()

    return table_exists


def insert(connection_str, user_id, reading, check_exists=True):
    check_exists = True

    conn = psycopg2.connect(connection_str)
    cursor = conn.cursor()

    if check_exists and probe_table_exists(conn) is False:
        cursor.execute(CREATE_PROBE_TABLE_SQL)
        cursor.execute(CREATE_PROBE_USER_ID_INDEX)
        cursor.execute(CREATE_PROBE_GUID_INDEX)
        cursor.execute(CREATE_PROBE_UTC_LOGGED_INDEX)

    if check_exists and device_table_exists(conn) is False:
        cursor.execute(CREATE_DEVICE_TABLE_SQL)
        cursor.execute(CREATE_DEVICE_USER_ID_INDEX)
        cursor.execute(CREATE_DEVICE_READING_ID_INDEX)
        cursor.execute(CREATE_DEVICE_UTC_LOGGED_INDEX)

    conn.commit()

    reading_cmd = 'INSERT INTO builtin_bluetoothdevicesprobe(user_id, ' + \
                                                            'guid, ' + \
                                                            'timestamp, ' + \
                                                            'utc_logged, ' + \
                                                            'device_count) VALUES (%s, %s, %s, %s, %s) RETURNING id;'
    device_count = None

    if 'DEVICE_COUNT' in reading:
        device_count = reading['DEVICE_COUNT']

    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 device_count))

    for row in cursor.fetchall():
        reading_id = row[0]

        device_cursor = conn.cursor()

        for device in reading['DEVICES']:
            device_cmd = 'INSERT INTO builtin_bluetoothdevicesprobe_device(user_id, ' + \
                                                                          'reading_id, ' + \
                                                                          'utc_logged, ' + \
                                                                          'name, ' + \
                                                                          'major_class, ' + \
                                                                          'minor_class, ' + \
                                                                          'bond_state, ' + \
                                                                          'address) VALUES (%s, %s, %s, %s, %s, %s, %s, %s);'
            major = None
            minor = None
            name = None
            bond = None
            address = None

            if 'DEVICE MAJOR CLASS' in device:
                major = device['DEVICE MAJOR CLASS']

            if 'DEVICE MINOR CLASS' in device:
                minor = device['DEVICE MINOR CLASS']

            if 'BLUETOOTH_NAME' in device:
                name = device['BLUETOOTH_NAME']

            if 'BOND_STATE' in device:
                bond = device['BOND_STATE']

            if 'BLUETOOTH_ADDRESS' in device:
                address = device['BLUETOOTH_ADDRESS']

            device_cursor.execute(device_cmd, (user_id,
                                               reading_id,
                                               datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                               name,
                                               major,
                                               minor,
                                               bond,
                                               address))
    conn.commit()

    cursor.close()
    conn.close()

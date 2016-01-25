# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_telephonyprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, network_country_iso TEXT, phone_type TEXT, sim_state TEXT, cid TEXT, network_operator TEXT, has_icc_card BOOLEAN, sim_country_iso TEXT, lac BIGINT, call_state BIGINT, gsm_signal_state DOUBLE PRECISION, sim_operator_name TEXT, psc BIGINT, device_software_version TEXT, gsm_error_rate DOUBLE PRECISION, network_type TEXT, service_state TEXT, is_forwarding BOOLEAN);'
CREATE_PROBE_USER_ID_INDEX = 'CREATE INDEX ON builtin_telephonyprobe(user_id);'
CREATE_PROBE_GUID_INDEX = 'CREATE INDEX ON builtin_telephonyprobe(guid);'
CREATE_PROBE_UTC_LOGGED_INDEX = 'CREATE INDEX ON builtin_telephonyprobe(utc_logged);'


def exists(connection_str, user_id, reading):
    conn = psycopg2.connect(connection_str)

    if probe_table_exists(conn) is False:
        conn.close()
        return False

    cursor = conn.cursor()

    cursor.execute('SELECT id FROM builtin_telephonyprobe WHERE (user_id = %s AND guid = %s);', (user_id, reading['GUID']))

    row_exists = (cursor.rowcount > 0)

    cursor.close()
    conn.close()

    return row_exists


def probe_table_exists(conn):
    cursor = conn.cursor()
    cursor.execute('SELECT table_name FROM information_schema.tables WHERE (table_schema = \'public\' AND table_name = \'builtin_telephonyprobe\')')

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

    reading_cmd = 'INSERT INTO builtin_telephonyprobe(user_id, ' + \
                                                   'guid, ' + \
                                                   'timestamp, ' + \
                                                   'utc_logged, ' + \
                                                   'network_country_iso, ' + \
                                                   'phone_type, ' + \
                                                   'sim_state, ' + \
                                                   'cid, ' + \
                                                   'network_operator, ' + \
                                                   'has_icc_card, ' + \
                                                   'sim_country_iso, ' + \
                                                   'lac, ' + \
                                                   'call_state, ' + \
                                                   'gsm_signal_state, ' + \
                                                   'sim_operator_name, ' + \
                                                   'psc, ' + \
                                                   'device_software_version, ' + \
                                                   'gsm_error_rate, ' + \
                                                   'network_type, ' + \
                                                   'service_state, ' + \
                                                   'is_forwarding) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
    cid = None
    if 'cid' in reading:
        cid = reading['cid']

    psc = None
    if 'psc' in reading:
        psc = reading['psc']

    lac = None
    if 'lac' in reading:
        lac = reading['lac']

    device_software_version = None
    if 'DEVICE_SOFTWARE_VERSION' in reading:
        device_software_version = reading['DEVICE_SOFTWARE_VERSION']

    gsm_strength = None
    if 'GSM_SIGNAL_STRENGTH' in reading:
        gsm_strength = reading['GSM_SIGNAL_STRENGTH']

    gsm_error = None
    if 'GSM_ERROR_RATE' in reading:
        gsm_error = reading['GSM_ERROR_RATE']

    cursor.execute(reading_cmd, (user_id,
                                 reading['GUID'],
                                 reading['TIMESTAMP'],
                                 datetime.datetime.fromtimestamp(reading['TIMESTAMP'], tz=pytz.utc),
                                 reading['NETWORK_COUNTRY_ISO'],
                                 reading['PHONE_TYPE'],
                                 reading['SIM_STATE'],
                                 cid,
                                 reading['NETWORK_OPERATOR'],
                                 reading['HAS_ICC_CARD'],
                                 reading['SIM_COUNTRY_ISO'],
                                 lac,
                                 reading['CALL_STATE'],
                                 gsm_strength,
                                 reading['SIM_OPERATOR_NAME'],
                                 psc,
                                 device_software_version,
                                 gsm_error,
                                 reading['NETWORK_TYPE'],
                                 reading['SERVICE_STATE'],
                                 reading['IS_FORWARDING']))
    conn.commit()

    cursor.close()
    conn.close()

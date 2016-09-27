# pylint: disable=line-too-long

import datetime
import psycopg2
import pytz

CREATE_PROBE_TABLE_SQL = 'CREATE TABLE builtin_telephonyprobe(id SERIAL PRIMARY KEY, user_id TEXT, guid TEXT, timestamp BIGINT, utc_logged TIMESTAMP, network_country_iso TEXT, phone_type TEXT, sim_state TEXT, cid TEXT, network_operator TEXT, has_icc_card BOOLEAN, sim_country_iso TEXT, lac BIGINT, call_state BIGINT, gsm_signal_state DOUBLE PRECISION, sim_operator_name TEXT, psc BIGINT, device_software_version TEXT, gsm_error_rate DOUBLE PRECISION, network_type TEXT, service_state TEXT, is_forwarding BOOLEAN, data_plmn TEXT, network_id DOUBLE PRECISION, cdma_ecio DOUBLE PRECISION, cdma_evdo_ecio DOUBLE PRECISION, cdma_system_id DOUBLE PRECISION, cdma_evdo_snr DOUBLE PRECISION, basestation_latitude DOUBLE PRECISION, basestation_longitude DOUBLE PRECISION, cdma_latitude DOUBLE PRECISION, cdma_longitude DOUBLE PRECISION, cdma_network_id DOUBLE PRECISION, cdma_station DOUBLE PRECISION, lte_station_id DOUBLE PRECISION, basestation_id DOUBLE PRECISION, tac DOUBLE PRECISION, system_id DOUBLE PRECISION, cdma_dbm DOUBLE PRECISION, cdma_evdo_dbm DOUBLE PRECISION);'

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
                                                   'is_forwarding, ' + \
                                                   'data_plmn, ' + \
                                                   'network_id, ' + \
                                                   'cdma_ecio, ' + \
                                                   'cdma_evdo_ecio, ' + \
                                                   'cdma_system_id, ' + \
                                                   'cdma_evdo_snr, ' + \
                                                   'basestation_latitude, ' + \
                                                   'basestation_longitude, ' + \
                                                   'cdma_latitude, ' + \
                                                   'cdma_longitude, ' + \
                                                   'cdma_network_id, ' + \
                                                   'cdma_station, ' + \
                                                   'lte_station_id, ' + \
                                                   'basestation_id, ' + \
                                                   'tac, ' + \
                                                   'system_id, ' + \
                                                   'cdma_dbm, ' + \
                                                   'cdma_evdo_dbm) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id;'
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
        
    data_plmn = None
    if 'mDataPlmn' in reading:
        data_plmn = reading['mDataPlmn']
    
    network_id = None
    if 'networkId' in reading:
        network_id = reading['networkId']

    cdma_ecio = None
    if 'CDMA_ECIO' in reading:
        cdma_ecio = reading['CDMA_ECIO']

    cdma_evdo_ecio = None
    if 'CDMA_EVDO_ECIO' in reading:
        cdma_evdo_ecio = reading['CDMA_EVDO_ECIO']

    cdma_system_id = None
    if 'CDMA_SYSTEM_ID' in reading:
        cdma_system_id = reading['CDMA_SYSTEM_ID']

    cdma_evdo_snr = None
    if 'CDMA_EVDO_SNR' in reading:
        cdma_evdo_snr = reading['CDMA_EVDO_SNR']

    basestation_latitude = None
    if 'baseStationLatitude' in reading:
        basestation_latitude = reading['baseStationLatitude']

    basestation_longitude = None
    if 'baseStationLongitude' in reading:
        basestation_longitude = reading['baseStationLongitude']

    cdma_latitude = None
    if 'CDMA_LATITUDE' in reading:
        cdma_latitude = reading['CDMA_LATITUDE']

    cdma_longitude = None
    if 'CDMA_LONGITUDE' in reading:
        cdma_longitude = reading['CDMA_LONGITUDE']

    cdma_network_id = None
    if 'CDMA_NETWORK_ID' in reading:
        cdma_network_id = reading['CDMA_NETWORK_ID']

    cdma_station = None
    if 'CDMA_STATION' in reading:
        cdma_station = reading['CDMA_STATION']

    lte_station_id = None
    if 'mLteCellId' in reading:
        lte_station_id = reading['mLteCellId']
        
    basestation_id = None
    if 'baseStationId' in reading:
        basestation_id = reading['baseStationId']
        
    tac = None
    if 'mTac' in reading:
        tac = reading['mTac']
        
    system_id = None
    if 'systemId' in reading:
        system_id = reading['systemId']
        
    cdma_dbm = None
    if 'CDMA_DBM' in reading:
        cdma_dbm = reading['CDMA_DBM']
        
    cdma_evdo_dbm = None
    if 'CDMA_EVDO_DBM' in reading:
        cdma_evdo_dbm = reading['CDMA_EVDO_DBM']

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
                                 reading['IS_FORWARDING'],
                                 data_plmn,
                                 network_id,
                                 cdma_ecio,
                                 cdma_evdo_ecio,
                                 cdma_system_id,
                                 cdma_evdo_snr,
                                 basestation_latitude,
                                 basestation_longitude,
                                 cdma_latitude,
                                 cdma_longitude,
                                 cdma_network_id,
                                 cdma_station,
                                 lte_station_id,
                                 basestation_id,
                                 tac,
                                 system_id,
                                 cdma_dbm,
                                 cdma_evdo_dbm))
                                 
    conn.commit()

    cursor.close()
    conn.close()

import datetime
import json
import psycopg2
import pytz

def exists(connection_str, user_id, reading):
    return False

def insert(connection_str, user_id, reading):
    print(json.dumps(reading, indent=2))

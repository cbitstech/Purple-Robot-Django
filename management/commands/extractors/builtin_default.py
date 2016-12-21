# pylint: disable=line-too-long, unused-argument

import json


def exists(connection_str, user_id, reading, check_exists=True):
    return False


def insert(connection_str, user_id, reading):
    print json.dumps(reading, indent=2)

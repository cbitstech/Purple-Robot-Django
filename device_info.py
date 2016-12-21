# pylint: disable=line-too-long

DEVICE_PROBES = {
    'LGE: LGLS740': {
        'name': 'LG Volt (LGLS740)',
        'missing_probes': [
            'edu.northwestern.cbits.purple_robot_manager.probes.sensors.LightSensorProbe',
        ]
    },
    'LGE: LGL34C': {
        'name': 'Optimus Fuel (LGL34C)',
        'missing_probes': [
            'edu.northwestern.cbits.purple_robot_manager.probes.sensors.LightSensorProbe',
        ]
    },
    'LGE: LGLS660': {
        'name': 'LG Tribute (LGLS660)',
        'missing_probes': [
            'edu.northwestern.cbits.purple_robot_manager.probes.sensors.LightSensorProbe',
        ]
    },
    'LGE: LGL41C': {
        'name': 'LG Ultimate 2 (LGL41C)',
        'missing_probes': [
            'edu.northwestern.cbits.purple_robot_manager.probes.sensors.LightSensorProbe',
        ]
    }
}


def can_sense(manufacturer, model, probe):
    if manufacturer is None or model is None or probe is None:
        return None

    # Until contrary evidence surfaces, assume that all devices have all sensors.

    key = manufacturer + ': ' + model

    if key in DEVICE_PROBES:
        device = DEVICE_PROBES[key]

        if probe in device['missing_probes']:
            return False

    return True

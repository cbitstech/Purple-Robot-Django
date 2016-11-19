# pylint: disable=line-too-long, no-member

import datetime
import json

from django.core.management.base import BaseCommand
from django.utils import timezone

from purple_robot_app.models import PurpleRobotDevice, PurpleRobotReading, my_slugify
from purple_robot_app.management.commands.pr_check_status import log_alert, cancel_alert

HARDWARE_SENSORS = (
    u'edu.northwestern.cbits.purple_robot_manager.probes.builtin.AccelerometerProbe',
    u'edu.northwestern.cbits.purple_robot_manager.probes.builtin.GyroscopeProbe',
    u'edu.northwestern.cbits.purple_robot_manager.probes.builtin.LightProbe',
    u'edu.northwestern.cbits.purple_robot_manager.probes.builtin.PressureProbe',
    u'edu.northwestern.cbits.purple_robot_manager.probes.builtin.ProximityProbe',
    u'edu.northwestern.cbits.purple_robot_manager.probes.sensors.AccelerometerSensorProbe',
    u'edu.northwestern.cbits.purple_robot_manager.probes.sensors.LightSensorProbe',
    # u'edu.northwestern.cbits.purple_robot_manager.probes.builtin.HardwareInformationProbe',
    # u'edu.northwestern.cbits.purple_robot_manager.probes.builtin.SoftwareInformationProbe',
)


class Command(BaseCommand):
    def handle(self, *args, **options):
        for device in PurpleRobotDevice.objects.filter(mute_alerts=False):
            for sensor in HARDWARE_SENSORS:
                last = device.most_recent_reading(sensor)

                if last is not None:
                    hardwares = set()

                    start = timezone.now() - datetime.timedelta(days=3)

                    for reading in PurpleRobotReading.objects.filter(user_id=device.hash_key, probe=sensor, logged__gte=start):
                        payload = json.loads(reading.payload)

                        if 'SENSOR' in payload:
                            hardwares.add(payload['SENSOR']['NAME'])

                    if len(hardwares) < 2:
                        cancel_alert(tags='device_sensor_changed_' + my_slugify(sensor.replace('edu.northwestern.cbits.purple_robot_manager.', '')), user_id=device.hash_key)
                    else:
                        log_alert(message='Multiple hardware sensors observed for ' + sensor.replace('edu.northwestern.cbits.purple_robot_manager.', '') + '. Multiple devices are likely sharing the same user identifier.', severity=2, tags='device_sensor_changed_' + my_slugify(sensor.replace('edu.northwestern.cbits.purple_robot_manager.', '')), user_id=device.hash_key)

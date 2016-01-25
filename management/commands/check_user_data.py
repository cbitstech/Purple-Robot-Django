# pylint: disable=line-too-long, no-member

import hashlib

from django.core.management.base import BaseCommand

from purple_robot_app.models import PurpleRobotReading


class Command(BaseCommand):
    def handle(self, *args, **options):
        user_file = open(args[0], 'r')

        for line in user_file:
            user_id = line.strip()

            if len(user_id) > 0:
                # readings = PurpleRobotReading.objects.filter(user_id=user_id)
                # print(user_id + ': ' + str(readings.count()))

                md5_hash = hashlib.md5()
                md5_hash.update(user_id)

                md5_id = md5_hash.hexdigest()

                readings = PurpleRobotReading.objects.filter(user_id=md5_id)

                print user_id + ' (MD5 - ' + md5_id + '): ' + str(readings.count())

                # m = hashlib.sha256()
                # m.update(user_id)
                #
                # sha256_id = m.hexdigest()
                #
                # readings = PurpleRobotReading.objects.filter(user_id=sha256_id)
                #
                # print(user_id + ' (SHA-256 - ' + sha256_id + '): ' + str(readings.count()))

# pylint: disable=line-too-long, no-member

import hashlib

from django.core.management.base import BaseCommand

from ...models import PurpleRobotReading


class Command(BaseCommand):
    def handle(self, *args, **options):
        md5_hash = hashlib.md5()
        md5_hash.update(args[0])

        user_id = md5_hash.hexdigest()

        count = PurpleRobotReading.objects.filter(user_id=user_id).count()

        print 'Readings for ' + args[0] + ': ' + str(count)

        if count == 0:
            md5_hash = hashlib.md5()
            md5_hash.update(args[0].lower())

            user_id = md5_hash.hexdigest()

            count = PurpleRobotReading.objects.filter(user_id=user_id).count()

            print 'Readings for ' + args[0].lower() + ': ' + str(count)

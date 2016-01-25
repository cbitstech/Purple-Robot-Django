# pylint: disable=line-too-long

import hashlib

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    def handle(self, *args, **options):
        md5_hash = hashlib.md5()
        md5_hash.update(args[0])

        user_id = md5_hash.hexdigest()

        print 'Hash for ' + args[0] + ': ' + user_id

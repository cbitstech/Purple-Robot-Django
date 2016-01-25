# pylint: disable=line-too-long, bare-except

import arrow
import datetime
# import msgpack
import os

import cPickle as pickle

from django.conf import settings
from django.utils import timezone


def append_performance_sample(user, item, detail_date=timezone.now(), value=''):
    os.umask(000)

    today = datetime.date.today()

    folder = settings.MEDIA_ROOT + '/purple_robot_analytics/' + user + '/' + today.isoformat()

    if not os.path.exists(folder):
        os.makedirs(folder)

    item_path = folder + '/' + item + '.pickle'

    content = {}

    if os.path.exists(item_path):
        pickle_file = open(item_path, 'rb')

        try:
            content = pickle.load(pickle_file)
        except:
            pass

        pickle_file.close()

    content[detail_date.isoformat()] = value

    pickle.dump(content, open(item_path, 'wb'))


def fetch_performance_samples(user, item, start=None, end=None):
    if end is None:
        end = timezone.now()

    if start is None:
        today = datetime.date.today()
        start = datetime.datetime(today.year, today.month, today.day, 0, 0, 0, 0, tzinfo=end.tzinfo)

    start_date = start.date()
    end_date = end.date()

    samples = []

    while start_date <= end_date:
        item_path = settings.MEDIA_ROOT + '/purple_robot_analytics/' + user + '/' + start_date.isoformat() + '/' + item + '.pickle'

        if os.path.exists(item_path):
            pickle_file = open(item_path, 'rb')

            content = pickle.load(pickle_file)

            for key, value in content.iteritems():
                sample_date = arrow.get(key).datetime

                if sample_date >= start and sample_date <= end:
                    value['sample_date'] = key
                    samples.append(value)

            pickle_file.close()

        start_date += datetime.timedelta(days=1)

    samples.sort(key=lambda sample: sample['sample_date'])

    return samples


def fetch_performance_users():
    items_path = settings.MEDIA_ROOT + '/purple_robot_analytics/'

    users = {}

    for item in os.listdir(items_path):
        if item != 'system':
            dates = os.listdir(items_path + '/' + item)

            last = sorted(dates, reverse=True)[0]

            toks = last.split('-')

            users[item] = datetime.date(int(toks[0]), int(toks[1]), int(toks[2]))

    return users

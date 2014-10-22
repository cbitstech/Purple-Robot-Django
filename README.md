Purple-Robot-Django
===================

This is a self-contained Django app for importing Purple Robot data from mobile devices.

Prerequisites
-------------

```
Django==1.6
South==1.0
argparse==1.2.1
distribute==0.6.24
psycopg2==2.5.4
python-dateutil==2.2
pytz==2014.7
six==1.8.0
wsgiref==0.1.2
```

Installation
------------

Copy this app into your projects file and run `./manage.py migrate` to create the tables for the models.

To extract readings from uploaded payloads, `./manage.py extract_readings` should be set up to run on a frequent basis from mechanisms like **cron**.

Relevant Exposed URLs
---------------------

`http://HOSTNAME/pr/`: The data upload endpoint where Purple Robot sends sensor data payloads.

`http://HOSTNAME/pr/log`: The optional event logging endpoint where Purple Robot logs usage and troubleshooting events.

`http://HOSTNAME/admin`: If the Django admin interface is enabled, uploaded data is available via that interface.

Questions?
----------

If you have any questions or comments, send an e-mail to `c-karr@northwestern.edu`.

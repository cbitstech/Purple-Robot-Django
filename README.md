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

*Example:*

1) Get the Django app.
```
$ cd /var/www/django/purple_robot
$ git clone https://github.com/cbitstech/Purple-Robot-Django
```
  then rename Purple-Robot-Django --> to purple_robot_app
```
$ mv Purple-Robot-Django purple_robot_app
```
2) Install the requirements
```
$ pip install -r requirements.txt
```
3) Using a python virtualenv
```
$ /var/www/django/purple_robot$ source ../venv/bin/activate
(venv)foo@bar:/var/www/django/purple_robot$ ./manage.py migrate
```
4) Include the JS and CSS elements
```
(venv)foo@bar:/var/www/django/purple_robot$ ./manage.py collectstatic
```
check this is working (http://HOSTNAME/pr/export)
5) edit the purple_robot/settings.py, add:
```py
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
ADMINS = (('Admin Name', 'admin@email'),)
URL_PREFIX = 'http://purple_robot.host/'
TEMPLATE_DEBUG = True
ALLOWED_HOSTS = []

#EMAIL settings for your STMP server (email sent with send_mail())
EMAIL_HOST = 'smtp.host.com'
EMAIL_HOST_USER = 'username'
EMAIL_HOST_PASSWORD = 'password'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
```

6) CRON job
A cron job controls a number of background actions through the `purple_robot/minutely_chronograph.sh` script, namely running:
```sh
./manage.py extract_readings,     #extracts readings from JSON payloads
./manage.py run_export_jobs,      #exports data into csv files where requested
./manage.py update_test_reports,  #updates reports
```
minutely_chronograph.sh should be set up to run on a frequent basis from mechanisms like **cron**. This should probably run on the main system cron i.e. `/etc/crontab` as a specified system user rather and set a non-root user.

e.g. /etc/crontab line:
```*  *    * * *   ubuntu  /var/www/django/purple_robot/purple_robot/minutely_chronograph.sh```

Security
--------
* To prevent cached export files being viewed, *do not* enable directory listings in web server serving static content.
* Do not run in debug mode. Configure the `ADMINS` key with your e-mail address and receive error reports via e-mail.

Relevant Exposed URLs
---------------------
To enable support for mirroring content to a flat database, include a connection string in the following format in your `local_settings.py` file:

```PURPLE_ROBOT_FLAT_MIRROR = 'dbname=DATABASE_NAME user=DATABASE_USER password=DATABASE_PASSWORD host=DATABASE_HOST'```

To automatically import data, add to your cron jobs the following command:

```./manage.py extract_into_database```

Relevant Exposed URLs
---------------------

`http://HOSTNAME/pr/`: The data upload endpoint where Purple Robot sends sensor data payloads.

`http://HOSTNAME/pr/log`: The optional event logging endpoint where Purple Robot logs usage and troubleshooting events.

`http://HOSTNAME/admin`: If the Django admin interface is enabled, uploaded data is available via that interface.

`http://HOSTNAME/pr/export`: The data export probe data page page. Dates are in `mm/dd/yyyy` format.

Questions?
----------

If you have any questions or comments, send an e-mail to `c-karr@northwestern.edu`.

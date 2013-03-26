import socket

from dashboard.settings import *

socket.setdefaulttimeout(1)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

SECRET_KEY = 'HELLA_SECRET!'

DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3'}}

TESTSERVER = 'http://testserver'

INSTALLED_APPS += ('django_nose',)

MESSAGE_STORAGE = 'django.contrib.messages.storage.cookie.CookieStorage'

TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'
NOSE_ARGS = ['--nocapture',
             '--nologcapture',
             '--cover-package=windc']

EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

OPENSTACK_ADDRESS = "localhost"
OPENSTACK_ADMIN_TOKEN = "openstack"
OPENSTACK_KEYSTONE_URL = "http://%s:5000/v2.0" % OPENSTACK_ADDRESS
OPENSTACK_KEYSTONE_ADMIN_URL = "http://%s:35357/v2.0" % OPENSTACK_ADDRESS
OPENSTACK_KEYSTONE_DEFAULT_ROLE = "Member"

# Silence logging output during tests.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
            },
        },
    'loggers': {
        'django.db.backends': {
            'handlers': ['null'],
            'propagate': False,
            },
        'horizon': {
            'handlers': ['null'],
            'propagate': False,
        },
        'novaclient': {
            'handlers': ['null'],
            'propagate': False,
        },
        'keystoneclient': {
            'handlers': ['null'],
            'propagate': False,
        },
        'quantum': {
            'handlers': ['null'],
            'propagate': False,
        },
        'nose.plugins.manager': {
            'handlers': ['null'],
            'propagate': False,
        }
    }
}

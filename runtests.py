#!/usr/bin/env python
import os
import sys

import django
from django.conf import settings


def configure_settings():
    settings_dict = {
        'DATABASES': {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        'INSTALLED_APPS': [
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            # Your app
            'modular_engine',
            # Add any other apps your tests depend on
        ],
        'SECRET_KEY': 'dummy-key-for-tests',

        # Add missing settings needed for tests
        # Updated to use test_utils instead of tests
        'ROOT_URLCONF': 'modular_engine.test_utils.urls',
        'MIDDLEWARE': [
            'django.middleware.security.SecurityMiddleware',
            'django.contrib.sessions.middleware.SessionMiddleware',
            'django.middleware.common.CommonMiddleware',
            'django.middleware.csrf.CsrfViewMiddleware',
            'django.contrib.auth.middleware.AuthenticationMiddleware',
            'django.contrib.messages.middleware.MessageMiddleware',
        ],
        'TEMPLATES': [
            {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                'APP_DIRS': True,
                'OPTIONS': {
                    'context_processors': [
                        'django.template.context_processors.debug',
                        'django.template.context_processors.request',
                        'django.contrib.auth.context_processors.auth',
                        'django.contrib.messages.context_processors.messages',
                    ],
                },
            },
        ],
    }

    settings.configure(**settings_dict)


def run_tests():
    configure_settings()
    django.setup()

    # Run migrations before accessing the database
    from django.core.management import call_command
    call_command('migrate')

    # Now run the tests
    from django.test.utils import get_runner
    TestRunner = get_runner(settings)
    test_runner = TestRunner()

    # Specifically target the tests.py file
    failures = test_runner.run_tests(["modular_engine"])
    sys.exit(bool(failures))


if __name__ == "__main__":
    run_tests()

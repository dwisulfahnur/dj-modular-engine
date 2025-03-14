============
django-modular-engine
============

django-modular-engine is a Django app manage modular apps in django project. For each app registered on the modular engine will be able to install/uninstall/upgrade.


Quick start
-----------

1. Add "modular_engine" to your INSTALLED_APPS setting like this::

    INSTALLED_APPS = [
        ...,
        "modular_engine",
    ]

2. Include the polls URLconf in your project urls.py like this::

    path("module/", include("modular_engine.urls")),

3. Run ``python manage.py migrate`` to create the models.

4. Start the development server and visit the admin to create a poll.

5. Visit the ``/module/`` URL to participate in the poll.
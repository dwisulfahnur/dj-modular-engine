DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

INSTALLED_APPS = [
    # Django apps needed for your tests
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",

    # modular_engine
    "modular_engine",
]

SECRET_KEY = "django-insecure-test-key-not-for-production"

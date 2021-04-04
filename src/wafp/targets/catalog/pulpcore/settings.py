SECRET_KEY = "test"
CONTENT_ORIGIN = "http://content-origin:24816"
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "test",
        "USER": "test",
        "PASSWORD": "test",
        "CONN_MAX_AGE": 0,
        "HOST": "db",
    },
}

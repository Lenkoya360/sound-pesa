import django
import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sound_pesa.settings._test')


def pytest_configure(config):
    django.setup()
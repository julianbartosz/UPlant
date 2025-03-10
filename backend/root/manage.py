import django
from django.utils.encoding import force_str
import datetime

import django.utils.encoding
django.utils.encoding.smart_text = force_str
django.utils.encoding.force_text = force_str

# Patch timezone utc attribute missing in Django 4.2 for DRF compatibility
from django.utils import timezone
if not hasattr(timezone, 'utc'):
    timezone.utc = datetime.timezone.utc

# Patch FieldDoesNotExist for DRF compatibility with Django 4.2
import django.core.exceptions
import django.db.models.fields
django.db.models.fields.FieldDoesNotExist = django.core.exceptions.FieldDoesNotExist

# Patch missing parse_header from django.http.multipartparser
import cgi
from django.http import multipartparser
if not hasattr(multipartparser, 'parse_header'):
    multipartparser.parse_header = cgi.parse_header

# Patch missing ugettext_lazy by aliasing it to gettext_lazy
from django.utils.translation import gettext_lazy
import django.utils.translation
django.utils.translation.ugettext_lazy = gettext_lazy

import os
import sys
from dotenv import load_dotenv


def main():

    dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'djangoProject1', '.env')
    load_dotenv(dotenv_path)

    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'djangoProject1.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()

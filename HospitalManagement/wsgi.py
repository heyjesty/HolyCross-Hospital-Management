"""
WSGI config for the HospitalManagement project.

Vercel's Python runtime imports this module and serves the ``app`` callable.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "HospitalManagement.settings")

application = get_wsgi_application()

if os.environ.get("VERCEL"):
    from HospitalManagement.bootstrap import prepare_database

    prepare_database()

app = application

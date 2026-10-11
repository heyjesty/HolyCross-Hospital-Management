"""
Cold-start database preparation for serverless deployments (Vercel).

Runs migrations, seeds demo content into an empty database and makes sure the
administrator account from the environment exists. Safe to run repeatedly.
"""
import logging
import os

from django.core.management import call_command

logger = logging.getLogger(__name__)


def prepare_database():
    try:
        call_command("migrate", interactive=False, verbosity=0)
        call_command("seed_demo", verbosity=0)
        ensure_admin()
    except Exception:  # never take the site down because of setup
        logger.exception("Database preparation failed")


def ensure_admin():
    from django.contrib.auth.models import User

    username = os.environ.get("DJANGO_ADMIN_USERNAME")
    password = os.environ.get("DJANGO_ADMIN_PASSWORD")
    if not username or not password:
        return
    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": os.environ.get("DJANGO_ADMIN_EMAIL", ""), "is_staff": True, "is_superuser": True},
    )
    if created:
        user.set_password(password)
        user.save()

from django.conf import settings


def hospital(request):
    return {
        "HOSPITAL": settings.HOSPITAL,
        "VIDEO_ENABLED": bool(settings.ZEGO_APP_ID and settings.ZEGO_SERVER_SECRET),
        "DEMO_MODE": settings.DEMO_DATABASE,
    }

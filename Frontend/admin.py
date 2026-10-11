from django.contrib import admin

from Frontend.models import Appointmentdb, Blogdb, ContactMessage, Profiledb


@admin.register(Appointmentdb)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ("id", "Name", "DrName", "Date", "Time", "Status")
    list_filter = ("Status", "Department", "Date")
    search_fields = ("Name", "DrName", "Phone", "Email", "Username")


@admin.register(Blogdb)
class StoryAdmin(admin.ModelAdmin):
    list_display = ("Subject", "Name", "Approved", "Created")
    list_filter = ("Approved",)


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("Subject", "Name", "Email", "Read", "Created")
    list_filter = ("Read",)


admin.site.register(Profiledb)
admin.site.site_header = "HolyCross Administration"

from django.contrib import admin

from Backend.models import Deptdb, Doctordb


@admin.register(Deptdb)
class DeptAdmin(admin.ModelAdmin):
    list_display = ("DeptName",)
    search_fields = ("DeptName",)


@admin.register(Doctordb)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ("Name", "Department", "Registrations", "Timing")
    list_filter = ("Department", "Timing")
    search_fields = ("Name", "Registrations")

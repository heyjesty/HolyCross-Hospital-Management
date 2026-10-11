from datetime import time

from django.db import models


class Deptdb(models.Model):
    DeptName = models.CharField(max_length=50, blank=True, null=True)
    Description = models.CharField(max_length=500, blank=True, null=True)
    Image = models.ImageField(upload_to="images", null=True, blank=True)

    class Meta:
        ordering = ["DeptName"]
        verbose_name = "department"

    def __str__(self):
        return f"{self.DeptName}"


class Doctordb(models.Model):
    MORNING, AFTERNOON, EVENING = "MORNING", "AFTERNOON", "EVENING"
    TIMING_CHOICES = [
        (MORNING, "Morning · 9:00 AM – 12:00 PM"),
        (AFTERNOON, "Afternoon · 1:00 PM – 4:00 PM"),
        (EVENING, "Evening · 5:00 PM – 8:00 PM"),
    ]
    TIMING_HOURS = {MORNING: (9, 12), AFTERNOON: (13, 16), EVENING: (17, 20)}
    GENDER_CHOICES = [("MALE", "Male"), ("FEMALE", "Female"), ("OTHER", "Other")]

    Name = models.CharField(max_length=50, null=True, blank=True)
    Department = models.CharField(max_length=50, null=True, blank=True)
    Experience = models.CharField(max_length=50, null=True, blank=True)
    Education = models.CharField(max_length=200, null=True, blank=True)
    Registrations = models.CharField(unique=True, max_length=40, null=True, blank=True)
    Timing = models.CharField(max_length=50, choices=TIMING_CHOICES, null=True, blank=True)
    Language = models.CharField(max_length=100, null=True, blank=True)
    About = models.TextField(null=True, blank=True)
    Gender = models.CharField(max_length=40, choices=GENDER_CHOICES, null=True, blank=True)
    Image = models.ImageField(upload_to="dr-img", null=True, blank=True)

    class Meta:
        ordering = ["Department", "Name"]
        verbose_name = "doctor"

    def __str__(self):
        return f"{self.Name}"

    def time_slots(self):
        """30-minute consultation slots for the doctor's shift."""
        start, end = self.TIMING_HOURS.get(self.Timing, (9, 17))
        return [time(hour, minute) for hour in range(start, end) for minute in (0, 30)]

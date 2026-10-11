from django.db import models


class Blogdb(models.Model):
    """Patient stories / testimonials. Shown publicly once approved by staff."""

    Name = models.CharField(max_length=50, null=True, blank=True)
    Email = models.EmailField(max_length=60, blank=True, null=True)
    Subject = models.CharField(max_length=500, null=True, blank=True)
    Message = models.CharField(max_length=500, null=True, blank=True)
    Approved = models.BooleanField(default=False)
    Created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["-Created", "-id"]
        verbose_name = "patient story"
        verbose_name_plural = "patient stories"

    def __str__(self):
        return f"{self.Subject} — {self.Name}"


class Profiledb(models.Model):
    Username = models.CharField(max_length=50, null=True, blank=True)
    Name = models.CharField(max_length=50, null=True, blank=True)
    Gender = models.CharField(max_length=50, null=True, blank=True)
    Birthday = models.DateField(null=True, blank=True)
    Location = models.CharField(max_length=100, null=True, blank=True)
    Phone = models.CharField(max_length=20, null=True, blank=True)
    Email = models.EmailField(max_length=200, null=True, blank=True)
    Image = models.ImageField(upload_to="ProfileImage", null=True, blank=True)

    class Meta:
        verbose_name = "patient profile"

    def __str__(self):
        return f"{self.Username}"


class Appointmentdb(models.Model):
    PENDING, CONFIRMED, COMPLETED, CANCELLED = "PENDING", "CONFIRMED", "COMPLETED", "CANCELLED"
    STATUS_CHOICES = [
        (PENDING, "Pending"),
        (CONFIRMED, "Confirmed"),
        (COMPLETED, "Completed"),
        (CANCELLED, "Cancelled"),
    ]

    Doctor = models.ForeignKey("Backend.Doctordb", on_delete=models.SET_NULL, null=True, blank=True,
                               related_name="appointments")
    DrName = models.CharField(max_length=50, null=True, blank=True)
    Department = models.CharField(max_length=50, null=True, blank=True)
    Registrations = models.CharField(max_length=40, null=True, blank=True)
    Username = models.CharField(max_length=150, null=True, blank=True)
    Name = models.CharField(max_length=50, null=True, blank=True)
    Email = models.EmailField(max_length=200, null=True, blank=True)
    Phone = models.CharField(max_length=20, null=True, blank=True)
    Date = models.DateField(null=True, blank=True)
    Time = models.TimeField(null=True, blank=True)
    Reason = models.CharField(max_length=300, blank=True, default="")
    Status = models.CharField(max_length=12, choices=STATUS_CHOICES, default=PENDING)
    Created = models.DateTimeField(auto_now_add=True, null=True)

    class Meta:
        ordering = ["-Date", "-Time"]
        verbose_name = "appointment"

    def __str__(self):
        return f"{self.reference} · {self.Name} with {self.DrName}"

    @property
    def reference(self):
        return f"HC-{self.pk:05d}" if self.pk else "HC-NEW"

    @property
    def is_active(self):
        return self.Status in (self.PENDING, self.CONFIRMED)


class ContactMessage(models.Model):
    Name = models.CharField(max_length=80)
    Email = models.EmailField(max_length=200)
    Phone = models.CharField(max_length=20, blank=True)
    Subject = models.CharField(max_length=150)
    Message = models.TextField(max_length=2000)
    Read = models.BooleanField(default=False)
    Created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-Created"]

    def __str__(self):
        return f"{self.Subject} — {self.Name}"

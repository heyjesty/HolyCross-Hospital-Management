import re
from datetime import date, datetime, timedelta

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.utils import timezone

from Frontend.models import Appointmentdb, Blogdb, ContactMessage, Profiledb

PHONE_RE = re.compile(r"^\+?[0-9\s-]{7,15}$")
BOOKING_WINDOW_DAYS = 60


class BootstrapFormMixin:
    """Adds Bootstrap classes to every widget."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            if isinstance(widget, (forms.Select, forms.SelectMultiple)):
                css = "form-select"
            elif isinstance(widget, (forms.CheckboxInput, forms.RadioSelect)):
                css = "form-check-input"
            else:
                css = "form-control"
            widget.attrs["class"] = f"{widget.attrs.get('class', '')} {css}".strip()
            if field.label and "placeholder" not in widget.attrs and css == "form-control":
                widget.attrs["placeholder"] = field.label


def clean_phone_value(value):
    value = (value or "").strip()
    if value and not PHONE_RE.match(value):
        raise forms.ValidationError("Enter a valid phone number (digits, spaces, + or -).")
    return value


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    pass


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    first_name = forms.CharField(label="Full name", max_length=150)
    email = forms.EmailField(label="Email address")

    class Meta:
        model = User
        fields = ("username", "first_name", "email")

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("That username is already taken.")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"].lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email


class AppointmentForm(BootstrapFormMixin, forms.ModelForm):
    Time = forms.ChoiceField(label="Time slot")

    class Meta:
        model = Appointmentdb
        fields = ("Name", "Phone", "Email", "Date", "Time", "Reason")
        labels = {"Name": "Patient name", "Phone": "Phone number", "Email": "Email address",
                  "Date": "Preferred date", "Reason": "Reason for visit (optional)"}
        widgets = {"Date": forms.DateInput(attrs={"type": "date"}),
                   "Reason": forms.TextInput()}

    def __init__(self, *args, doctor=None, **kwargs):
        self.doctor = doctor
        super().__init__(*args, **kwargs)
        self.fields["Name"].required = True
        self.fields["Phone"].required = True
        self.fields["Date"].required = True
        today = timezone.localdate()
        self.fields["Date"].widget.attrs.update(
            min=today.isoformat(), max=(today + timedelta(days=BOOKING_WINDOW_DAYS)).isoformat())
        slots = doctor.time_slots() if doctor else []
        self.fields["Time"].choices = [("", "Select a time")] + [
            (slot.strftime("%H:%M"), slot.strftime("%I:%M %p").lstrip("0")) for slot in slots]

    def clean_Phone(self):
        return clean_phone_value(self.cleaned_data.get("Phone"))

    def clean_Date(self):
        value = self.cleaned_data["Date"]
        today = timezone.localdate()
        if value < today:
            raise forms.ValidationError("Please choose today or a future date.")
        if value > today + timedelta(days=BOOKING_WINDOW_DAYS):
            raise forms.ValidationError(f"Appointments can be booked up to {BOOKING_WINDOW_DAYS} days ahead.")
        return value

    def clean_Time(self):
        return datetime.strptime(self.cleaned_data["Time"], "%H:%M").time()

    def clean(self):
        cleaned = super().clean()
        day, slot = cleaned.get("Date"), cleaned.get("Time")
        if day and slot:
            if day == timezone.localdate() and slot <= timezone.localtime().time():
                self.add_error("Time", "That time has already passed today. Please pick a later slot.")
            elif self.doctor and Appointmentdb.objects.filter(
                    Doctor=self.doctor, Date=day, Time=slot,
                    Status__in=[Appointmentdb.PENDING, Appointmentdb.CONFIRMED]).exists():
                self.add_error("Time", "This slot was just booked. Please choose another time.")
        return cleaned


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Profiledb
        fields = ("Name", "Email", "Phone", "Gender", "Birthday", "Location", "Image")
        labels = {"Name": "Full name", "Birthday": "Date of birth", "Location": "City / Address",
                  "Image": "Profile photo"}
        widgets = {
            "Gender": forms.Select(choices=[("", "Prefer not to say"), ("Male", "Male"),
                                            ("Female", "Female"), ("Other", "Other")]),
            "Birthday": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d"),
            "Image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }

    def clean_Phone(self):
        return clean_phone_value(self.cleaned_data.get("Phone"))

    def clean_Birthday(self):
        value = self.cleaned_data.get("Birthday")
        if value and value > date.today():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        return value

    def clean_Image(self):
        image = self.cleaned_data.get("Image")
        if image and hasattr(image, "size") and image.size > 3 * 1024 * 1024:
            raise forms.ValidationError("Please upload an image smaller than 3 MB.")
        return image


class StoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Blogdb
        fields = ("Name", "Email", "Subject", "Message")
        labels = {"Name": "Your name", "Email": "Email (not published)", "Subject": "Title",
                  "Message": "Your experience"}
        widgets = {"Message": forms.Textarea(attrs={"rows": 4, "maxlength": 500})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("Name", "Subject", "Message"):
            self.fields[name].required = True


class ContactForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ("Name", "Email", "Phone", "Subject", "Message")
        labels = {"Name": "Full name", "Email": "Email address", "Phone": "Phone (optional)"}
        widgets = {"Message": forms.Textarea(attrs={"rows": 5})}

    def clean_Phone(self):
        return clean_phone_value(self.cleaned_data.get("Phone"))

from django import forms

from Backend.models import Deptdb, Doctordb
from Frontend.forms import BootstrapFormMixin

MAX_IMAGE_MB = 3


def validate_image_size(image):
    if image and hasattr(image, "size") and image.size > MAX_IMAGE_MB * 1024 * 1024:
        raise forms.ValidationError(f"Please upload an image smaller than {MAX_IMAGE_MB} MB.")
    return image


class DepartmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Deptdb
        fields = ("DeptName", "Description", "Image")
        labels = {"DeptName": "Department name", "Image": "Icon / image"}
        widgets = {"Description": forms.Textarea(attrs={"rows": 4}),
                   "Image": forms.ClearableFileInput(attrs={"accept": "image/*"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["DeptName"].required = True

    def clean_DeptName(self):
        name = self.cleaned_data["DeptName"].strip()
        duplicates = Deptdb.objects.filter(DeptName__iexact=name).exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise forms.ValidationError("A department with this name already exists.")
        return name

    def clean_Image(self):
        return validate_image_size(self.cleaned_data.get("Image"))


class DoctorForm(BootstrapFormMixin, forms.ModelForm):
    Department = forms.ChoiceField(label="Department")

    class Meta:
        model = Doctordb
        fields = ("Name", "Department", "Registrations", "Experience", "Education", "Language",
                  "Gender", "Timing", "About", "Image")
        labels = {"Name": "Doctor name", "Registrations": "Registration no.",
                  "Language": "Languages spoken", "Timing": "Consultation shift", "Image": "Photo"}
        widgets = {"About": forms.Textarea(attrs={"rows": 5}),
                   "Image": forms.ClearableFileInput(attrs={"accept": "image/*"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["Department"].choices = [("", "Select department")] + [
            (d.DeptName, d.DeptName) for d in Deptdb.objects.all()]
        for name in ("Name", "Registrations", "Timing"):
            self.fields[name].required = True

    def clean_Image(self):
        return validate_image_size(self.cleaned_data.get("Image"))


class DoctorSearchForm(forms.Form):
    search_query = forms.CharField(max_length=100, required=False, label="Search")

from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from Backend.models import Deptdb, Doctordb
from Frontend.models import Appointmentdb, Blogdb, ContactMessage, Profiledb


@override_settings(STORAGES={
    "default": {"BACKEND": "django.core.files.storage.InMemoryStorage"},
    "staticfiles": {"BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"},
})
class PublicSiteTests(TestCase):
    fixtures = ["demo_data"]

    def setUp(self):
        self.doctor = Doctordb.objects.get(Name="Dr. Veena")
        self.patient = User.objects.create_user("patient", "patient@example.com", "Str0ng-pass!")
        self.tomorrow = timezone.localdate() + timedelta(days=1)

    def book(self, **overrides):
        data = {"Name": "Asha", "Phone": "+91 98765 43210", "Email": "asha@example.com",
                "Date": self.tomorrow.isoformat(), "Time": "09:30", "Reason": "Check-up"}
        data.update(overrides)
        return self.client.post(reverse("singledoctor", args=[self.doctor.id]), data)

    def test_public_pages_render(self):
        Deptdb.objects.filter(DeptName="Cardiology").first()
        urls = [reverse("index"), reverse("aboutus"), reverse("service"), reverse("doctor_list"),
                reverse("doctor_list") + "?department=Cardiology&q=veena",
                reverse("singledoctor", args=[self.doctor.id]), reverse("blog"), reverse("contact"),
                reverse("loginfr")]
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_legacy_department_url_redirects(self):
        response = self.client.get("/doctors/Cardiology/")
        self.assertRedirects(response, reverse("doctor_list") + "?department=Cardiology")

    def test_unknown_page_returns_404(self):
        self.assertEqual(self.client.get("/singledoctor/99999/").status_code, 404)

    def test_register_hashes_password_and_logs_in(self):
        response = self.client.post(reverse("registersave"), {
            "first_name": "New Patient", "username": "newpatient", "email": "new@example.com",
            "password1": "Very-secure-123", "password2": "Very-secure-123"})
        self.assertEqual(response.status_code, 302)
        user = User.objects.get(username="newpatient")
        self.assertNotEqual(user.password, "Very-secure-123")
        self.assertTrue(Profiledb.objects.filter(Username="newpatient").exists())
        self.assertEqual(self.client.get(reverse("profile")).status_code, 200)

    def test_login_rejects_bad_password(self):
        response = self.client.post(reverse("userlogin"), {"username": "patient", "password": "wrong"})
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_login_ignores_external_next(self):
        response = self.client.post(reverse("userlogin"), {
            "username": "patient", "password": "Str0ng-pass!", "next": "https://evil.example/"})
        self.assertRedirects(response, reverse("index"))

    def test_booking_requires_login(self):
        response = self.book()
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("loginfr"), response["Location"])
        self.assertFalse(Appointmentdb.objects.exists())

    def test_booking_flow(self):
        self.client.login(username="patient", password="Str0ng-pass!")
        response = self.book()
        appointment = Appointmentdb.objects.get()
        self.assertRedirects(response, reverse("appointment_detail", args=[appointment.pk]))
        self.assertEqual(appointment.Doctor, self.doctor)
        self.assertEqual(appointment.Department, "Cardiology")
        self.assertEqual(appointment.Status, Appointmentdb.PENDING)
        self.assertEqual(appointment.Username, "patient")

        # Slot is now shown as booked and can't be double-booked.
        slots = self.client.get(reverse("doctor_slots", args=[self.doctor.id]), {"date": self.tomorrow.isoformat()})
        self.assertEqual(slots.json(), {"booked": ["09:30"]})
        self.assertEqual(self.book().status_code, 200)
        self.assertEqual(Appointmentdb.objects.count(), 1)

        # Patient can cancel, which frees the slot.
        self.client.post(reverse("appointment_cancel", args=[appointment.pk]))
        appointment.refresh_from_db()
        self.assertEqual(appointment.Status, Appointmentdb.CANCELLED)
        self.assertEqual(self.book().status_code, 302)

    def test_booking_validation(self):
        self.client.login(username="patient", password="Str0ng-pass!")
        yesterday = (timezone.localdate() - timedelta(days=1)).isoformat()
        for bad in ({"Date": yesterday}, {"Time": "23:00"}, {"Phone": "call me"}, {"Name": ""}):
            with self.subTest(bad=bad):
                self.assertEqual(self.book(**bad).status_code, 200)
        self.assertFalse(Appointmentdb.objects.exists())

    def test_patients_cannot_see_each_others_appointments(self):
        other = Appointmentdb.objects.create(Doctor=self.doctor, DrName=self.doctor.Name, Name="Other",
                                             Username="someoneelse", Date=self.tomorrow)
        self.client.login(username="patient", password="Str0ng-pass!")
        self.assertEqual(self.client.get(reverse("appointment_detail", args=[other.pk])).status_code, 404)
        self.client.post(reverse("appointment_cancel", args=[other.pk]))
        other.refresh_from_db()
        self.assertEqual(other.Status, Appointmentdb.PENDING)

    def test_profile_shows_only_own_details(self):
        Profiledb.objects.create(Username="someoneelse", Name="Secret Person")
        self.client.login(username="patient", password="Str0ng-pass!")
        response = self.client.get(reverse("profile"))
        self.assertNotContains(response, "Secret Person")
        response = self.client.post(reverse("profileedit"), {
            "Name": "Pat Ient", "Email": "p@example.com", "Phone": "9876543210", "Gender": "Female",
            "Birthday": "1990-05-01", "Location": "Kochi"})
        self.assertRedirects(response, reverse("profile"))
        self.assertEqual(Profiledb.objects.get(Username="patient").Name, "Pat Ient")

    def test_story_requires_approval(self):
        self.client.post(reverse("blogsave"), {"Name": "Ravi", "Subject": "Great care", "Message": "Thanks!"})
        story = Blogdb.objects.get(Subject="Great care")
        self.assertFalse(story.Approved)
        self.assertNotContains(self.client.get(reverse("blog")), "Great care")

    def test_contact_message_is_stored(self):
        response = self.client.post(reverse("contact"), {
            "Name": "Meera", "Email": "meera@example.com", "Subject": "Visiting hours", "Message": "When?"})
        self.assertRedirects(response, reverse("contact"))
        self.assertTrue(ContactMessage.objects.filter(Subject="Visiting hours").exists())

    def test_logout_requires_post(self):
        self.client.login(username="patient", password="Str0ng-pass!")
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.client.post(reverse("logout"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_media_is_served(self):
        response = self.client.get(Deptdb.objects.first().Image.url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/media/../manage.py").status_code, 404)

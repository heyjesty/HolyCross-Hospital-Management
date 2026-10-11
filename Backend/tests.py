from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from Backend.models import Deptdb, Doctordb
from Frontend.models import Appointmentdb, Blogdb, ContactMessage


class DashboardTests(TestCase):
    fixtures = ["demo_data"]

    def setUp(self):
        self.admin = User.objects.create_superuser("admin", "admin@example.com", "Admin-pass-123")
        self.staff = User.objects.create_user("frontdesk", password="Staff-pass-123", is_staff=True)
        self.patient = User.objects.create_user("patient", password="Patient-pass-123")
        self.doctor = Doctordb.objects.first()
        self.appointment = Appointmentdb.objects.create(
            Doctor=self.doctor, DrName=self.doctor.Name, Name="Asha", Username="patient",
            Date=timezone.localdate(), Time="10:00")

    def test_dashboard_requires_staff(self):
        self.assertRedirects(self.client.get(reverse("indexpage")),
                             reverse("loginpg") + "?next=" + reverse("indexpage"), fetch_redirect_response=False)
        self.client.login(username="patient", password="Patient-pass-123")
        self.assertEqual(self.client.get(reverse("indexpage")).status_code, 302)

    def test_staff_login_rejects_patients(self):
        response = self.client.post(reverse("loginpg"), {"username": "patient", "password": "Patient-pass-123"})
        self.assertContains(response, "does not have staff access")

    def test_all_dashboard_pages_render_for_admin(self):
        self.client.login(username="admin", password="Admin-pass-123")
        ContactMessage.objects.create(Name="A", Email="a@example.com", Subject="Hi", Message="Hello")
        pages = ["indexpage", "appointments", "displaydept", "department", "doctordisplay", "doctorlist",
                 "patients", "inbox", "stories"]
        for name in pages:
            with self.subTest(page=name):
                self.assertEqual(self.client.get(reverse(name)).status_code, 200)
        self.assertEqual(self.client.get(reverse("appointments") + "?when=upcoming&status=PENDING&q=asha").status_code, 200)
        self.assertEqual(self.client.get(reverse("editdept", args=[Deptdb.objects.first().id])).status_code, 200)
        self.assertEqual(self.client.get(reverse("doctoredit", args=[self.doctor.id])).status_code, 200)

    def test_staff_cannot_manage_doctors(self):
        self.client.login(username="frontdesk", password="Staff-pass-123")
        self.assertEqual(self.client.get(reverse("appointments")).status_code, 200)
        self.assertRedirects(self.client.get(reverse("doctorlist")), reverse("indexpage"))
        self.client.post(reverse("doctordel", args=[self.doctor.id]))
        self.assertTrue(Doctordb.objects.filter(id=self.doctor.id).exists())

    def test_update_status(self):
        self.client.login(username="frontdesk", password="Staff-pass-123")
        self.client.post(reverse("appointment_status", args=[self.appointment.id]),
                         {"status": "CONFIRMED", "next": "https://evil.example/"})
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.Status, "CONFIRMED")

    def test_department_crud_and_rename_cascades(self):
        self.client.login(username="admin", password="Admin-pass-123")
        self.client.post(reverse("department"), {"DeptName": "Pediatrics", "Description": "Children's health"})
        dept = Deptdb.objects.get(DeptName="Pediatrics")
        self.assertEqual(self.client.post(reverse("department"), {"DeptName": "pediatrics"}).status_code, 200)

        cardiology = Deptdb.objects.get(DeptName="Cardiology")
        self.client.post(reverse("editdept", args=[cardiology.id]), {"DeptName": "Cardiac Sciences", "Description": ""})
        self.assertFalse(Doctordb.objects.filter(Department="Cardiology").exists())
        self.assertTrue(Doctordb.objects.filter(Department="Cardiac Sciences").exists())

        # Departments with doctors are protected from deletion.
        self.client.post(reverse("deletedept", args=[cardiology.id]))
        self.assertTrue(Deptdb.objects.filter(id=cardiology.id).exists())
        self.client.post(reverse("deletedept", args=[dept.id]))
        self.assertFalse(Deptdb.objects.filter(id=dept.id).exists())

    def test_add_doctor(self):
        self.client.login(username="admin", password="Admin-pass-123")
        response = self.client.post(reverse("doctorlist"), {
            "Name": "Dr. New", "Department": "Cardiology", "Registrations": "2001", "Timing": "EVENING",
            "Experience": "4 Years", "Education": "MBBS", "Language": "English", "Gender": "FEMALE", "About": "Hi"})
        self.assertRedirects(response, reverse("doctordisplay"))
        self.assertEqual(Doctordb.objects.get(Registrations="2001").time_slots()[0].hour, 17)

    def test_story_moderation(self):
        story = Blogdb.objects.create(Name="R", Subject="Pending story", Message="M")
        self.client.login(username="frontdesk", password="Staff-pass-123")
        self.client.post(reverse("story_action", args=[story.id]), {"action": "approve"})
        story.refresh_from_db()
        self.assertTrue(story.Approved)

    def test_logout(self):
        self.client.login(username="admin", password="Admin-pass-123")
        self.assertRedirects(self.client.post(reverse("logoutpg")), reverse("loginpg"))
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_dashboard_week_chart_counts(self):
        Appointmentdb.objects.create(Doctor=self.doctor, Name="B", Date=timezone.localdate() + timedelta(days=2),
                                     Time="10:30")
        self.client.login(username="admin", password="Admin-pass-123")
        week = self.client.get(reverse("indexpage")).context["week_load"]
        self.assertEqual([d["count"] for d in week][:3], [1, 0, 1])

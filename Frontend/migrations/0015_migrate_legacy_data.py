from django.contrib.auth.hashers import make_password
from django.db import migrations


def forwards(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Registerdb = apps.get_model("Frontend", "Registerdb")
    Appointmentdb = apps.get_model("Frontend", "Appointmentdb")
    Blogdb = apps.get_model("Frontend", "Blogdb")
    Doctordb = apps.get_model("Backend", "Doctordb")

    # Legacy patient accounts stored plain-text passwords; move them to Django
    # auth users with properly hashed passwords.
    for legacy in Registerdb.objects.all():
        username = (legacy.Username or "").strip()
        if not username or User.objects.filter(username__iexact=username).exists():
            continue
        User.objects.create(
            username=username,
            email=legacy.Email or "",
            password=make_password(legacy.Password) if legacy.Password else make_password(None),
        )

    for appointment in Appointmentdb.objects.filter(Doctor__isnull=True):
        doctor = (Doctordb.objects.filter(Registrations=appointment.Registrations).first()
                  or Doctordb.objects.filter(Name=appointment.DrName).first())
        if doctor:
            appointment.Doctor = doctor
            appointment.Department = doctor.Department
            appointment.save(update_fields=["Doctor", "Department"])

    # Stories published before moderation existed stay visible.
    Blogdb.objects.update(Approved=True)


class Migration(migrations.Migration):

    dependencies = [
        ("Frontend", "0014_professional_upgrade"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(forwards, migrations.RunPython.noop),
    ]

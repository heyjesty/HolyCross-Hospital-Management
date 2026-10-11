from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("Frontend", "0015_migrate_legacy_data"),
    ]

    operations = [
        migrations.DeleteModel(name="Appoinmentdb"),
        migrations.DeleteModel(name="Registerdb"),
    ]

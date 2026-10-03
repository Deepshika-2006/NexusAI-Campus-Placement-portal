from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0005_recruiter_interview"),
    ]

    operations = [
        migrations.AddField(
            model_name="application",
            name="resume",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="applications",
                to="core.resume",
            ),
        ),
    ]

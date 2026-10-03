from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("core", "0006_application_resume")]

    operations = [
        migrations.CreateModel(
            name="ResumeJobAnalysis",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("ats_score", models.PositiveIntegerField(default=0)),
                ("matched_keywords", models.TextField(blank=True)),
                ("missing_keywords", models.TextField(blank=True)),
                ("strengths", models.TextField(blank=True)),
                ("suggestions", models.TextField(blank=True)),
                ("ai_powered", models.BooleanField(default=False)),
                ("raw_response", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now=True)),
                ("job", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="resume_analyses", to="core.job")),
                ("resume", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="job_analyses", to="core.resume")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddConstraint(
            model_name="resumejobanalysis",
            constraint=models.UniqueConstraint(fields=("resume", "job"), name="unique_resume_job_analysis"),
        ),
    ]

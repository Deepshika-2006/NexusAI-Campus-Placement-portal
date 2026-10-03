from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="profile",
            name="company_name",
            field=models.CharField(blank=True, max_length=160),
        ),
        migrations.AddField(
            model_name="profile",
            name="branch",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="profile",
            name="graduation_year",
            field=models.PositiveIntegerField(default=2027),
        ),
        migrations.AddField(
            model_name="profile",
            name="cgpa",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AddField(
            model_name="profile",
            name="backlogs",
            field=models.PositiveIntegerField(default=0),
        ),
        migrations.AddField(
            model_name="profile",
            name="bio",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="profile",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name="job",
            name="min_cgpa",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AddField(
            model_name="job",
            name="batch",
            field=models.CharField(blank=True, default="2027", max_length=30),
        ),
        migrations.AddField(
            model_name="job",
            name="deadline",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="job",
            name="match_score",
            field=models.PositiveIntegerField(default=80),
        ),
        migrations.AddField(
            model_name="application",
            name="notes",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="application",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name="application",
            name="job",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="core.job"),
        ),
        migrations.AlterField(
            model_name="application",
            name="student",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="applications", to="auth.user"),
        ),
        migrations.CreateModel(
            name="PracticeAttempt",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("practice_type", models.CharField(choices=[("aptitude", "Aptitude"), ("coding", "Coding"), ("assessment", "Assessment"), ("mock_interview", "Mock Interview")], max_length=30)),
                ("score", models.PositiveIntegerField(default=0)),
                ("total", models.PositiveIntegerField(default=0)),
                ("feedback", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(auto_now_add=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="practice_attempts", to="auth.user")),
            ],
            options={"ordering": ["-submitted_at"]},
        ),
        migrations.CreateModel(
            name="InterviewSession",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("prompt", models.CharField(default="Tell me about a technical project you are proud of.", max_length=500)),
                ("answer", models.TextField(blank=True)),
                ("feedback", models.TextField(blank=True)),
                ("score", models.PositiveIntegerField(default=0)),
                ("status", models.CharField(choices=[("active", "Active"), ("completed", "Completed")], default="active", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("student", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interview_sessions", to="auth.user")),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="job",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="resume",
            options={"ordering": ["-created_at"]},
        ),
        migrations.AlterModelOptions(
            name="application",
            options={"ordering": ["-applied_at"]},
        ),
        migrations.AlterUniqueTogether(
            name="application",
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name="application",
            constraint=models.UniqueConstraint(fields=("job", "student"), name="unique_job_student_application"),
        ),
    ]

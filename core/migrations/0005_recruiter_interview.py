# Generated for NexusAI recruiter interview workflow.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_bookmark"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="RecruiterInterview",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("interview_type", models.CharField(choices=[("technical", "Technical Interview"), ("hr", "HR Interview"), ("behavioral", "Behavioral Interview")], default="technical", max_length=20)),
                ("scheduled_at", models.DateTimeField()),
                ("duration_minutes", models.PositiveIntegerField(default=30)),
                ("meeting_link", models.URLField(blank=True)),
                ("question", models.TextField(blank=True, default="Explain one of your projects and your exact technical contribution.")),
                ("candidate_response", models.TextField(blank=True)),
                ("status", models.CharField(choices=[("scheduled", "Scheduled"), ("in_progress", "In Progress"), ("completed", "Completed"), ("cancelled", "Cancelled")], default="scheduled", max_length=20)),
                ("technical_score", models.PositiveIntegerField(default=0)),
                ("communication_score", models.PositiveIntegerField(default=0)),
                ("problem_solving_score", models.PositiveIntegerField(default=0)),
                ("overall_score", models.PositiveIntegerField(default=0)),
                ("recruiter_feedback", models.TextField(blank=True)),
                ("decision", models.CharField(choices=[("pending", "Pending"), ("next_round", "Move to Next Round"), ("selected", "Selected"), ("rejected", "Not Selected")], default="pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("application", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="interviews", to="core.application")),
                ("recruiter", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="recruiter_interviews", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["scheduled_at", "-created_at"]},
        ),
    ]

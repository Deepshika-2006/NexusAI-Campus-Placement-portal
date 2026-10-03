from django.contrib.auth.models import User
from django.db import models


class Profile(models.Model):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("recruiter", "Recruiter"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="student")
    full_name = models.CharField(max_length=120, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    college = models.CharField(max_length=160, blank=True)
    company_name = models.CharField(max_length=160, blank=True)
    branch = models.CharField(max_length=120, blank=True)
    graduation_year = models.PositiveIntegerField(default=2027)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    backlogs = models.PositiveIntegerField(default=0)
    skills = models.TextField(blank=True)
    bio = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.full_name or self.user.username


class Job(models.Model):
    recruiter = models.ForeignKey(User, on_delete=models.CASCADE, related_name="posted_jobs")
    company = models.CharField(max_length=160)
    title = models.CharField(max_length=160)
    location = models.CharField(max_length=120, default="Hyderabad")
    description = models.TextField()
    skills = models.TextField(blank=True)
    eligibility = models.TextField(blank=True)
    salary = models.CharField(max_length=80, blank=True)
    min_cgpa = models.DecimalField(max_digits=4, decimal_places=2, default=0)
    batch = models.CharField(max_length=30, blank=True, default="2027")
    deadline = models.DateField(null=True, blank=True)
    match_score = models.PositiveIntegerField(default=80)
    created_at = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.company} — {self.title}"


class Application(models.Model):
    STATUS = [
        ("applied", "Applied"),
        ("screening", "Screening"),
        ("shortlisted", "Shortlisted"),
        ("interview", "Interview"),
        ("selected", "Selected"),
        ("rejected", "Rejected"),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    resume = models.ForeignKey(
        "Resume",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="applications",
    )
    status = models.CharField(max_length=30, choices=STATUS, default="applied")
    notes = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["job", "student"], name="unique_job_student_application")
        ]
        ordering = ["-applied_at"]

    def __str__(self):
        return f"{self.student.username} → {self.job}"


class Resume(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="resumes")
    file = models.FileField(upload_to="resumes/")
    extracted_text = models.TextField(blank=True)
    ats_score = models.PositiveIntegerField(default=0)
    matched_skills = models.TextField(blank=True)
    missing_skills = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.username} — {self.file.name}"


class ResumeJobAnalysis(models.Model):
    """Job-specific resume screening result. AI-powered when an API key is configured."""
    resume = models.ForeignKey(Resume, on_delete=models.CASCADE, related_name="job_analyses")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="resume_analyses")
    ats_score = models.PositiveIntegerField(default=0)
    matched_keywords = models.TextField(blank=True)
    missing_keywords = models.TextField(blank=True)
    strengths = models.TextField(blank=True)
    suggestions = models.TextField(blank=True)
    ai_powered = models.BooleanField(default=False)
    raw_response = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["resume", "job"], name="unique_resume_job_analysis")
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.resume.student.username} — {self.job.title}"


class PracticeAttempt(models.Model):
    PRACTICE_TYPES = [
        ("aptitude", "Aptitude"),
        ("coding", "Coding"),
        ("assessment", "Assessment"),
        ("mock_interview", "Mock Interview"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="practice_attempts")
    practice_type = models.CharField(max_length=30, choices=PRACTICE_TYPES)
    score = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)
    feedback = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-submitted_at"]


class InterviewSession(models.Model):
    STATUS = [
        ("active", "Active"),
        ("completed", "Completed"),
    ]

    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="interview_sessions")
    prompt = models.CharField(max_length=500, default="Tell me about a technical project you are proud of.")
    answer = models.TextField(blank=True)
    feedback = models.TextField(blank=True)
    score = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=STATUS, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]


class Bookmark(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bookmarks")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="bookmarks")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["student", "job"],
                name="unique_student_job_bookmark"
            )
        ]
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.student.username} → {self.job}"

class RecruiterInterview(models.Model):
    INTERVIEW_TYPES = [
        ("technical", "Technical Interview"),
        ("hr", "HR Interview"),
        ("behavioral", "Behavioral Interview"),
    ]

    STATUS_CHOICES = [
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ]

    DECISION_CHOICES = [
        ("pending", "Pending"),
        ("next_round", "Move to Next Round"),
        ("selected", "Selected"),
        ("rejected", "Not Selected"),
    ]

    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="interviews",
    )
    recruiter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="recruiter_interviews",
    )
    interview_type = models.CharField(
        max_length=20,
        choices=INTERVIEW_TYPES,
        default="technical",
    )
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=30)
    meeting_link = models.URLField(blank=True)
    question = models.TextField(
        blank=True,
        default="Explain one of your projects and your exact technical contribution.",
    )
    candidate_response = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="scheduled",
    )
    technical_score = models.PositiveIntegerField(default=0)
    communication_score = models.PositiveIntegerField(default=0)
    problem_solving_score = models.PositiveIntegerField(default=0)
    overall_score = models.PositiveIntegerField(default=0)
    recruiter_feedback = models.TextField(blank=True)
    decision = models.CharField(
        max_length=20,
        choices=DECISION_CHOICES,
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["scheduled_at", "-created_at"]

    def __str__(self):
        return f"{self.application.student.username} — {self.application.job.title} — {self.get_interview_type_display()}"


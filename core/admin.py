from django.contrib import admin
from .models import Application, Bookmark, InterviewSession, Job, PracticeAttempt, Profile, RecruiterInterview, Resume


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("full_name", "user", "role", "college", "company_name", "cgpa", "graduation_year")
    search_fields = ("full_name", "user__username", "user__email", "college", "company_name")


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ("company", "title", "recruiter", "location", "min_cgpa", "match_score", "active", "created_at")
    list_filter = ("active", "company")
    search_fields = ("company", "title", "skills")


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ("job", "student", "status", "applied_at", "updated_at")
    list_filter = ("status",)
    search_fields = ("student__username", "job__title", "job__company")


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ("student", "ats_score", "created_at")
    search_fields = ("student__username",)


@admin.register(PracticeAttempt)
class PracticeAttemptAdmin(admin.ModelAdmin):
    list_display = ("student", "practice_type", "score", "total", "submitted_at")
    list_filter = ("practice_type",)


@admin.register(InterviewSession)
class InterviewSessionAdmin(admin.ModelAdmin):
    list_display = ("student", "status", "score", "created_at", "completed_at")
    list_filter = ("status",)


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ("student", "job", "created_at")
    search_fields = ("student__username", "student__email", "job__title", "job__company")


@admin.register(RecruiterInterview)
class RecruiterInterviewAdmin(admin.ModelAdmin):
    list_display = ("application", "recruiter", "interview_type", "scheduled_at", "status", "decision", "overall_score")
    list_filter = ("interview_type", "status", "decision")
    search_fields = ("application__student__username", "application__student__email", "application__job__title", "application__job__company")

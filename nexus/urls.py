from django.contrib import admin

from django.conf import settings

from django.conf.urls.static import static

from django.urls import path

from core import views





urlpatterns = [



    # =========================================================

    # ADMIN

    # =========================================================



    path("admin/", admin.site.urls),





    # =========================================================

    # AUTHENTICATION

    # =========================================================



    path("", views.home, name="home"),



    path(

        "login/",

        views.login_view,

        name="login"

    ),



    path(

        "login-recruiter/",

        views.recruiter_login_view,

        name="login_recruiter"

    ),



    path(

        "register/",

        views.register_view,

        name="register"

    ),



    path(

        "register-recruiter/",

        views.recruiter_register_view,

        name="register_recruiter"

    ),



    path(

        "logout/",

        views.logout_view,

        name="logout"

    ),



    path(

        "forgot-password/",

        views.forgot_password,

        name="forgot_password"

    ),





    # =========================================================

    # STUDENT

    # =========================================================



    path(

        "student-dashboard/",

        views.student_dashboard,

        name="student_dashboard"

    ),





    # =========================================================

    # JOBS

    # =========================================================



    path(

        "jobs/",

        views.jobs,

        name="jobs"

    ),



    path(

        "jobs/<int:job_id>/",

        views.job_detail,

        name="job_detail"

    ),



    path(

        "jobs/<int:job_id>/apply/",

        views.apply_job,

        name="apply_job"

    ),



    # IMPORTANT:

    # AI-powered resume vs job-description matching

    path(

        "jobs/<int:job_id>/ai-match/",

        views.ai_resume_match,

        name="ai_resume_match"

    ),



    path(

        "jobs/<int:job_id>/bookmark/",

        views.bookmark_job,

        name="bookmark_job"

    ),





    # =========================================================

    # APPLICATIONS

    # =========================================================



    path(

        "applications/",

        views.applications,

        name="applications"

    ),



    path(

        "applications/<int:application_id>/withdraw/",

        views.withdraw_application,

        name="withdraw_application"

    ),





    # =========================================================

    # RESUME / AI

    # =========================================================



    path(

        "resume-intelligence/",

        views.resume_intelligence,

        name="resume_intelligence"

    ),

    path(
        "resume-improve/",
        views.resume_improve,
        name="resume_improve"
    ),



    path(

        "profile/",

        views.profile,

        name="profile"

    ),



    path(

        "role-match/",

        views.role_match,

        name="role_match"

    ),





    # =========================================================

    # PREPARATION & TESTS

    # =========================================================



    path(

        "prep-and-tests/",

        lambda request: views.render_exact(

            request,

            "prep-and-tests.html"

        ),

        name="prep_and_tests"

    ),



    path(

        "aptitude-practice/",

        lambda request: views.render_exact(

            request,

            "aptitude-practice.html"

        ),

        name="aptitude_practice"

    ),



    path(

        "coding-practice/",

        lambda request: views.render_exact(

            request,

            "coding-practice.html"

        ),

        name="coding_practice"

    ),



    path(

        "test-assessment/",

        views.assessment_page,

        name="test_assessment"

    ),



    path(

        "mock-interview/",

        views.mock_interview,

        name="mock_interview"

    ),



    path(

        "practice/submit/",

        views.submit_practice,

        name="submit_practice"

    ),



    path(

        "practice/result/<int:attempt_id>/",

        views.practice_result,

        name="practice_result"

    ),



    path(

        "interview/submit/",

        views.submit_interview,

        name="submit_interview"

    ),





    # =========================================================

    # RECRUITER

    # =========================================================



    path(

        "recruiter-dashboard/",

        views.recruiter_dashboard,

        name="recruiter_dashboard"

    ),



    path(

        "recruiter-jobs/",

        views.recruiter_jobs,

        name="recruiter_jobs"

    ),



    path(

        "recruiter-candidates/",

        views.recruiter_candidates,

        name="recruiter_candidates"

    ),



    path(

        "recruiter-candidates/<int:application_id>/status/",

        views.update_application_status,

        name="update_application_status"

    ),



    path(

        "recruiter-candidates/<int:application_id>/review/",

        views.recruiter_candidate_review,

        name="recruiter_candidate_review"

    ),



    path(

        "recruiter-candidates/<int:application_id>/schedule-interview/",

        views.schedule_interview,

        name="schedule_interview"

    ),



    path(

        "recruiter-interviews/<int:interview_id>/",

        views.recruiter_interview_detail,

        name="recruiter_interview_detail"

    ),



    path(

        "my-interviews/",

        views.student_interviews,

        name="student_interviews"

    ),



    path(

        "my-interviews/<int:interview_id>/",

        views.student_interview_detail,

        name="student_interview_detail"

    ),



    path(

        "recruiter-analytics/",

        views.recruiter_analytics,

        name="recruiter_analytics"

    ),



    path(

        "recruiter-sourcing/",

        views.recruiter_sourcing,

        name="recruiter_sourcing"

    ),



    path(

        "recruiter-settings/",

        views.recruiter_settings,

        name="recruiter_settings"

    ),





    # =========================================================

    # CANDIDATE PROFILE

    # =========================================================



    path(

        "candidate-profile/",

        views.candidate_profile,

        name="candidate_profile"

    ),



    path(

        "candidate-profile/<int:user_id>/",

        views.candidate_profile,

        name="candidate_profile_user"

    ),





    # =========================================================

    # API

    # =========================================================



    path(

        "api/jobs/",

        views.jobs_api,

        name="jobs_api"

    ),



    path(

        "api/applications/",

        views.applications_api,

        name="applications_api"

    ),





    # =========================================================

    # ORIGINAL HTML PAGE ALIASES

    # Keeps your existing frontend links working

    # =========================================================



    path(

        "index.html",

        views.home

    ),



    path(

        "login.html",

        views.login_view

    ),



    path(

        "login-recruiter.html",

        views.recruiter_login_view

    ),



    path(

        "register.html",

        views.register_view

    ),



    path(

        "register-recruiter.html",

        views.recruiter_register_view

    ),



    path(

        "logout.html",

        views.logout_view

    ),



    path(

        "forgot-password.html",

        views.forgot_password

    ),



    path(

        "student-dashboard.html",

        views.student_dashboard

    ),



    path(

        "jobs.html",

        views.jobs

    ),



    path(

        "job-details.html",

        views.job_detail

    ),



    path(

        "applications.html",

        views.applications

    ),



    path(

        "resume-intelligence.html",

        views.resume_intelligence

    ),

    path(
        "resume-improve.html",
        views.resume_improve
    ),



    path(

        "profile.html",

        views.profile

    ),



    path(

        "role-match.html",

        views.role_match

    ),



    path(

        "prep-and-tests.html",

        lambda request: views.render_exact(

            request,

            "prep-and-tests.html"

        )

    ),



    path(

        "aptitude-practice.html",

        lambda request: views.render_exact(

            request,

            "aptitude-practice.html"

        )

    ),



    path(

        "coding-practice.html",

        lambda request: views.render_exact(

            request,

            "coding-practice.html"

        )

    ),



    path(

        "test-assessment.html",

        views.assessment_page

    ),



    path(

        "mock-interview.html",

        views.mock_interview

    ),



    path(

        "recruiter-dashboard.html",

        views.recruiter_dashboard

    ),



    path(

        "recruiter-jobs.html",

        views.recruiter_jobs

    ),



    path(

        "recruiter-candidates.html",

        views.recruiter_candidates

    ),



    path(

        "recruiter-analytics.html",

        views.recruiter_analytics

    ),



    path(

        "recruiter-sourcing.html",

        views.recruiter_sourcing

    ),



    path(

        "recruiter-settings.html",

        views.recruiter_settings

    ),



    path(

        "candidate-profile.html",

        views.candidate_profile

    ),

]





# =========================================================

# MEDIA & STATIC FILES

# =========================================================



urlpatterns += static(

    settings.MEDIA_URL,

    document_root=settings.MEDIA_ROOT

)



urlpatterns += static(

    settings.STATIC_URL,

    document_root=settings.STATICFILES_DIRS[0]

)
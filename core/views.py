import re

from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Count, Q, Prefetch
from django.http import JsonResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import (
    Application,
    Bookmark,
    InterviewSession,
    Job,
    PracticeAttempt,
    Profile,
    RecruiterInterview,
    Resume,
    ResumeJobAnalysis,
)


SKILL_LIBRARY = [
    "python",
    "django",
    "javascript",
    "react",
    "sql",
    "mysql",
    "postgresql",
    "java",
    "c++",
    "html",
    "css",
    "node.js",
    "rest api",
    "git",
    "aws",
    "machine learning",
    "typescript",
    "docker",
    "kubernetes",
    "terraform",
    "pytorch",
    "go",
    "graphql",
    "redis",
    "tailwind",
    "system design",
]


def _keyword_tokens(text):
    """Return useful normalized skill/technology phrases found in text."""
    corpus = (text or "").lower()
    aliases = {
        "react.js": "react", "reactjs": "react", "nodejs": "node.js",
        "restful api": "rest api", "restful apis": "rest api",
        "postgres": "postgresql", "k8s": "kubernetes",
        "ml": "machine learning", "js": "javascript", "ts": "typescript",
    }
    found = set()
    for skill in SKILL_LIBRARY:
        if skill in corpus:
            found.add(skill)
    for alias, canonical in aliases.items():
        if alias in corpus:
            found.add(canonical)
    return sorted(found)


def _local_job_resume_analysis(resume_text, job_text, job_skills=""):
    """Safe deterministic fallback used when no AI API key is configured."""
    resume_tokens = set(_keyword_tokens(resume_text))
    job_tokens = set(_keyword_tokens((job_text or "") + " " + (job_skills or "")))
    matched = sorted(resume_tokens & job_tokens)
    missing = sorted(job_tokens - resume_tokens)
    score = round((len(matched) / len(job_tokens)) * 100) if job_tokens else 0
    return {
        "ats_score": max(0, min(100, score)),
        "matched_keywords": matched,
        "missing_keywords": missing,
        "strengths": [f"Resume mentions {x}." for x in matched[:6]],
        "suggestions": [f"Consider adding genuine experience with {x} if you have used it." for x in missing[:6]],
        "ai_powered": False,
        "raw_response": "Local keyword fallback used because OPENAI_API_KEY is not configured.",
    }


def _ai_job_resume_analysis(resume_text, job):
    """Analyze a resume against a job using the free local Sentence Transformer model."""
    from .local_ai import analyze_resume_against_job

    try:
        result = analyze_resume_against_job(
            resume_text=resume_text,
            job_description=job.description,
            job_skills=job.skills,
        )
        return result
    except Exception as exc:
        return {
            "ats_score": 0,
            "matched_keywords": [],
            "missing_keywords": [],
            "strengths": [],
            "suggestions": [
                "The local AI screening model could not complete the analysis.",
                "Please verify that the Sentence Transformer model is installed correctly.",
            ],
            "ai_powered": False,
            "raw_response": f"Local AI screening failed: {type(exc).__name__}: {exc}",
        }


def render_exact(request, name, **ctx):
    return render(request, name, ctx)


def role_required(role):
    def decorator(view_func):

        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):

            profile = getattr(request.user, "profile", None)

            if not profile or profile.role != role:

                if profile and profile.role == "recruiter":
                    return redirect("recruiter_dashboard")

                return redirect("student_dashboard")

            return view_func(request, *args, **kwargs)

        return wrapper

    return decorator


def home(request):
    return render_exact(request, "index.html")


# ============================================================
# LOGIN
# ============================================================

def _login(request, expected_role=None):

    if request.method == "POST":

        login_value = (
            request.POST.get("username")
            or request.POST.get("email")
            or ""
        ).strip()

        password = request.POST.get("password", "")

        user = None

        # ----------------------------------------------------
        # 1. Try normal Django username authentication
        # ----------------------------------------------------

        if login_value:
            user = authenticate(
                request,
                username=login_value,
                password=password,
            )

        # ----------------------------------------------------
        # 2. If username authentication failed, find by email
        # ----------------------------------------------------

        if user is None and login_value:

            account = User.objects.filter(
                email__iexact=login_value
            ).first()

            if account:

                user = authenticate(
                    request,
                    username=account.username,
                    password=password,
                )

        # ----------------------------------------------------
        # 3. Successful authentication
        # ----------------------------------------------------

        if user is not None:

            profile = getattr(user, "profile", None)

            if expected_role:

                if not profile or profile.role != expected_role:

                    messages.error(
                        request,
                        "This account does not belong to the selected workspace."
                    )

                    return render_exact(
                        request,
                        "login-recruiter.html"
                        if expected_role == "recruiter"
                        else "login.html",
                    )

            login(request, user)

            if profile and profile.role == "recruiter":
                return redirect("recruiter_dashboard")

            return redirect("student_dashboard")

        # ----------------------------------------------------
        # Invalid credentials
        # ----------------------------------------------------

        messages.error(
            request,
            "Invalid email or password."
        )

    if expected_role == "recruiter":
        template = "login-recruiter.html"
    else:
        template = "login.html"

    return render_exact(request, template)


def login_view(request):
    return _login(request, "student")


def recruiter_login_view(request):
    return _login(request, "recruiter")


# ============================================================
# STUDENT REGISTRATION
# ============================================================

def register_view(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        phone = request.POST.get("phone", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")

        if not name or not email or not password:

            messages.error(
                request,
                "Name, email and password are required."
            )

        elif len(password) < 6:

            messages.error(
                request,
                "Password must contain at least 6 characters."
            )

        elif password != confirm:

            messages.error(
                request,
                "Passwords do not match."
            )

        elif User.objects.filter(
            username__iexact=email
        ).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

        elif User.objects.filter(
            email__iexact=email
        ).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

        else:

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
            )

            Profile.objects.create(
                user=user,
                role="student",
                full_name=name,
                phone=phone,
            )

            login(request, user)

            return redirect("student_dashboard")

    return render_exact(request, "register.html")


# ============================================================
# RECRUITER REGISTRATION
# ============================================================

def recruiter_register_view(request):

    if request.method == "POST":

        name = request.POST.get("name", "").strip()
        email = request.POST.get("email", "").strip().lower()
        company = request.POST.get("company", "").strip()
        password = request.POST.get("password", "")
        confirm = request.POST.get("confirm", "")

        if not name or not email or not company or not password:

            messages.error(
                request,
                "Name, email, company and password are required."
            )

        elif len(password) < 6:

            messages.error(
                request,
                "Password must contain at least 6 characters."
            )

        elif password != confirm:

            messages.error(
                request,
                "Passwords do not match."
            )

        elif User.objects.filter(
            username__iexact=email
        ).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

        elif User.objects.filter(
            email__iexact=email
        ).exists():

            messages.error(
                request,
                "An account with this email already exists."
            )

        else:

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=name,
            )

            Profile.objects.create(
                user=user,
                role="recruiter",
                full_name=name,
                company_name=company,
            )

            login(request, user)

            return redirect("recruiter_dashboard")

    return render_exact(
        request,
        "register-recruiter.html"
    )


# ============================================================
# LOGOUT
# ============================================================

def logout_view(request):

    logout(request)

    return redirect("home")


# ============================================================
# JOB MATCHING
# ============================================================

def _job_matches(job, profile, resume):

    score = job.match_score

    if profile:

        required = {
            x.strip().lower()
            for x in re.split(r"[,;\n]+", job.skills)
            if x.strip()
        }

        owned = {
            x.strip().lower()
            for x in re.split(r"[,;\n]+", profile.skills)
            if x.strip()
        }

        if resume:

            owned |= {
                x.strip().lower()
                for x in resume.matched_skills.split(",")
                if x.strip()
            }

        if required:

            overlap = len(required & owned)

            score = max(
                score,
                min(
                    99,
                    round(
                        60
                        + 40 * overlap / len(required)
                    )
                )
            )

    return score


# ============================================================
# JOBS
# ============================================================

@role_required("student")
def jobs(request):

    qs = (
        Job.objects
        .filter(active=True)
        .select_related("recruiter")
    )

    query = request.GET.get("q", "").strip()

    if query:

        qs = qs.filter(
            Q(title__icontains=query)
            | Q(company__icontains=query)
            | Q(skills__icontains=query)
            | Q(location__icontains=query)
        )

    profile = getattr(
        request.user,
        "profile",
        None
    )

    resume = (
        Resume.objects
        .filter(student=request.user)
        .first()
    )

    job_rows = []

    applied_ids = set(
        Application.objects
        .filter(student=request.user)
        .values_list("job_id", flat=True)
    )

    bookmarked_ids = set(
        Bookmark.objects
        .filter(student=request.user)
        .values_list("job_id", flat=True)
    )

    for job in qs:

        job.display_match = _job_matches(
            job,
            profile,
            resume
        )

        job_rows.append(job)

    return render_exact(
        request,
        "jobs.html",
        jobs=job_rows,
        applied_ids=applied_ids,
        bookmarked_ids=bookmarked_ids,
        query=query,
    )


# ============================================================
# JOB DETAILS
# ============================================================

@role_required("student")
def job_detail(request, job_id=None):

    if job_id:

        job = get_object_or_404(
            Job,
            id=job_id,
            active=True
        )

    else:

        job_id = request.GET.get("job")

        if job_id:

            job = get_object_or_404(
                Job,
                id=job_id,
                active=True
            )

        else:

            job = Job.objects.filter(
                active=True
            ).first()

    if not job:
        return redirect("jobs")

    application = (
        Application.objects
        .filter(
            job=job,
            student=request.user
        )
        .first()
    )

    return render_exact(
        request,
        "job-details.html",
        job=job,
        application=application,
    )


# ============================================================
# APPLY FOR JOB
# ============================================================

@role_required("student")
@require_http_methods(["GET", "POST"])
def ai_resume_match(request, job_id):
    """
    Analyze the CURRENT saved resume against the selected job.

    Important:
    - Matching is always calculated from the current resume text.
    - Old/stale ResumeJobAnalysis data is refreshed.
    - Missing keywords are never added to the resume.
    - Results change automatically when the resume changes.
    """

    job = get_object_or_404(
        Job,
        id=job_id,
        active=True
    )

    # ------------------------------------------------------------
    # Select resume
    # ------------------------------------------------------------

    resume_id = (
        request.POST.get("resume_id")
        or request.GET.get("resume_id")
        or ""
    ).strip()

    if resume_id:
        resume = (
            Resume.objects
            .filter(
                id=resume_id,
                student=request.user
            )
            .first()
        )
    else:
        resume = (
            Resume.objects
            .filter(student=request.user)
            .order_by("-created_at")
            .first()
        )

    if not resume:
        messages.error(
            request,
            "Please upload or select a resume before running the AI analysis."
        )
        return redirect("resume_intelligence")

    # ------------------------------------------------------------
    # Make sure resume has text
    # ------------------------------------------------------------

    resume_text = (resume.extracted_text or "").strip()

    if not resume_text:
        messages.error(
            request,
            "Analyze your resume first so NexusAI can read its text."
        )
        return redirect("resume_intelligence")

    # ------------------------------------------------------------
    # ALWAYS calculate a fresh analysis.
    #
    # This is the important fix.
    #
    # We do NOT simply read the old ResumeJobAnalysis record.
    # ------------------------------------------------------------

    result = _ai_job_resume_analysis(
        resume_text,
        job
    )

    analysis, _ = (
        ResumeJobAnalysis.objects
        .update_or_create(
            resume=resume,
            job=job,
            defaults={
                "ats_score": result["ats_score"],

                "matched_keywords": ", ".join(
                    result.get("matched_keywords", [])
                ),

                "missing_keywords": ", ".join(
                    result.get("missing_keywords", [])
                ),

                "strengths": "\n".join(
                    result.get("strengths", [])
                ),

                "suggestions": "\n".join(
                    result.get("suggestions", [])
                ),

                "ai_powered": result.get(
                    "ai_powered",
                    False
                ),

                "raw_response": result.get(
                    "raw_response",
                    ""
                ),
            }
        )
    )

    # ------------------------------------------------------------
    # Show message only after POST.
    # GET should simply display the fresh analysis.
    # ------------------------------------------------------------

    if request.method == "POST":

        if analysis.ai_powered:
            messages.success(
                request,
                "NexusAI analyzed your current resume successfully."
            )
        else:
            messages.warning(
                request,
                "NexusAI used the local resume-matching analysis."
            )

    # ------------------------------------------------------------
    # Available resumes
    # ------------------------------------------------------------

    resumes = (
        Resume.objects
        .filter(student=request.user)
        .order_by("-created_at")
    )

    # ------------------------------------------------------------
    # IMPORTANT:
    # 'analysis' now ALWAYS represents the CURRENT resume.
    # ------------------------------------------------------------

    return render_exact(
        request,
        "ai-resume-match.html",
        job=job,
        resume=resume,
        resumes=resumes,
        analysis=analysis,
    )

@role_required("student")
@require_http_methods(["GET", "POST"])
def apply_job(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        active=True
    )

    profile = getattr(request.user, "profile", None)

    if (
        profile
        and profile.cgpa
        and job.min_cgpa
        and profile.cgpa < job.min_cgpa
    ):
        messages.error(
            request,
            f"You do not meet the minimum CGPA requirement of {job.min_cgpa}."
        )
        return redirect("jobs")

    existing_application = Application.objects.filter(
        job=job,
        student=request.user
    ).first()

    if request.method == "GET":
        resumes = Resume.objects.filter(student=request.user).order_by("-created_at")
        return render_exact(
            request,
            "apply-job.html",
            job=job,
            application=existing_application,
            resumes=resumes,
        )

    if existing_application:
        messages.info(request, "You have already applied for this role.")
        return redirect("applications")

    resume = None
    resume_id = request.POST.get("resume_id", "").strip()
    uploaded_file = request.FILES.get("resume_file")

    if resume_id:
        resume = Resume.objects.filter(
            id=resume_id,
            student=request.user
        ).first()
        if not resume:
            messages.error(request, "The selected resume could not be found.")
            return redirect("apply_job", job_id=job.id)

    if uploaded_file:
        resume = Resume.objects.create(
            student=request.user,
            file=uploaded_file,
        )

    if not resume:
        messages.error(
            request,
            "Please select an existing resume or upload a resume before applying."
        )
        return redirect("apply_job", job_id=job.id)

    application = Application.objects.create(
        job=job,
        student=request.user,
        resume=resume,
    )

    messages.success(
        request,
        f"Application submitted for {job.title} at {job.company} with your resume."
    )
    return redirect("applications")


# ============================================================
# BOOKMARK / SAVE JOB
# ============================================================

@role_required("student")
@require_http_methods(["POST"])
def bookmark_job(request, job_id):

    job = get_object_or_404(
        Job,
        id=job_id,
        active=True
    )

    bookmark = Bookmark.objects.filter(
        student=request.user,
        job=job
    ).first()

    if bookmark:

        bookmark.delete()

        messages.success(
            request,
            f"{job.title} removed from saved jobs."
        )

    else:

        Bookmark.objects.create(
            student=request.user,
            job=job
        )

        messages.success(
            request,
            f"{job.title} saved successfully."
        )

    return redirect("jobs")


# ============================================================
# WITHDRAW APPLICATION
# ============================================================

@role_required("student")
@require_http_methods(["POST"])
def withdraw_application(
    request,
    application_id
):

    application = get_object_or_404(
        Application,
        id=application_id,
        student=request.user
    )

    if application.status in {
        "selected",
        "rejected"
    }:

        messages.error(
            request,
            "This application can no longer be withdrawn."
        )

    else:

        application.delete()

        messages.success(
            request,
            "Application withdrawn."
        )

    return redirect("applications")


# ============================================================
# APPLICATIONS
# ============================================================

@role_required("student")
def applications(request):

    application_list = (
        Application.objects
        .filter(student=request.user)
        .select_related(
            "job",
            "job__recruiter"
        )
    )

    counts = {
        "applied": application_list.filter(
            status="applied"
        ).count(),

        "screening": application_list.filter(
            status="screening"
        ).count(),

        "shortlisted": application_list.filter(
            status="shortlisted"
        ).count(),

        "interview": application_list.filter(
            status="interview"
        ).count(),

        "selected": application_list.filter(
            status="selected"
        ).count(),
    }

    interviews = (
        RecruiterInterview.objects
        .filter(application__student=request.user)
        .select_related("application__job", "recruiter")
        .order_by("scheduled_at")
    )

    # Attach the latest interview to each application so the candidate page
    # always reflects the recruiter-side interview workflow.
    latest_interviews = {}
    for interview in interviews.order_by("-scheduled_at"):
        latest_interviews.setdefault(interview.application_id, interview)

    for application in application_list:
        application.latest_interview = latest_interviews.get(application.id)

    return render_exact(
        request,
        "applications.html",
        applications=application_list,
        counts=counts,
        interviews=interviews,
    )


# ============================================================
# RESUME INTELLIGENCE
# ============================================================

@role_required("student")
def resume_intelligence(request):
    """Upload and analyze a student's resume using robust PDF/DOCX extraction."""

    uploaded_file = request.FILES.get("resume")

    if not uploaded_file:
        latest = (
            Resume.objects
            .filter(student=request.user)
            .first()
        )

        return render_exact(
            request,
            "resume-intelligence.html",
            resume=latest,
        )

    if uploaded_file.size > 5 * 1024 * 1024:
        messages.error(request, "Resume must be 5 MB or smaller.")
        return redirect("resume_intelligence")

    filename = uploaded_file.name.lower().strip()

    if not filename.endswith((".pdf", ".docx")):
        messages.error(request, "Please upload a PDF or DOCX resume.")
        return redirect("resume_intelligence")

    # Read the upload once so multiple parsers can safely inspect the same file.
    try:
        uploaded_file.seek(0)
        file_bytes = uploaded_file.read()
    except Exception:
        messages.error(request, "The uploaded resume could not be read. Please try again.")
        return redirect("resume_intelligence")

    text = ""
    parser_errors = []

    if filename.endswith(".pdf"):
        # First try PyMuPDF because it handles many real-world PDFs that are
        # rejected by stricter PDF parsers.
        try:
            import fitz

            pdf = fitz.open(stream=file_bytes, filetype="pdf")
            try:
                text = "\n".join(page.get_text("text") or "" for page in pdf)
            finally:
                pdf.close()
        except Exception as exc:
            parser_errors.append(f"PyMuPDF: {exc}")

        # Fall back to pypdf for PDFs PyMuPDF cannot open.
        if not text.strip():
            try:
                from io import BytesIO
                from pypdf import PdfReader

                reader = PdfReader(BytesIO(file_bytes), strict=False)

                if reader.is_encrypted:
                    try:
                        reader.decrypt("")
                    except Exception:
                        pass

                text = "\n".join(
                    page.extract_text() or ""
                    for page in reader.pages
                )
            except Exception as exc:
                parser_errors.append(f"pypdf: {exc}")

    elif filename.endswith(".docx"):
        try:
            from io import BytesIO
            from docx import Document

            document = Document(BytesIO(file_bytes))
            text_parts = [p.text for p in document.paragraphs if p.text.strip()]

            # Also inspect simple table-based resumes, which are common in
            # professionally formatted DOCX files.
            for table in document.tables:
                for row in table.rows:
                    text_parts.append(" | ".join(cell.text for cell in row.cells))

            text = "\n".join(text_parts)
        except Exception as exc:
            parser_errors.append(f"python-docx: {exc}")

    if not text.strip():
        messages.error(
            request,
            "We could not extract readable text from this resume. "
            "Please upload a text-based PDF or DOCX resume. "
            "If this is a scanned/image-only PDF, export it as a text PDF and try again."
        )
        return redirect("resume_intelligence")

    corpus = text.lower()

    matched = [
        skill
        for skill in SKILL_LIBRARY
        if skill in corpus
    ]

    missing = [
        skill
        for skill in SKILL_LIBRARY
        if skill not in matched
    ]

    score = min(
        100,
        round(
            len(matched)
            / len(SKILL_LIBRARY)
            * 100
        )
    )

    # Save only after the file has been successfully read and parsed. This
    # prevents a failed scan from leaving a broken Resume record behind.
    uploaded_file.seek(0)
    resume = Resume.objects.create(
        student=request.user,
        file=uploaded_file,
        extracted_text=text,
        matched_skills=", ".join(matched),
        missing_skills=", ".join(missing),
        ats_score=score,
    )

    messages.success(
        request,
        f"Resume analyzed successfully. ATS-style score: {score}% "
        f"with {len(matched)} matched skill(s)."
    )

    return redirect("resume_intelligence")


# ============================================================
# RESUME IMPROVEMENT STUDIO
# ============================================================

@role_required("student")
@require_http_methods(["GET", "POST"])
def resume_improve(request):
    """
    Resume Improvement Studio.

    Important rules:
    1. The student controls the resume content.
    2. Missing keywords are NEVER automatically inserted.
    3. Saving the resume triggers a fresh job analysis.
    4. Matched and missing keywords always reflect the current
       saved resume.
    """

    # ============================================================
    # FIND RESUME
    # ============================================================

    resume_id = (
        request.GET.get("resume_id")
        or request.POST.get("resume_id")
    )

    if resume_id:
        resume = (
            Resume.objects
            .filter(
                id=resume_id,
                student=request.user
            )
            .first()
        )
    else:
        resume = (
            Resume.objects
            .filter(student=request.user)
            .order_by("-created_at")
            .first()
        )

    if not resume:
        messages.error(
            request,
            "Please upload a resume before opening Resume Improvement Studio."
        )
        return redirect("resume_intelligence")

    # ============================================================
    # CURRENT RESUME TEXT
    # ============================================================

    current_text = (
        resume.extracted_text or ""
    ).strip()

    if not current_text:
        messages.error(
            request,
            "This resume does not contain extracted text yet. "
            "Please run the resume scan first."
        )
        return redirect("resume_intelligence")

    # ============================================================
    # OPTIONAL JOB CONTEXT
    # ============================================================

    job_id = (
        request.GET.get("job_id")
        or request.POST.get("job_id")
    )

    job = None
    analysis = None

    if job_id:

        job = (
            Job.objects
            .filter(
                id=job_id,
                active=True
            )
            .first()
        )

    # ============================================================
    # SAVE UPDATED RESUME
    # ============================================================

    if request.method == "POST":

        action = (
            request.POST.get(
                "action",
                "save"
            )
            .strip()
            .lower()
        )

        if action == "save":

            updated_text = (
                request.POST.get(
                    "resume_text",
                    ""
                )
                .strip()
            )

            if not updated_text:

                messages.error(
                    request,
                    "Resume content cannot be empty."
                )

                target = (
                    f"/resume-improve/"
                    f"?resume_id={resume.id}"
                )

                if job:
                    target += (
                        f"&job_id={job.id}"
                    )

                return redirect(target)

            # ----------------------------------------------------
            # SAVE EXACTLY WHAT THE STUDENT ENTERED
            #
            # DO NOT ADD MISSING KEYWORDS.
            # DO NOT MODIFY THE RESUME AUTOMATICALLY.
            # ----------------------------------------------------

            resume.extracted_text = updated_text

            resume.save(
                update_fields=[
                    "extracted_text"
                ]
            )

            # ----------------------------------------------------
            # REFRESH ANALYSIS
            # ----------------------------------------------------

            if job:

                try:

                    refreshed = (
                        _ai_job_resume_analysis(
                            resume.extracted_text,
                            job
                        )
                    )

                    ResumeJobAnalysis.objects.update_or_create(
                        resume=resume,
                        job=job,
                        defaults={
                            "ats_score": refreshed.get(
                                "ats_score",
                                0
                            ),

                            "matched_keywords": ", ".join(
                                refreshed.get(
                                    "matched_keywords",
                                    []
                                )
                            ),

                            "missing_keywords": ", ".join(
                                refreshed.get(
                                    "missing_keywords",
                                    []
                                )
                            ),

                            "strengths": "\n".join(
                                refreshed.get(
                                    "strengths",
                                    []
                                )
                            ),

                            "suggestions": "\n".join(
                                refreshed.get(
                                    "suggestions",
                                    []
                                )
                            ),

                            "ai_powered": refreshed.get(
                                "ai_powered",
                                False
                            ),

                            "raw_response": refreshed.get(
                                "raw_response",
                                ""
                            ),
                        }
                    )

                except Exception as exc:

                    messages.warning(
                        request,
                        "Resume saved, but the job analysis "
                        "could not be refreshed."
                    )

            messages.success(
                request,
                "Your resume has been saved and the job match has been refreshed."
            )

            target = (
                f"/resume-improve/"
                f"?resume_id={resume.id}"
            )

            if job:
                target += (
                    f"&job_id={job.id}"
                )

            return redirect(target)

    # ============================================================
    # ALWAYS REFRESH ANALYSIS FOR CURRENT RESUME
    # ============================================================

    if job:

        try:

            refreshed = (
                _ai_job_resume_analysis(
                    current_text,
                    job
                )
            )

            analysis, _ = (
                ResumeJobAnalysis.objects
                .update_or_create(
                    resume=resume,
                    job=job,
                    defaults={
                        "ats_score": refreshed.get(
                            "ats_score",
                            0
                        ),

                        "matched_keywords": ", ".join(
                            refreshed.get(
                                "matched_keywords",
                                []
                            )
                        ),

                        "missing_keywords": ", ".join(
                            refreshed.get(
                                "missing_keywords",
                                []
                            )
                        ),

                        "strengths": "\n".join(
                            refreshed.get(
                                "strengths",
                                []
                            )
                        ),

                        "suggestions": "\n".join(
                            refreshed.get(
                                "suggestions",
                                []
                            )
                        ),

                        "ai_powered": refreshed.get(
                            "ai_powered",
                            False
                        ),

                        "raw_response": refreshed.get(
                            "raw_response",
                            ""
                        ),
                    }
                )
            )

        except Exception:
            analysis = (
                ResumeJobAnalysis.objects
                .filter(
                    resume=resume,
                    job=job
                )
                .first()
            )

    # ============================================================
    # MATCHED / MISSING KEYWORDS
    # ============================================================

    matched_keywords = []
    missing_keywords = []
    suggestions = []

    if analysis:

        matched_keywords = [
            item.strip()
            for item in (
                analysis.matched_keywords or ""
            ).split(",")
            if item.strip()
        ]

        missing_keywords = [
            item.strip()
            for item in (
                analysis.missing_keywords or ""
            ).split(",")
            if item.strip()
        ]

        # --------------------------------------------------------
        # Missing keywords are ONLY suggestions.
        # They are NOT inserted into the resume.
        # --------------------------------------------------------

        for keyword in missing_keywords:

            suggestions.append(
                f"Consider mentioning '{keyword}' "
                f"only if you genuinely have experience with it."
            )

        for suggestion in (
            analysis.suggestions or ""
        ).splitlines():

            suggestion = suggestion.strip()

            if suggestion:
                suggestions.append(
                    suggestion
                )

    # ============================================================
    # GENERAL SUGGESTIONS
    # ============================================================

    suggestions.extend([
        "Keep your professional summary concise and focused on your strongest skills.",
        "Use measurable achievements wherever possible, such as numbers, percentages, or project results.",
        "Mention technologies and skills that you have genuinely used.",
        "Use strong action verbs such as developed, implemented, designed, optimized, analyzed, and deployed.",
        "Keep project descriptions focused on your contribution, technologies used, and result.",
        "Avoid adding skills, certifications, or experience that you do not actually have.",
        "Use clear ATS-friendly section headings such as Summary, Skills, Projects, Education, and Experience.",
        "Keep formatting consistent throughout the resume.",
        "Place the most relevant technical skills and projects where recruiters can find them quickly.",
        "Remove unnecessary repeated information.",
    ])

    # ============================================================
    # REMOVE DUPLICATE SUGGESTIONS
    # ============================================================

    unique_suggestions = []
    seen = set()

    for suggestion in suggestions:

        cleaned = (
            " ".join(
                suggestion.split()
            )
            .strip()
        )

        if (
            cleaned
            and cleaned.lower() not in seen
        ):

            seen.add(
                cleaned.lower()
            )

            unique_suggestions.append(
                cleaned
            )

    # ============================================================
    # RENDER
    # ============================================================

    return render_exact(
        request,
        "resume-improve.html",

        resume=resume,

        job=job,

        analysis=analysis,

        resume_text=current_text,

        matched_keywords=matched_keywords,

        missing_keywords=missing_keywords,

        suggestions=unique_suggestions[:12],

        character_count=len(
            current_text
        ),

        word_count=len(
            current_text.split()
        ),
    )

    # ============================================================
    # DISPLAY MATCHED / MISSING KEYWORDS
    # ============================================================

    matched_keywords = []
    missing_keywords = []
    suggestions = []

    if analysis:

        matched_keywords = [
            item.strip()
            for item in (
                analysis.matched_keywords or ""
            ).split(",")
            if item.strip()
        ]

        missing_keywords = [
            item.strip()
            for item in (
                analysis.missing_keywords or ""
            ).split(",")
            if item.strip()
        ]

        # Missing keywords are suggestions only.
        # They are NOT added to the resume.
        for keyword in missing_keywords[:10]:

            suggestions.append(
                f"Consider mentioning '{keyword}' only if "
                f"you genuinely have experience with it."
            )

        for suggestion in (
            analysis.suggestions or ""
        ).splitlines():

            suggestion = suggestion.strip()

            if suggestion:
                suggestions.append(
                    suggestion
                )

    # ============================================================
    # GENERAL RESUME SUGGESTIONS
    # ============================================================

    suggestions.extend([
        "Keep your professional summary concise and focused on your strongest skills.",

        "Use measurable achievements wherever possible, "
        "such as numbers, percentages, or project results.",

        "Mention technologies and skills that you have genuinely used.",

        "Use strong action verbs such as developed, implemented, "
        "designed, optimized, analyzed, and deployed.",

        "Keep project descriptions focused on your contribution, "
        "technologies used, and result.",

        "Avoid adding skills, certifications, or experience "
        "that you do not actually have.",

        "Use clear ATS-friendly section headings such as "
        "Summary, Skills, Projects, Education, and Experience.",

        "Keep formatting consistent throughout the resume.",

        "Place the most relevant technical skills and projects "
        "where recruiters can find them quickly.",

        "Remove unnecessary repeated information.",
    ])

    # ============================================================
    # REMOVE DUPLICATE SUGGESTIONS
    # ============================================================

    unique_suggestions = []
    seen = set()

    for suggestion in suggestions:

        cleaned = " ".join(
            suggestion.split()
        ).strip()

        if (
            cleaned
            and cleaned.lower() not in seen
        ):

            seen.add(
                cleaned.lower()
            )

            unique_suggestions.append(
                cleaned
            )

    # ============================================================
    # RENDER RESUME IMPROVEMENT STUDIO
    # ============================================================

    return render_exact(
        request,
        "resume-improve.html",

        resume=resume,

        job=job,

        analysis=analysis,

        resume_text=current_text,

        matched_keywords=matched_keywords,

        missing_keywords=missing_keywords,

        suggestions=unique_suggestions[:12],

        character_count=len(
            current_text
        ),

        word_count=len(
            current_text.split()
        ),
    )

# ============================================================
# STUDENT PROFILE
# ============================================================

@role_required("student")
def profile(request):

    profile_obj, _ = Profile.objects.get_or_create(
        user=request.user,
        defaults={"role": "student"}
    )

    if request.method == "POST":

        profile_obj.full_name = (
            request.POST.get(
                "full_name",
                ""
            ).strip()
        )

        profile_obj.phone = (
            request.POST.get(
                "phone",
                ""
            ).strip()
        )

        profile_obj.college = (
            request.POST.get(
                "college",
                ""
            ).strip()
        )

        profile_obj.branch = (
            request.POST.get(
                "branch",
                ""
            ).strip()
        )

        profile_obj.graduation_year = int(
            request.POST.get(
                "graduation_year"
            ) or 2027
        )

        profile_obj.cgpa = (
            request.POST.get(
                "cgpa"
            ) or 0
        )

        profile_obj.backlogs = int(
            request.POST.get(
                "backlogs"
            ) or 0
        )

        profile_obj.skills = (
            request.POST.get(
                "skills",
                ""
            ).strip()
        )

        profile_obj.bio = (
            request.POST.get(
                "bio",
                ""
            ).strip()
        )

        profile_obj.save()

        request.user.first_name = (
            profile_obj.full_name
        )

        request.user.save(
            update_fields=["first_name"]
        )

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("profile")

    return render_exact(
        request,
        "profile.html",
        profile=profile_obj
    )


# ============================================================
# ROLE MATCH
# ============================================================

@role_required("student")
def role_match(request):

    job = None

    job_id = request.GET.get("job")

    if job_id:

        job = get_object_or_404(
            Job,
            id=job_id,
            active=True
        )

    else:

        job = Job.objects.filter(
            active=True
        ).first()

    profile = getattr(
        request.user,
        "profile",
        None
    )

    resume = (
        Resume.objects
        .filter(student=request.user)
        .first()
    )

    match = (
        _job_matches(
            job,
            profile,
            resume
        )
        if job
        else 0
    )

    return render_exact(
        request,
        "role-match.html",
        job=job,
        match=match
    )


# ============================================================
# RECRUITER DASHBOARD
# ============================================================

@role_required("recruiter")
def recruiter_dashboard(request):

    jobs_qs = Job.objects.filter(recruiter=request.user)
    apps = Application.objects.filter(job__recruiter=request.user)
    interviews = (
        RecruiterInterview.objects
        .filter(recruiter=request.user)
        .select_related("application__student", "application__job")
        .order_by("scheduled_at")
    )

    stats = {
        "active_drives": jobs_qs.filter(active=True).count(),
        "candidates": apps.values("student").distinct().count(),
        "shortlisted": apps.filter(status="shortlisted").count(),
        "interviews": apps.filter(status="interview").count(),
        "selected": apps.filter(status="selected").count(),
    }

    return render_exact(
        request,
        "recruiter-dashboard.html",
        jobs=jobs_qs,
        stats=stats,
        upcoming_interviews=interviews.filter(status__in=["scheduled", "in_progress"])[:5],
    )


# ============================================================
# RECRUITER JOBS
# ============================================================

@role_required("recruiter")
def recruiter_jobs(request):

    if request.method == "POST":

        title = request.POST.get(
            "job_title",
            ""
        ).strip()

        company = request.POST.get(
            "company",
            ""
        ).strip()

        salary = request.POST.get(
            "ctc",
            ""
        ).strip()

        skills = request.POST.get(
            "skills",
            ""
        ).strip()

        description = request.POST.get("description", "").strip()

        min_cgpa = (
            request.POST.get("cgpa")
            or 0
        )

        if not title or not company or not skills or not description:

            messages.error(
                request,
                "Job title, company and skills are required."
            )

        else:

            Job.objects.create(
                recruiter=request.user,
                title=title,
                company=company,
                location=request.POST.get(
                    "location",
                    "Campus / Hybrid"
                ),
                salary=salary,
                skills=skills,
                min_cgpa=min_cgpa,
                batch=request.POST.get(
                    "batch",
                    "2027"
                ),
                eligibility=(
                    f"Minimum CGPA {min_cgpa}; "
                    f"0 active backlogs; "
                    f"required skills: {skills}"
                ),
                description=description,
                match_score=85,
            )

            messages.success(
                request,
                "Drive published successfully and is now visible to students."
            )

            return redirect(
                "recruiter_jobs"
            )

    jobs_qs = (
        Job.objects
        .filter(recruiter=request.user)
        .prefetch_related("applications")
    )

    jobs_list = list(jobs_qs)
    for job in jobs_list:
        job.applied_count = job.applications.count()
        job.shortlisted_count = job.applications.filter(status="shortlisted").count()
        job.interview_count = job.applications.filter(status="interview").count()
        job.selected_count = job.applications.filter(status="selected").count()

    return render_exact(
        request,
        "recruiter-jobs.html",
        jobs=jobs_list
    )


# ============================================================
# UPDATE APPLICATION STATUS
# ============================================================

@role_required("recruiter")
@require_http_methods(["POST"])
def update_application_status(request, application_id):

    with transaction.atomic():
        application = get_object_or_404(
            Application.objects.select_for_update(),
            id=application_id,
            job__recruiter=request.user,
        )

        new_status = request.POST.get("status")
        valid = dict(Application.STATUS)
        if new_status not in valid:
            return HttpResponseBadRequest("Invalid status.")

        latest_interview = application.interviews.order_by("-scheduled_at", "-created_at").first()
        active_interview = application.interviews.filter(status__in=["scheduled", "in_progress"]).first()

        if application.status in {"selected", "rejected"} and new_status != application.status:
            messages.error(request, "This application is already finalized and cannot be moved backward.")
            return redirect("recruiter_candidate_review", application_id=application.id)

        if new_status == "interview":
            if active_interview:
                messages.info(request, "An interview is already active for this candidate. Open the interview instead.")
            elif latest_interview and latest_interview.status == "completed" and latest_interview.decision == "next_round":
                messages.info(request, "The previous interview approved the next round. Use Schedule Next Round to create it.")
            else:
                messages.info(request, "Use Schedule Interview after shortlisting the candidate. Interview status is updated automatically.")
            return redirect("recruiter_candidate_review", application_id=application.id)

        if new_status == "selected":
            if not (latest_interview and latest_interview.status == "completed" and latest_interview.decision == "selected"):
                messages.error(request, "A candidate can be marked Selected only after a finalized interview evaluation with the Selected decision.")
                return redirect("recruiter_candidate_review", application_id=application.id)

        if new_status == "shortlisted":
            if active_interview or (latest_interview and latest_interview.status == "completed"):
                messages.error(request, "This candidate is already in the interview workflow. Use the interview controls instead of moving them back to Shortlisted.")
                return redirect("recruiter_candidate_review", application_id=application.id)

        if new_status == "screening" and (active_interview or latest_interview):
            messages.error(request, "This candidate already has an interview record. The interview workflow controls the current stage.")
            return redirect("recruiter_candidate_review", application_id=application.id)

        if new_status == "rejected" and active_interview:
            application.interviews.filter(status__in=["scheduled", "in_progress"]).update(status="cancelled")

        application.status = new_status
        application.notes = request.POST.get("notes", application.notes)
        application.save(update_fields=["status", "notes", "updated_at"])

    messages.success(request, f"Application status updated to {valid[new_status]}.")
    return redirect("recruiter_candidate_review", application_id=application.id)


# ============================================================
# RECRUITER CANDIDATES
# ============================================================

@role_required("recruiter")
def recruiter_candidates(request):

    apps = (
        Application.objects
        .filter(job__recruiter=request.user)
        .select_related("student", "student__profile", "job")
        .prefetch_related("student__resumes", "interviews")
        .order_by("-applied_at")
    )

    for application in apps:
        candidate_profile = getattr(application.student, "profile", None)
        candidate_resume = application.resume or application.student.resumes.first()
        application.display_match = _job_matches(
            application.job,
            candidate_profile,
            candidate_resume,
        )
        application.latest_interview = application.interviews.order_by("-scheduled_at", "-created_at").first()
        application.active_interview = application.interviews.filter(status__in=["scheduled", "in_progress"]).first()
        application.can_schedule_next_round = bool(
            application.latest_interview
            and application.latest_interview.status == "completed"
            and application.latest_interview.decision == "next_round"
        )

    interview_qs = RecruiterInterview.objects.filter(
        recruiter=request.user
    )

    stats = {
        "total": apps.count(),
        "screening": apps.filter(status="screening").count(),
        "shortlisted": apps.filter(status="shortlisted").count(),
        "interviews": apps.filter(status="interview").count(),
        "selected": apps.filter(status="selected").count(),
    }

    return render_exact(
        request,
        "recruiter-candidates.html",
        applications=apps,
        stats=stats,
        upcoming_interviews=interview_qs.filter(status__in=["scheduled", "in_progress"]).order_by("scheduled_at")[:6],
    )


# ============================================================
# RECRUITER CANDIDATE REVIEW
# ============================================================

@role_required("recruiter")
def recruiter_candidate_review(request, application_id):

    application = get_object_or_404(
        Application.objects.select_related(
            "student",
            "student__profile",
            "job",
        ).prefetch_related("student__resumes", "interviews"),
        id=application_id,
        job__recruiter=request.user,
    )

    profile = getattr(application.student, "profile", None)
    # Always review the exact resume submitted with this application.
    # Fall back to the latest resume only for legacy applications created before
    # application-specific resume attachment was introduced.
    resume = application.resume or application.student.resumes.first()
    match = _job_matches(application.job, profile, resume)
    attempts = PracticeAttempt.objects.filter(
        student=application.student
    ).order_by("-submitted_at")[:8]
    interviews = application.interviews.order_by("-scheduled_at", "-created_at")
    latest_interview = interviews.first()
    active_interview = interviews.filter(status__in=["scheduled", "in_progress"]).first()
    can_schedule_next_round = bool(
        latest_interview
        and latest_interview.status == "completed"
        and latest_interview.decision == "next_round"
    )

    return render_exact(
        request,
        "recruiter-candidate-review.html",
        application=application,
        candidate=application.student,
        profile=profile,
        resume=resume,
        match=match,
        attempts=attempts,
        interviews=interviews,
        latest_interview=latest_interview,
        active_interview=active_interview,
        can_schedule_next_round=can_schedule_next_round,
    )


# ============================================================
# SCHEDULE RECRUITER INTERVIEW
# ============================================================

@role_required("recruiter")
def schedule_interview(request, application_id):

    if request.method == "POST":
        with transaction.atomic():
            application = get_object_or_404(
                Application.objects.select_for_update().select_related("student", "job"),
                id=application_id,
                job__recruiter=request.user,
            )

            if application.status in {"selected", "rejected"}:
                messages.info(request, "This application is already finalized. A new interview cannot be scheduled.")
                return redirect("recruiter_candidate_review", application_id=application.id)

            latest_interview = application.interviews.select_for_update().order_by("-scheduled_at", "-created_at").first()

            if latest_interview and latest_interview.status in {"scheduled", "in_progress"}:
                messages.info(
                    request,
                    "An interview has already been sent to this candidate. They are currently waiting to respond."
                    if not latest_interview.candidate_response.strip()
                    else "The candidate has already responded. Please evaluate the current interview before scheduling another round.",
                )
                return redirect("recruiter_interview_detail", interview_id=latest_interview.id)

            if latest_interview and not (latest_interview.status == "completed" and latest_interview.decision == "next_round"):
                messages.info(request, "This interview is finalized. A new round can only be scheduled after choosing Move to Next Round.")
                return redirect("recruiter_interview_detail", interview_id=latest_interview.id)

            if application.status not in {"shortlisted", "interview"}:
                messages.error(request, "Shortlist the candidate before scheduling an interview.")
                return redirect("recruiter_candidate_review", application_id=application.id)

            raw_datetime = request.POST.get("scheduled_at", "").strip()
            try:
                scheduled_at = timezone.datetime.fromisoformat(raw_datetime)
                if timezone.is_naive(scheduled_at):
                    scheduled_at = timezone.make_aware(scheduled_at, timezone.get_current_timezone())
            except (TypeError, ValueError):
                messages.error(request, "Please choose a valid interview date and time.")
                return redirect("schedule_interview", application_id=application.id)

            if scheduled_at <= timezone.now():
                messages.error(request, "Interview date and time must be in the future.")
                return redirect("schedule_interview", application_id=application.id)

            try:
                duration = max(15, int(request.POST.get("duration_minutes") or 30))
            except (TypeError, ValueError):
                duration = 30

            interview = RecruiterInterview.objects.create(
                application=application,
                recruiter=request.user,
                interview_type=request.POST.get("interview_type", "technical"),
                scheduled_at=scheduled_at,
                duration_minutes=duration,
                meeting_link=request.POST.get("meeting_link", "").strip(),
                question=request.POST.get(
                    "question",
                    "Explain one of your projects and your exact technical contribution.",
                ).strip(),
            )

            application.status = "interview"
            application.save(update_fields=["status", "updated_at"])

        messages.success(request, f"Interview scheduled for {application.student.get_full_name() or application.student.username}.")
        return redirect("recruiter_interview_detail", interview_id=interview.id)

    application = get_object_or_404(
        Application.objects.select_related("student", "job"),
        id=application_id,
        job__recruiter=request.user,
    )

    if application.status in {"selected", "rejected"}:
        messages.info(request, "This application is already finalized. A new interview cannot be scheduled.")
        return redirect("recruiter_candidate_review", application_id=application.id)

    latest_interview = application.interviews.order_by("-scheduled_at", "-created_at").first()
    if latest_interview and latest_interview.status in {"scheduled", "in_progress"}:
        return redirect("recruiter_interview_detail", interview_id=latest_interview.id)
    if latest_interview and not (latest_interview.status == "completed" and latest_interview.decision == "next_round"):
        return redirect("recruiter_interview_detail", interview_id=latest_interview.id)
    if application.status not in {"shortlisted", "interview"}:
        messages.error(request, "Shortlist the candidate before scheduling an interview.")
        return redirect("recruiter_candidate_review", application_id=application.id)

    return render_exact(request, "schedule-interview.html", application=application)


# ============================================================
# RECRUITER INTERVIEW ROOM / EVALUATION
# ============================================================

@role_required("recruiter")
def recruiter_interview_detail(request, interview_id):

    if request.method == "POST":
        with transaction.atomic():
            interview = get_object_or_404(
                RecruiterInterview.objects.select_for_update().select_related(
                    "application__student",
                    "application__student__profile",
                    "application__job",
                ),
                id=interview_id,
                recruiter=request.user,
            )

            if interview.status == "completed":
                messages.info(request, "This interview has already been finalized.")
                return redirect("recruiter_interview_detail", interview_id=interview.id)

            if not interview.candidate_response.strip():
                messages.error(request, "The candidate has not submitted a response yet. Evaluation is locked until the response is received.")
                return redirect("recruiter_interview_detail", interview_id=interview.id)

            try:
                technical = int(request.POST.get("technical_score") or 0)
                communication = int(request.POST.get("communication_score") or 0)
                problem_solving = int(request.POST.get("problem_solving_score") or 0)
            except (TypeError, ValueError):
                messages.error(request, "Scores must be whole numbers from 0 to 10.")
                return redirect("recruiter_interview_detail", interview_id=interview.id)

            if not all(0 <= score <= 10 for score in (technical, communication, problem_solving)):
                messages.error(request, "Each score must be between 0 and 10.")
                return redirect("recruiter_interview_detail", interview_id=interview.id)

            decision = request.POST.get("decision", "pending")
            valid_decisions = dict(RecruiterInterview.DECISION_CHOICES)
            if decision not in valid_decisions:
                return HttpResponseBadRequest("Invalid interview decision.")

            interview.technical_score = technical
            interview.communication_score = communication
            interview.problem_solving_score = problem_solving
            interview.overall_score = round(((technical + communication + problem_solving) / 30) * 100)
            interview.recruiter_feedback = request.POST.get("recruiter_feedback", "").strip()
            interview.decision = decision

            application = interview.application
            if decision == "pending":
                interview.status = "in_progress"
                interview.completed_at = None
                application.status = "interview"
            else:
                interview.status = "completed"
                interview.completed_at = timezone.now()
                if decision == "selected":
                    application.status = "selected"
                elif decision == "rejected":
                    application.status = "rejected"
                else:
                    application.status = "interview"

            interview.save()
            application.notes = interview.recruiter_feedback or application.notes
            application.save(update_fields=["status", "notes", "updated_at"])

        if decision == "pending":
            messages.success(request, "Interview scores saved. Final decision is still pending.")
        else:
            messages.success(request, f"Interview evaluation finalized. Decision: {valid_decisions[decision]}.")
        return redirect("recruiter_candidate_review", application_id=application.id)

    interview = get_object_or_404(
        RecruiterInterview.objects.select_related(
            "application__student",
            "application__student__profile",
            "application__job",
        ),
        id=interview_id,
        recruiter=request.user,
    )

    return render_exact(request, "recruiter-interview.html", interview=interview, application=interview.application)


# ============================================================
# STUDENT INTERVIEWS
# ============================================================

@role_required("student")
def student_interviews(request):

    interviews = (
        RecruiterInterview.objects
        .filter(application__student=request.user)
        .select_related("application__job", "application__job__recruiter", "recruiter")
        .order_by("-scheduled_at", "-created_at")
    )

    return render_exact(
        request,
        "student-interviews.html",
        interviews=interviews,
        upcoming=interviews.filter(status__in=["scheduled", "in_progress"]),
        completed=interviews.filter(status="completed"),
        cancelled=interviews.filter(status="cancelled"),
    )


@role_required("student")
def student_interview_detail(request, interview_id):

    if request.method == "POST":
        with transaction.atomic():
            interview = get_object_or_404(
                RecruiterInterview.objects.select_for_update().select_related("application__job", "application__job__recruiter"),
                id=interview_id,
                application__student=request.user,
            )

            if interview.status == "completed":
                messages.info(request, "This interview has already been finalized by the recruiter.")
                return redirect("student_interview_detail", interview_id=interview.id)

            if interview.status == "cancelled":
                messages.info(request, "This interview is no longer active because the recruiter cancelled it.")
                return redirect("student_interviews")

            if interview.candidate_response.strip():
                messages.info(request, "Your response has already been submitted for this interview.")
                return redirect("student_interview_detail", interview_id=interview.id)

            response = request.POST.get("candidate_response", "").strip()
            if not response:
                messages.error(request, "Please enter your interview response before submitting.")
            else:
                interview.candidate_response = response
                interview.status = "in_progress"
                interview.save(update_fields=["candidate_response", "status"])
                messages.success(request, "Your interview response has been submitted to the recruiter.")

        return redirect("student_interview_detail", interview_id=interview.id)

    interview = get_object_or_404(
        RecruiterInterview.objects.select_related("application__job", "application__job__recruiter"),
        id=interview_id,
        application__student=request.user,
    )

    return render_exact(request, "student-interview.html", interview=interview)


# ============================================================
# RECRUITER ANALYTICS
# ============================================================

@role_required("recruiter")
def recruiter_analytics(request):

    apps = Application.objects.filter(
        job__recruiter=request.user
    )

    stats = list(
        apps.values("status")
        .annotate(total=Count("id"))
    )

    total = apps.count()

    shortlisted = apps.filter(
        status="shortlisted"
    ).count()

    selected = apps.filter(
        status="selected"
    ).count()

    interviews = apps.filter(
        status="interview"
    ).count()

    return render_exact(
        request,
        "recruiter-analytics.html",
        stats=stats,
        total=total,
        shortlisted=shortlisted,
        selected=selected,
        interviews=interviews
    )


# ============================================================
# RECRUITER SOURCING
# ============================================================

@role_required("recruiter")
def recruiter_sourcing(request):

    query = request.GET.get(
        "q",
        ""
    ).strip()

    profiles = (
        Profile.objects
        .filter(role="student")
        .select_related("user")
    )

    if query:

        profiles = profiles.filter(
            Q(full_name__icontains=query)
            | Q(skills__icontains=query)
            | Q(college__icontains=query)
        )

    return render_exact(
        request,
        "recruiter-sourcing.html",
        profiles=profiles
    )


# ============================================================
# RECRUITER SETTINGS
# ============================================================

@role_required("recruiter")
def recruiter_settings(request):

    profile = getattr(
        request.user,
        "profile",
        None
    )

    if request.method == "POST" and profile:

        profile.full_name = request.POST.get(
            "full_name",
            profile.full_name
        )

        profile.company_name = request.POST.get(
            "company_name",
            profile.company_name
        )

        profile.phone = request.POST.get(
            "phone",
            profile.phone
        )

        profile.save()

        messages.success(
            request,
            "Recruiter settings updated."
        )

        return redirect(
            "recruiter_settings"
        )

    return render_exact(
        request,
        "recruiter-settings.html",
        profile=profile
    )


# ============================================================
# CANDIDATE PROFILE
# ============================================================

@login_required
def candidate_profile(
    request,
    user_id=None
):

    if user_id:

        profile_obj = getattr(
            request.user,
            "profile",
            None
        )

        if (
            not profile_obj
            or profile_obj.role != "recruiter"
        ):
            return redirect("profile")

        candidate = get_object_or_404(
            User,
            id=user_id
        )

    else:

        candidate = request.user

    profile_obj = getattr(
        candidate,
        "profile",
        None
    )

    resume = (
        Resume.objects
        .filter(student=candidate)
        .first()
    )

    apps = (
        Application.objects
        .filter(student=candidate)
        .select_related("job")
    )

    return render_exact(
        request,
        "candidate-profile.html",
        candidate=candidate,
        profile=profile_obj,
        resume=resume,
        applications=apps
    )


# ============================================================
# ASSESSMENT
# ============================================================

@role_required("student")
def assessment_page(request):

    return render_exact(
        request,
        "test-assessment.html"
    )


@role_required("student")
@require_http_methods(["POST"])
def submit_practice(request):

    practice_type = request.POST.get("practice_type", "assessment")

    try:
        score = max(0, int(request.POST.get("score") or 0))
        total = max(0, int(request.POST.get("total") or 0))
    except (TypeError, ValueError):
        messages.error(request, "Invalid test result.")
        return redirect("prep_and_tests")

    if total <= 0:
        messages.error(request, "The test could not be submitted because it has no questions.")
        return redirect("prep_and_tests")

    score = min(score, total)

    feedback = request.POST.get("feedback", "").strip()
    percentage = round((score / total) * 100)

    if percentage >= 80:
        feedback = feedback or "Excellent performance. You are showing strong placement readiness."
    elif percentage >= 60:
        feedback = feedback or "Good attempt. Review the questions you missed and practice the weaker areas."
    else:
        feedback = feedback or "Keep practicing. Focus on fundamentals and review the explanations before retaking the test."

    attempt = PracticeAttempt.objects.create(
        student=request.user,
        practice_type=practice_type,
        score=score,
        total=total,
        feedback=feedback
    )

    return redirect("practice_result", attempt_id=attempt.id)


@role_required("student")
def practice_result(request, attempt_id):

    attempt = get_object_or_404(
        PracticeAttempt,
        id=attempt_id,
        student=request.user
    )

    percentage = round((attempt.score / attempt.total) * 100) if attempt.total else 0

    if percentage >= 80:
        result_label = "Excellent"
        result_class = "excellent"
    elif percentage >= 60:
        result_label = "Good"
        result_class = "good"
    else:
        result_label = "Needs Practice"
        result_class = "needs-practice"

    recent_attempts = (
        PracticeAttempt.objects
        .filter(student=request.user)
        .order_by("-submitted_at")[:8]
    )

    return render_exact(
        request,
        "practice-result.html",
        attempt=attempt,
        percentage=percentage,
        result_label=result_label,
        result_class=result_class,
        recent_attempts=recent_attempts,
    )


# ============================================================
# MOCK INTERVIEW
# ============================================================

@role_required("student")
def mock_interview(request):

    session = (
        InterviewSession.objects
        .filter(student=request.user)
        .order_by("-created_at")
        .first()
    )

    if not session:

        session = InterviewSession.objects.create(
            student=request.user,
            prompt=(
                "Tell me about a technical project you are proud of "
                "and explain your technical contribution."
            )
        )

    return render_exact(
        request,
        "mock-interview.html",
        interview=session
    )


@role_required("student")
@require_http_methods(["POST"])
def submit_interview(request):

    session = get_object_or_404(
        InterviewSession,
        id=request.POST.get("session_id"),
        student=request.user
    )

    answer = request.POST.get(
        "answer",
        ""
    ).strip()

    score = min(
        100,
        max(
            0,
            50 + min(
                50,
                len(answer.split()) // 4
            )
        )
    )

    session.answer = answer

    session.score = score

    session.feedback = (
        "Good structure. Add measurable impact, "
        "your exact technical contribution, and the result."
    )

    session.status = "completed"

    session.completed_at = timezone.now()

    session.save()

    messages.success(
        request,
        f"Mock interview completed with a score of {score}/100."
    )

    return redirect(
        "mock_interview"
    )


# ============================================================
# JOBS API
# ============================================================

@login_required
def jobs_api(request):

    data = list(
        Job.objects
        .filter(active=True)
        .values(
            "id",
            "company",
            "title",
            "location",
            "skills",
            "eligibility",
            "salary",
            "match_score"
        )
    )

    return JsonResponse(
        {
            "jobs": data
        }
    )


# ============================================================
# APPLICATIONS API
# ============================================================

@role_required("student")
def applications_api(request):

    if request.method == "POST":

        job = get_object_or_404(
            Job,
            id=request.POST.get("job_id"),
            active=True
        )

        application, created = (
            Application.objects.get_or_create(
                job=job,
                student=request.user
            )
        )

        return JsonResponse(
            {
                "ok": True,
                "id": application.id,
                "status": application.status,
                "created": created
            }
        )

    data = list(
        Application.objects
        .filter(student=request.user)
        .values(
            "id",
            "job_id",
            "status",
            "applied_at",
            "updated_at"
        )
    )

    return JsonResponse(
        {
            "applications": data
        }
    )


# ============================================================
# FORGOT PASSWORD
# ============================================================

def forgot_password(request):

    if request.method == "POST":

        email = (
            request.POST.get(
                "email",
                ""
            )
            .strip()
            .lower()
        )

        exists = User.objects.filter(
            email__iexact=email
        ).exists()

        if exists:

            messages.success(
                request,
                "Password reset request received. "
                "Configure SMTP in deployment to send the reset email."
            )

        else:

            messages.error(
                request,
                "No account was found for that email."
            )

        return redirect("login")

    return render_exact(
        request,
        "forgot-password.html"
    )
@role_required("student")
def student_dashboard(request):

    # --------------------------------------------------------
    # Student applications
    # --------------------------------------------------------

    interview_prefetch = Prefetch(
        "interviews",
        queryset=(
            RecruiterInterview.objects
            .order_by("-scheduled_at", "-created_at")
        ),
        to_attr="dashboard_interviews",
    )

    applications = (
        Application.objects
        .filter(student=request.user)
        .select_related("job", "job__recruiter")
        .prefetch_related(interview_prefetch)
        .order_by("-applied_at")
    )

    # --------------------------------------------------------
    # Student resume
    # --------------------------------------------------------

    resume = (
        Resume.objects
        .filter(student=request.user)
        .order_by("-created_at")
        .first()
    )

    # --------------------------------------------------------
    # Student profile
    # --------------------------------------------------------

    profile = getattr(
        request.user,
        "profile",
        None
    )

    # --------------------------------------------------------
    # All active jobs posted by recruiters
    # --------------------------------------------------------

    all_jobs = (
        Job.objects
        .filter(active=True)
        .select_related("recruiter")
        .order_by("-created_at")
    )

    # --------------------------------------------------------
    # Jobs already applied for
    # --------------------------------------------------------

    applied_ids = set(
        applications.values_list(
            "job_id",
            flat=True
        )
    )

    # --------------------------------------------------------
    # Prepare jobs for dashboard
    # --------------------------------------------------------

    dashboard_jobs = []

    for job in all_jobs:

        # Calculate matching score
        job.display_match = _job_matches(
            job,
            profile,
            resume
        )

        # Mark whether student already applied
        job.is_applied = job.id in applied_ids

        dashboard_jobs.append(job)

    # --------------------------------------------------------
    # Dashboard statistics
    # --------------------------------------------------------

    stats = {

        "eligible_jobs": len(dashboard_jobs),

        "applications": applications.count(),

        "interviews": applications.filter(
            status="interview"
        ).count(),

        "ats_score": (
            resume.ats_score
            if resume
            else 0
        ),

        "pending_tests": 2,
    }

    # --------------------------------------------------------
    # Test / preparation history
    # --------------------------------------------------------

    recent_attempts = (
        PracticeAttempt.objects
        .filter(student=request.user)
        .order_by("-submitted_at")[:5]
    )

    test_count = PracticeAttempt.objects.filter(student=request.user).count()

    latest_attempt = recent_attempts[0] if recent_attempts else None

    dashboard_interviews = (
        RecruiterInterview.objects
        .filter(application__student=request.user)
        .select_related("application__job", "application__job__recruiter")
        .order_by("-scheduled_at", "-created_at")
    )

    upcoming_interviews = dashboard_interviews.filter(
        status__in=["scheduled", "in_progress"]
    ).order_by("scheduled_at")[:5]

    recent_interviews = dashboard_interviews[:5]

    # --------------------------------------------------------
    # Render dashboard
    # --------------------------------------------------------

    return render_exact(
        request,
        "student-dashboard.html",

        applications=applications,
        stats=stats,
        resume=resume,
        latest_resume=resume,
        jobs=dashboard_jobs,
        applied_ids=applied_ids,

        # Template-friendly dashboard metrics
        active_jobs=len(dashboard_jobs),
        application_count=applications.count(),
        interview_count=applications.filter(status="interview").count(),
        test_count=test_count,
        latest_attempt=latest_attempt,
        recent_attempts=recent_attempts,
        upcoming_interviews=upcoming_interviews,
        recent_interviews=recent_interviews,
    )
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.core.files import File
from pathlib import Path

from core.models import Application, PracticeAttempt, Profile, Job, Resume


class Command(BaseCommand):

    help = (
        "Create or update NexusAI demo recruiter, "
        "student and demo jobs."
    )

    def handle(self, *args, **kwargs):

        # ====================================================
        # DEMO RECRUITER
        # ====================================================

        recruiter_username = "recruiter_demo"
        recruiter_email = "recruiter_demo@nexusai.local"
        recruiter_password = "Recruiter@123"

        recruiter = User.objects.filter(
            username=recruiter_username
        ).first()

        if recruiter is None:

            recruiter = User.objects.create_user(
                username=recruiter_username,
                email=recruiter_email,
                first_name="NexusAI Recruiter",
                password=recruiter_password,
            )

        else:

            recruiter.email = recruiter_email
            recruiter.first_name = "NexusAI Recruiter"

            recruiter.set_password(
                recruiter_password
            )

            recruiter.save()

        Profile.objects.update_or_create(
            user=recruiter,
            defaults={
                "role": "recruiter",
                "full_name": "NexusAI Recruiter",
                "company_name": "NexusAI Demo Hiring",
            },
        )

        # ====================================================
        # DEMO STUDENT
        # ====================================================

        student_username = "student_demo@nexusai.local"
        student_email = "student_demo@nexusai.local"
        student_password = "Student@123"

        student = User.objects.filter(
            username=student_username
        ).first()

        if student is None:

            student = User.objects.create_user(
                username=student_username,
                email=student_email,
                first_name="Demo Student",
                password=student_password,
            )

        else:

            student.email = student_email
            student.first_name = "Demo Student"

            student.set_password(
                student_password
            )

            student.save()

        Profile.objects.update_or_create(
            user=student,
            defaults={
                "role": "student",
                "full_name": "Demo Student",
                "college": "NexusAI Demo College",
                "branch": "Computer Science & Engineering",
                "graduation_year": 2027,
                "cgpa": 8.8,
                "backlogs": 0,
                "skills": (
                    "Python, Django, SQL, MySQL, "
                    "HTML, CSS, JavaScript, React, Git"
                ),
            },
        )

        # ====================================================
        # DEMO JOBS
        # ====================================================

        jobs = [

            (
                "Uber Technologies",
                "Senior Frontend Engineer",
                "BLR / Hybrid",
                "₹28 LPA",
                "React.js, TypeScript, Tailwind CSS, Web Vitals",
                "8.6",
                95,
            ),

            (
                "Snowflake Inc",
                "Cloud Platform Specialist",
                "Hyderabad",
                "₹32 LPA Fixed",
                "AWS Architecture, Docker, Kubernetes, Terraform",
                "8.0",
                89,
            ),

            (
                "OpenAI Partner Lab",
                "AI Research Engineer",
                "100% Remote",
                "₹35 LPA",
                "PyTorch, LLM Fine-Tuning, Vector DBs, Python",
                "8.5",
                92,
            ),

            (
                "Microsoft",
                "Software Engineer - 1",
                "Hyderabad / Bengaluru",
                "₹26 LPA",
                "DSA, React, Python, Cloud",
                "8.0",
                94,
            ),

            (
                "Stripe",
                "Backend Engineering Fellow",
                "Remote First",
                "₹34 LPA",
                "Distributed Systems, Go, SQL, APIs",
                "8.0",
                89,
            ),

            (
                "Google",
                "Software Development Engineer",
                "Bengaluru",
                "₹38 LPA",
                "Java, DSA, Cloud, System Design",
                "8.5",
                96,
            ),

            (
                "Amazon",
                "SDE Graduate",
                "Hyderabad / Bengaluru",
                "₹24 LPA",
                "Java, AWS, DSA, Problem Solving",
                "7.5",
                93,
            ),

            (
                "Atlassian",
                "SDE Graduate Program",
                "Bengaluru / Hybrid",
                "₹30 LPA",
                "React, Java, Distributed Systems, Testing",
                "8.0",
                91,
            ),
        ]

        for (
            company,
            title,
            location,
            salary,
            skills,
            cgpa,
            match,
        ) in jobs:

            Job.objects.update_or_create(

                recruiter=recruiter,

                company=company,

                title=title,

                defaults={

                    "location": location,

                    "salary": salary,

                    "skills": skills,

                    "min_cgpa": cgpa,

                    "batch": "2027",

                    "match_score": match,

                    "eligibility": (
                        f"Minimum CGPA {cgpa}; "
                        "0 active backlogs preferred; "
                        f"required skills: {skills}"
                    ),

                    "description": (
                        f"{title} campus opportunity "
                        f"at {company}."
                    ),

                    "active": True,
                },
            )

        # ====================================================
        # DEMO STUDENT APPLICATION + TEST RESULT
        # ====================================================

        demo_job = Job.objects.filter(recruiter=recruiter).order_by("created_at").first()

        if demo_job is not None:
            demo_resume = Resume.objects.filter(
                student=student,
                file__icontains="demo_student_resume"
            ).first()

            if demo_resume is None:
                resume_path = Path(__file__).resolve().parents[3] / "demo_assets" / "demo_student_resume.pdf"
                if resume_path.exists():
                    with resume_path.open("rb") as resume_file:
                        demo_resume = Resume.objects.create(
                            student=student,
                            file=File(resume_file, name="demo_student_resume.pdf"),
                            ats_score=88,
                            matched_skills="Python, Django, SQL, MySQL, React",
                            missing_skills="System Design",
                            extracted_text="Demo Student resume for NexusAI recruiter demonstration.",
                        )

            application, _ = Application.objects.get_or_create(
                job=demo_job,
                student=student,
                defaults={"status": "applied", "resume": demo_resume},
            )
            if demo_resume and application.resume_id != demo_resume.id:
                application.resume = demo_resume
                application.save(update_fields=["resume", "updated_at"])

        if not PracticeAttempt.objects.filter(student=student).exists():
            PracticeAttempt.objects.create(
                student=student,
                practice_type="aptitude",
                score=8,
                total=10,
                feedback="Good demo performance. Review time-work and reasoning questions before the next round.",
            )

        # ====================================================
        # SUCCESS MESSAGE
        # ====================================================

        self.stdout.write(
            self.style.SUCCESS(
                "\n"
                "========================================\n"
                " NexusAI Demo Data Ready\n"
                "========================================\n"
                "\n"
                "RECRUITER\n"
                f"Username : {recruiter_username}\n"
                f"Email    : {recruiter_email}\n"
                f"Password : {recruiter_password}\n"
                "\n"
                "STUDENT\n"
                f"Username : {student_username}\n"
                f"Email    : {student_email}\n"
                f"Password : {student_password}\n"
                "\n"
                "Jobs loaded: 8\n"
                "========================================\n"
            )
        )
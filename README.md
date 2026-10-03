# NexusAI — Full-Stack V4 — Campus Career Copilot

NexusAI is a full-stack campus placement management and intelligent resume screening platform built around the supplied NexusAI HTML/CSS frontend.

## Stack
- Frontend: HTML5, CSS3, JavaScript-ready Django templates
- Backend: Python + Django
- API: Django JSON endpoints / Django REST Framework dependency
- Database: MySQL
- Resume parsing: PyMuPDF + pypdf fallback + python-docx
- Production static files: WhiteNoise
- Production server: Gunicorn

## Main workflows

### Student
1. Register / login
2. Maintain profile
3. Browse and search campus jobs
4. Review eligibility
5. Apply to jobs
6. Track applications and statuses
7. Upload PDF/DOCX resume
8. Run ATS-style skill analysis
9. Practice aptitude, coding and assessment content
10. Complete an AI mock interview and receive stored feedback

### Recruiter
1. Register / login
2. Manage recruiter profile
3. Publish campus drives
4. See live applicant counts
5. Review candidates
6. Move applications through screening / shortlist / interview / selected / rejected
7. Review candidate dossiers with ATS, job-match and test history
8. Shortlist candidates and move applications through the hiring pipeline
9. Schedule technical, HR or behavioral interviews
10. Provide an optional Google Meet/Zoom link or use the NexusAI interview response room
11. Evaluate technical, communication and problem-solving skills
12. Record feedback and choose next round / selected / not selected
13. Search student profiles and view pipeline analytics

## Local setup

### 1. Create MySQL database

```sql
CREATE DATABASE nexusai CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. Create environment file

Copy `.env.example` to `.env` and fill in the MySQL credentials.

Never commit `.env`.

### 3. Install dependencies

Windows PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 4. Apply migrations

```powershell
python manage.py migrate
```

### 5. Create admin

```powershell
python manage.py createsuperuser
```

### 6. Optional demo data

```powershell
python manage.py seed_demo
```

Demo accounts:
- Student: `student_demo@nexusai.local` / `Student@123`
- Recruiter: `recruiter_demo` / `Recruiter@123`

Change these credentials for any real deployment.

### 7. Run

```powershell
python manage.py runserver
```

Open:

`http://127.0.0.1:8000/`

## Recruiter-to-student interview workflow

1. Recruiter opens **Candidates** and clicks **Review**.
2. Recruiter checks the candidate profile, ATS score, calculated job match and stored test results.
3. Recruiter changes the application to **Shortlisted**.
4. Recruiter clicks **Schedule Interview**, selects technical/HR/behavioral, date/time, duration, optional meeting link and interview prompt.
5. The application automatically moves to **Interview** and the student sees the round under **Applications → Interview Center** and on the dashboard.
6. The student can open the NexusAI interview room, submit a response and optionally open the recruiter meeting link.
7. Recruiter opens the interview record, reviews the response, scores Technical / Communication / Problem Solving from 0–10, writes feedback and chooses **Next Round**, **Selected** or **Not Selected**.
8. NexusAI stores the evaluation and updates the application status.

The interview workflow is an application-management and interview-room feature; it does not claim to provide built-in video conferencing. For a live call, paste a Google Meet, Microsoft Teams or Zoom link into the meeting-link field.


## V4 interview workflow fixes

- Recruiter evaluation is locked until the candidate submits an interview response.
- Zero scores can no longer be mistaken for an unanswered interview.
- Recruiter Candidates shows the latest interview state and whether a response has been received.
- Student Applications shows the latest interview status, response state, score and recruiter decision.
- Existing `RecruiterInterview` migration `0005_recruiter_interview` remains unchanged; no new migration is required for V4.

## Production

Set:
- `DEBUG=False`
- strong `SECRET_KEY`
- production `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- production MySQL credentials

Then:

```bash
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
gunicorn nexus.wsgi:application
```

The project includes `Procfile`, `build.sh`, and `render.yaml` as deployment starting points.

## Important implementation note

The ATS module is a deterministic keyword-based screening engine, not a claim of a connected commercial LLM. It extracts text from PDF/DOCX files, compares detected skills with a maintained skill library, stores the score and matched/missing skills, and uses the stored result for role matching.

Email password-reset delivery requires SMTP credentials. The current recovery workflow validates the account and provides a deployment configuration message rather than pretending an email was sent.

## Security checklist before production

- Set a strong `SECRET_KEY`.
- Keep `.env` outside version control.
- Use HTTPS.
- Configure `CSRF_TRUSTED_ORIGINS`.
- Change demo credentials.
- Configure a production MySQL user with least privilege.
- Review upload limits and storage.
- Configure SMTP if password-reset emails are required.
- Run `python manage.py check --deploy`.

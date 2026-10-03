# NexusAI local setup (Windows)

1. Install Python 3.12.
2. Install and start MySQL.
3. Create the database:

```sql
CREATE DATABASE nexusai_final CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

4. Open `.env` and replace `YOUR_MYSQL_PASSWORD` with your MySQL root password.
5. Open PowerShell in this project folder:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

6. Open http://127.0.0.1:8000/

Demo student:
- Email/username: student_demo@nexusai.local
- Password: Student@123

Demo recruiter:
- Username/email: recruiter_demo
- Password: Recruiter@123

If PowerShell blocks activation, use:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate the environment again.

## Recruiter interview demo flow

After `python manage.py seed_demo`, use the demo accounts to test the complete hiring workflow:

1. Log in as recruiter: `recruiter_demo` / `Recruiter@123`.
2. Open **Candidates**. The seeded demo student has a sample application.
3. Click **Review** to inspect the candidate dossier, ATS score, job match and test history.
4. Change the candidate to **Shortlisted**.
5. Click **Schedule Interview**, choose date/time/type, optionally paste a Google Meet/Teams/Zoom link, and save.
6. Log out and log in as the student: `student_demo@nexusai.local` / `Student@123`.
7. Open **Applications → Interview Center** or the dashboard interview card.
8. Open the scheduled interview, join the external meeting if a link was added, and submit the demo response.
9. Log back in as recruiter and open the interview record.
10. Score Technical, Communication and Problem Solving from 0–10, add feedback, and choose **Move to Next Round**, **Selected**, or **Not Selected**.
11. The application status is updated automatically and the student can see the result.

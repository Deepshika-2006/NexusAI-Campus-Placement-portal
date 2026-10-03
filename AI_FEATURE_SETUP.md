# NexusAI AI Resume Screening

This version adds a real AI-powered, job-specific resume screening workflow while preserving the existing student/recruiter placement workflow.

## What was added

1. Recruiters enter a complete Job Description when publishing a drive.
2. Students can open **AI Resume Match** for a job.
3. NexusAI compares the student's extracted resume text with the recruiter job description.
4. When `OPENAI_API_KEY` is configured, the OpenAI Responses API performs the analysis.
5. The result contains:
   - ATS-style score (0-100)
   - matched keywords
   - missing/weak keywords
   - strengths
   - improvement suggestions
6. Results are stored per resume/job in MySQL in `ResumeJobAnalysis`.
7. If the API key is blank or an API call fails, the application uses a transparent local keyword fallback instead of pretending that AI ran.

## Windows setup

Inside the project virtual environment:

```powershell
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Put your own API key in `.env`:

```env
OPENAI_API_KEY=YOUR_OWN_API_KEY_HERE
OPENAI_MODEL=gpt-5.5
```

The submitted `.env` intentionally has a blank database password and blank API key. Add your own local credentials before running against MySQL.

## Demo workflow

1. Log in as recruiter:
   - Email: `recruiter_demo@nexusai.local`
   - Password: `Recruiter@123`
2. Publish a job and paste a real job description.
3. Log in as student:
   - Email/username: `student_demo@nexusai.local`
   - Password: `Student@123`
4. Open Jobs → select the job → **AI Resume Match**.
5. Upload/analyze a resume in Resume Intelligence if needed.
6. Select the resume and run the AI analysis.
7. Review ATS score, matched keywords, missing keywords and suggestions.
8. Continue to the normal application flow.

## Important

The AI score is an ATS-style compatibility signal, not a hiring decision. The system is instructed not to invent candidate experience and to recommend adding a skill only when the candidate genuinely has it.

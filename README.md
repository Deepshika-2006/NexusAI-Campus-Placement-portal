# NexusAI — Campus Placement Portal

NexusAI is a **full-stack campus placement management and intelligent resume screening system** designed to connect students and recruiters through a single platform.

## 🚀 Features

### Student
- Register and login
- Create and manage profile
- Browse campus job opportunities
- Check job eligibility
- Apply for jobs
- Track application status
- Upload PDF/DOCX resumes
- Resume ATS analysis with matched and missing keywords
- Aptitude and coding practice
- Mock interview and feedback

### Recruiter
- Recruiter registration and login
- Create and manage job drives
- View applicants
- Review candidate profiles and resumes
- ATS-based candidate screening
- Shortlist candidates
- Schedule interviews
- Record interview feedback
- Manage candidate application status

## 🛠️ Technologies

- **Frontend:** HTML5, CSS3, JavaScript
- **Backend:** Python, Django
- **Database:** MySQL
- **Resume Processing:** PyMuPDF, pypdf, python-docx
- **AI/Screening:** Local resume analysis and keyword matching
- **Server:** Gunicorn
- **Deployment:** Render

## 📁 Project Structure

```text
NexusAI/
├── core/
├── nexus/
├── templates/
├── static/
├── manage.py
├── requirements.txt
├── .env.example
├── Procfile
└── README.md
```

## ⚙️ Setup

### 1. Clone the repository

```bash
git clone https://github.com/Deepshika-2006/NexusAI-Campus-Placement-portal.git
cd NexusAI-Campus-Placement-portal
```

### 2. Create virtual environment

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL

Create a MySQL database and configure the credentials in `.env`.

```env
DB_NAME=nexusai_final
DB_USER=root
DB_PASSWORD=
DB_HOST=127.0.0.1
DB_PORT=3306
```

Keep your actual `.env` file private.

### 5. Run migrations

```bash
python manage.py migrate
```

### 6. Start the server

```bash
python manage.py runserver
```

Open:

```text
http://127.0.0.1:8000/
```

## 🔐 Security

- `.env` is excluded from GitHub.
- Never commit API keys or passwords.
- Use a strong Django `SECRET_KEY` for deployment.
- Configure production database credentials securely.

## 🎯 Project Goal

NexusAI aims to simplify campus recruitment by providing students with **job discovery, application tracking, resume screening, preparation, and interview management**, while helping recruiters efficiently manage candidates and placement drives.

## 👩‍💻 Developed By

**Deepshika Garlapati**

GitHub: `https://github.com/Deepshika-2006`

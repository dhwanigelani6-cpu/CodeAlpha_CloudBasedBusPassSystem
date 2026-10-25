# Cloud-Based Bus Pass System

A Flask + SQLite demo application for applying for bus passes online, checking application status, and managing applications through a password-protected admin page.

## Features
- Apply for a daily, weekly, monthly, or student monthly bus pass.
- Demo fares are shown before submission (update them to match official rates).
- A unique reference number is generated for each application.
- Track an application using its reference number.
- Admin can approve or reject applications.
- Responsive HTML/CSS interface.
- Ready for local VS Code use and deployment to a Python web host such as Render.

## Project structure
```text
Cloud_Based_Bus_Pass_System/
├── app.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── .gitignore
├── .env.example
├── README.md
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── apply.html
│   ├── success.html
│   ├── track.html
│   ├── admin_login.html
│   ├── admin.html
│   └── error.html
└── static/
    └── style.css
```

## Run locally in VS Code (Windows)
1. Install Python 3.11 or 3.12 and VS Code.
2. Extract this ZIP and open the `Cloud_Based_Bus_Pass_System` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   ```powershell
   py -m venv .venv
   ```
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
   If PowerShell blocks activation, use Command Prompt terminal and run:
   ```bat
   .venv\Scripts\activate.bat
   ```
6. Install packages:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Set demo admin credentials in the current PowerShell terminal:
   ```powershell
   $env:SECRET_KEY="use-a-long-random-value"
   $env:ADMIN_PASSWORD="BusAdmin-ChangeMe-2026"
   ```
8. Start the website:
   ```powershell
   python app.py
   ```
9. Open `http://127.0.0.1:5000` in your browser.
10. Admin page: `http://127.0.0.1:5000/admin/login`. Use the `ADMIN_PASSWORD` value you set in step 7.

## Deploy to Render
1. Push the complete project to a GitHub repository.
2. In Render, choose **New + → Web Service** and connect that repository.
3. Runtime: Python.
4. Build command: `pip install -r requirements.txt`
5. Start command: `gunicorn app:app`
6. Add environment variables in Render:
   - `SECRET_KEY`: a long random secret value.
   - `ADMIN_PASSWORD`: a strong admin password.
7. Click **Create Web Service** and wait until deployment succeeds.

### Important hosting note
This starter uses SQLite stored in the app's filesystem. On hosting platforms with an ephemeral filesystem, the database may reset after redeploy/restart. For durable production data, connect a managed PostgreSQL database and update the application to use it. Do not use real passenger data for a demo deployment. Use HTTPS and configure strong secrets before public use.

## GitHub commands
Run these from the project folder:
```bash
git init
git add .
git commit -m "Build cloud-based bus pass system"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/Cloud-Based-Bus-Pass-System.git
git push -u origin main
```
Replace the remote URL with your actual GitHub repository URL. If a remote already exists, use `git remote set-url origin YOUR_REPOSITORY_URL`.

## Suggested commit messages
- `Initial commit: add Flask bus pass application`
- `Add bus pass application form and fare plans`
- `Add application status tracking`
- `Add password-protected admin dashboard`
- `Style responsive bus pass website`
- `Add Render deployment instructions`

## Scope
This is an educational internship project, not a real transport authority payment system. Fare plans are illustrative. No online payment is collected.

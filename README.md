# Cloud-Based Bus Pass System

A beginner-friendly CodeAlpha Cloud Computing Task 3 demo built with Python Flask, HTML, CSS, JavaScript, and a database.

## Features
- User registration and login with hashed passwords
- Sample bus routes
- Daily, Monthly, and Student pass application
- Server-side fare selection and unique booking references
- My Passes booking history
- Admin route and booking dashboard (requires an admin account to be provisioned securely)
- Responsive blue-and-white interface
- SQLite for quick local testing; PostgreSQL when `DATABASE_URL` is configured

## Important demo notes
- The displayed routes and fares are sample data, not official transit information.
- Booking confirmation is a demo record, not a government-issued bus pass.
- No online payment gateway is included.
- Public deployment requires secure environment variables, PostgreSQL configuration, and testing.
- The app does not implement autoscaling or load balancing by itself.

## Run locally
1. Install Python 3.10 or newer.
2. Create and activate a virtual environment.
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python app.py`
5. Open `http://127.0.0.1:5000`

SQLite is used automatically when `DATABASE_URL` is not set.

## Deploy on Render
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Set `SECRET_KEY` to a strong random value.
- Set `DATABASE_URL` to your PostgreSQL connection string.
- Never commit credentials or `.env` files.

## Main pages
- `/` Home
- `/register` Register
- `/login` Login
- `/apply` Apply for pass (login required)
- `/my-passes` Booking history (login required)
- `/admin` Admin dashboard (admin role required)

## Database
The application creates its tables automatically on startup. `schema.sql` is also included as a reference PostgreSQL schema.

## License
Educational demonstration project.

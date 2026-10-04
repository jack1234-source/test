# Nova Studio Website

A FastAPI-based website with a portfolio-style landing experience, user authentication, dashboard access, contact submission storage, and an admin panel.

## Features that are working

### Public website pages
- Home/login page at `/`
- Login page at `/login`
- Registration page at `/register`
- About page at `/about`
- Services page at `/services`
- Work/projects page at `/work`
- Contact page at `/contact`

### Authentication and user access
- User registration via `/api/register`
- User login via `/api/login`
- User logout via `/api/logout`
- Session-based authentication using cookies
- Redirects to the dashboard when a valid session is active
- Protected pages for logged-in users only

### Dashboard features
- Authenticated users are redirected to `/dashboard`
- User details are available through `/api/me`
- Logged-in users can view their own submitted contact requests via `/api/my-submissions`

### Contact form system
- Contact form submissions are accepted via `/api/contact`
- The form stores:
  - name
  - email
  - project type
  - message
- The submission is saved in SQLite and linked to the logged-in user when available

### Admin features
- Admin-only access at `/admin`
- Admin users can view all contact submissions at `/api/admin/submissions`
- Admin users can view user records and their submission history at `/api/admin/users`
- A default admin account is created automatically when the database is initialized

### Database and app behavior
- SQLite database is created automatically on startup
- Sessions and users are persisted in the database
- A health check endpoint is available at `/health`

## Default admin account
The app creates a default admin account automatically on first startup:

- Username: `admin`
- Password: `admin123`

## Tech stack
- Python
- FastAPI
- SQLite
- HTML/CSS/JavaScript front-end pages

## Run the application

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the server:
   ```bash
   uvicorn main:app --reload
   ```

3. Open the browser at:
   ```text
   http://localhost:8000
   ```

## Main routes
- `/` - login/home redirect
- `/login` - login page
- `/register` - registration page
- `/dashboard` - user dashboard
- `/admin` - admin dashboard
- `/about` - about page
- `/services` - services page
- `/work` - portfolio/work page
- `/contact` - contact page
- `/health` - health check

## API endpoints
- `POST /api/register`
- `POST /api/login`
- `POST /api/logout`
- `GET /api/me`
- `POST /api/contact`
- `GET /api/my-submissions`
- `GET /api/admin/submissions`
- `GET /api/admin/users`

## Notes
This project is a complete working website with page navigation, registration/login, protected routes, contact form processing, and admin review functionality using SQLite persistence.
